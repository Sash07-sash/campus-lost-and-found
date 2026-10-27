import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Data directory for persistent document storage
DATA_DIR = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent)) / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHAT_LOGS_FILE = DATA_DIR / 'mongo_chat_logs.json'
FEEDBACK_FILE = DATA_DIR / 'mongo_feedback.json'
ITEMS_BACKUP_FILE = DATA_DIR / 'mongo_items.json'
AUTH_LOGS_FILE = DATA_DIR / 'mongo_auth_logs.json'


def _load_json_list(filepath: Path) -> list:
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    return []


def _save_json_list(filepath: Path, data: list):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")


# Initialize embedded fallback client (mongomock)
try:
    import mongomock
    _EMBEDDED_CLIENT = mongomock.MongoClient()
    _EMBEDDED_DB = _EMBEDDED_CLIENT[getattr(settings, 'MONGO_DB_NAME', 'campus_lost_found')]

    # Preload persistent documents into collections
    for log_entry in _load_json_list(CHAT_LOGS_FILE):
        entry_copy = dict(log_entry)
        entry_copy.pop('_id', None)
        _EMBEDDED_DB.chat_logs.insert_one(entry_copy)

    for fb_entry in _load_json_list(FEEDBACK_FILE):
        fb_copy = dict(fb_entry)
        fb_copy.pop('_id', None)
        _EMBEDDED_DB.chat_feedback.insert_one(fb_copy)
except Exception as e:
    logger.warning(f"Failed to initialize mongomock: {e}")
    _EMBEDDED_CLIENT = None
    _EMBEDDED_DB = None


def get_mongo_client(custom_uri: Optional[str] = None):
    """
    Establish a MongoDB client. Supports both local MongoDB (port 27017 on D: drive)
    and MongoDB Atlas cloud clusters (mongodb+srv://...mongodb.net).
    Falls back to embedded mongomock engine if server is unreachable.
    """
    try:
        from pymongo import MongoClient
        mongo_uri = custom_uri or getattr(settings, 'MONGO_URI', os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
        
        # Atlas cloud clusters require longer timeout for DNS SRV lookup & SSL handshake
        is_atlas = '+srv' in mongo_uri or 'mongodb.net' in mongo_uri
        timeout_ms = 6000 if is_atlas else 1200
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command('ping')
        return client
    except Exception as e:
        logger.info(f"External/Atlas MongoDB not reachable: {e}")
        return _EMBEDDED_CLIENT


def get_mongo_db():
    client = get_mongo_client()
    db_name = getattr(settings, 'MONGO_DB_NAME', os.environ.get('MONGO_DB_NAME', 'campus_lost_found'))
    if client is not None:
        return client[db_name]
    return None


def is_live_mongo() -> bool:
    """Check if connected to a live MongoDB instance (Local or Atlas)."""
    try:
        from pymongo import MongoClient
        mongo_uri = getattr(settings, 'MONGO_URI', os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
        is_atlas = '+srv' in mongo_uri or 'mongodb.net' in mongo_uri
        timeout_ms = 6000 if is_atlas else 1200
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command('ping')
        return True
    except Exception:
        return False


def is_atlas_connected() -> bool:
    """Check if currently connected specifically to MongoDB Atlas."""
    mongo_uri = getattr(settings, 'MONGO_URI', os.environ.get('MONGO_URI', ''))
    return is_live_mongo() and ('mongodb.net' in mongo_uri or '+srv' in mongo_uri)


def log_chat_interaction(
    session_id: str,
    user: str,
    user_message: str,
    ai_response: str,
    matched_faq_id: Optional[int] = None,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """Store AI conversation interaction in MongoDB."""
    doc = {
        'session_id': session_id,
        'user': user or 'anonymous_student',
        'user_message': user_message,
        'ai_response': ai_response,
        'matched_faq_id': matched_faq_id,
        'error_code': error_code,
        'timestamp': datetime.utcnow().isoformat(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            result = db.chat_logs.insert_one(dict(doc))
            doc['_id'] = str(result.inserted_id)
            doc['storage'] = 'mongodb_atlas' if is_atlas_connected() else ('mongodb_live' if is_live_mongo() else 'mongodb_embedded')
        except Exception as e:
            logger.error(f"Failed to write chat log to MongoDB: {e}")

    # Synchronize to persistent JSON file for backup durability
    current_logs = _load_json_list(CHAT_LOGS_FILE)
    current_logs.insert(0, doc)
    _save_json_list(CHAT_LOGS_FILE, current_logs[:100])
    return doc


def save_chat_feedback(session_id: str, rating: int, comment: str = '') -> Dict[str, Any]:
    """Store student rating and feedback in MongoDB."""
    doc = {
        'session_id': session_id,
        'rating': int(rating),
        'comment': comment.strip(),
        'timestamp': datetime.utcnow().isoformat(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            result = db.chat_feedback.insert_one(dict(doc))
            doc['_id'] = str(result.inserted_id)
            doc['storage'] = 'mongodb_atlas' if is_atlas_connected() else ('mongodb_live' if is_live_mongo() else 'mongodb_embedded')
        except Exception as e:
            logger.error(f"Failed to write chat feedback to MongoDB: {e}")

    current_fb = _load_json_list(FEEDBACK_FILE)
    current_fb.insert(0, doc)
    _save_json_list(FEEDBACK_FILE, current_fb[:100])
    return doc


def sync_item_to_mongo(item) -> Dict[str, Any]:
    """
    Store or update a reported item in MongoDB collection 'reported_items'.
    Ensures item metadata, descriptions, and photo paths are mirrored in MongoDB.
    """
    doc = {
        'item_id': item.id,
        'title': item.title,
        'description': item.description,
        'category': item.category,
        'category_display': item.get_category_display() if hasattr(item, 'get_category_display') else item.category,
        'report_type': item.report_type,
        'campus_location': item.campus_location,
        'date_lost_or_found': str(item.date_lost_or_found),
        'status': item.status,
        'reported_by': item.created_by.username if item.created_by else 'anonymous',
        'has_image': bool(item.image),
        'image_url': item.image.url if item.image else None,
        'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') and item.created_at else datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            db.reported_items.update_one(
                {'item_id': item.id},
                {'$set': doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error mirroring item {item.id} to MongoDB: {e}")

    # Synchronize to local backup
    items_list = _load_json_list(ITEMS_BACKUP_FILE)
    items_list = [i for i in items_list if i.get('item_id') != item.id]
    items_list.insert(0, doc)
    _save_json_list(ITEMS_BACKUP_FILE, items_list[:100])
    return doc


def get_all_chat_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent chat logs from MongoDB collections."""
    db = get_mongo_db()
    if db is not None:
        try:
            cursor = db.chat_logs.find().sort('timestamp', -1).limit(limit)
            logs = []
            for item in cursor:
                item_copy = dict(item)
                item_copy['_id'] = str(item_copy.get('_id', ''))
                logs.append(item_copy)
            if logs:
                return logs
        except Exception as e:
            logger.error(f"Error fetching chat logs from MongoDB: {e}")

    return _load_json_list(CHAT_LOGS_FILE)[:limit]


def get_all_feedback(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent feedback from MongoDB collections."""
    db = get_mongo_db()
    if db is not None:
        try:
            cursor = db.chat_feedback.find().sort('timestamp', -1).limit(limit)
            feedback = []
            for item in cursor:
                item_copy = dict(item)
                item_copy['_id'] = str(item_copy.get('_id', ''))
                feedback.append(item_copy)
            if feedback:
                return feedback
        except Exception as e:
            logger.error(f"Error fetching feedback from MongoDB: {e}")

    return _load_json_list(FEEDBACK_FILE)[:limit]


def get_all_mongo_items(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve items stored in MongoDB collection 'reported_items'."""
    db = get_mongo_db()
    if db is not None:
        try:
            cursor = db.reported_items.find().sort('created_at', -1).limit(limit)
            items = []
            for it in cursor:
                c = dict(it)
                c['_id'] = str(c.get('_id', ''))
                items.append(c)
            if items:
                return items
        except Exception as e:
            logger.error(f"Error fetching items from MongoDB: {e}")
    return _load_json_list(ITEMS_BACKUP_FILE)[:limit]


def log_auth_event(
    event: str,
    user=None,
    identifier: str = '',
    request=None,
    error: str = ''
) -> Dict[str, Any]:
    """Store authentication events (login success, login failure, logout) in MongoDB Atlas."""
    ip_address = '127.0.0.1'
    user_agent = 'Unknown'
    if request:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')[:140]

    username = user.username if user and hasattr(user, 'username') else (identifier or 'anonymous')
    email = user.email if user and hasattr(user, 'email') else (identifier if '@' in identifier else '')

    doc = {
        'event': event,
        'status': 'SUCCESS' if event == 'LOGIN_SUCCESS' else ('FAILED' if event == 'LOGIN_FAILED' else 'LOGOUT'),
        'username': username,
        'email': email,
        'identifier': identifier or username,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'error': error,
        'timestamp': datetime.utcnow().isoformat(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            result = db.auth_logs.insert_one(dict(doc))
            doc['_id'] = str(result.inserted_id)
            doc['storage'] = 'mongodb_atlas' if is_atlas_connected() else ('mongodb_live' if is_live_mongo() else 'mongodb_embedded')
        except Exception as e:
            logger.error(f"Failed to write auth log to MongoDB: {e}")

    # Synchronize to persistent JSON file for backup durability
    current_auth = _load_json_list(AUTH_LOGS_FILE)
    current_auth.insert(0, doc)
    _save_json_list(AUTH_LOGS_FILE, current_auth[:100])
    return doc


def get_all_auth_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent authentication logs from MongoDB collections."""
    db = get_mongo_db()
    if db is not None:
        try:
            cursor = db.auth_logs.find().sort('timestamp', -1).limit(limit)
            logs = []
            for item in cursor:
                item_copy = dict(item)
                item_copy['_id'] = str(item_copy.get('_id', ''))
                logs.append(item_copy)
            if logs:
                return logs
        except Exception as e:
            logger.error(f"Error fetching auth logs from MongoDB: {e}")

    return _load_json_list(AUTH_LOGS_FILE)[:limit]


def configure_mongo_uri(new_uri: str) -> Dict[str, Any]:
    """
    Test and save a new MongoDB URI (e.g., from MongoDB Atlas).
    Validates connection, updates .env file, reloads settings, and migrates existing collections.
    """
    clean_uri = new_uri.strip()
    if not clean_uri:
        return {'success': False, 'error': 'Connection string cannot be empty.'}

    # Test the connection
    try:
        from pymongo import MongoClient
        test_client = MongoClient(clean_uri, serverSelectionTimeoutMS=8000)
        test_client.admin.command('ping')
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to connect to MongoDB with provided URI: {str(e)}",
            'tip': "Make sure: 1) Your database username/password are correct. 2) In MongoDB Atlas -> Network Access, add IP 0.0.0.0/0 (allow from anywhere)."
        }

    # Update .env file
    env_file = Path(settings.BASE_DIR) / '.env'
    try:
        lines = []
        updated = False
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.startswith('MONGO_URI='):
                    new_lines.append(f"MONGO_URI={clean_uri}\n")
                    updated = True
                else:
                    new_lines.append(line)
            lines = new_lines
        if not updated:
            lines.append(f"\nMONGO_URI={clean_uri}\n")

        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        logger.error(f"Failed to write to .env: {e}")

    # Update in-memory settings
    settings.MONGO_URI = clean_uri
    os.environ['MONGO_URI'] = clean_uri

    # Migrate existing data into the new MongoDB database
    try:
        db_name = getattr(settings, 'MONGO_DB_NAME', 'campus_lost_found')
        new_db = test_client[db_name]
        
        # Migrate chat logs
        for log in _load_json_list(CHAT_LOGS_FILE):
            log_c = dict(log)
            log_c.pop('_id', None)
            new_db.chat_logs.update_one(
                {'session_id': log_c.get('session_id'), 'timestamp': log_c.get('timestamp')},
                {'$set': log_c},
                upsert=True
            )

        # Migrate feedback
        for fb in _load_json_list(FEEDBACK_FILE):
            fb_c = dict(fb)
            fb_c.pop('_id', None)
            new_db.chat_feedback.update_one(
                {'session_id': fb_c.get('session_id'), 'timestamp': fb_c.get('timestamp')},
                {'$set': fb_c},
                upsert=True
            )

        # Migrate items from SQLite
        from items.models import Item
        for item in Item.objects.all():
            sync_item_to_mongo(item)
    except Exception as e:
        logger.warning(f"Error migrating data to new MongoDB: {e}")

    is_atlas = 'mongodb.net' in clean_uri or '+srv' in clean_uri
    return {
        'success': True,
        'message': 'Connected to MongoDB Atlas Cloud Cluster successfully! Data synchronized.' if is_atlas else 'Connected to MongoDB successfully!',
        'engine': 'MongoDB Atlas (Cloud)' if is_atlas else 'MongoDB Server (Live)'
    }


def check_mongo_health() -> Dict[str, Any]:
    """Check MongoDB connectivity status for /health/ and /api/health/ endpoints."""
    live = is_live_mongo()
    atlas = is_atlas_connected()
    db_name = getattr(settings, 'MONGO_DB_NAME', 'campus_lost_found')
    mongo_uri = getattr(settings, 'MONGO_URI', os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
    
    chat_count = len(get_all_chat_logs(100))
    fb_count = len(get_all_feedback(100))
    items_count = len(get_all_mongo_items(100))
    auth_count = len(get_all_auth_logs(100))

    if atlas:
        cluster_host = mongo_uri.split('@')[-1].split('/')[0] if '@' in mongo_uri else 'Atlas Cluster'
        return {
            'status': 'connected',
            'storage_engine': f'MongoDB Atlas Cloud ({cluster_host})',
            'database': db_name,
            'is_atlas': True,
            'is_live': True,
            'uri_display': f"mongodb+srv://****:****@{cluster_host}",
            'chat_logs_count': chat_count,
            'feedback_count': fb_count,
            'reported_items_count': items_count,
            'auth_logs_count': auth_count,
            'collections': ['chat_logs', 'chat_feedback', 'reported_items', 'auth_logs']
        }
    elif live:
        return {
            'status': 'connected',
            'storage_engine': 'MongoDB Server (Live on D: Drive)',
            'database': db_name,
            'is_atlas': False,
            'is_live': True,
            'uri_display': mongo_uri.split('@')[-1],
            'chat_logs_count': chat_count,
            'feedback_count': fb_count,
            'reported_items_count': items_count,
            'auth_logs_count': auth_count,
            'collections': ['chat_logs', 'chat_feedback', 'reported_items', 'auth_logs']
        }
    return {
        'status': 'connected',
        'storage_engine': 'MongoDB Embedded Engine (Persistent)',
        'database': db_name,
        'is_atlas': False,
        'is_live': False,
        'uri_display': 'embedded://campus_lost_found',
        'chat_logs_count': chat_count,
        'feedback_count': fb_count,
        'reported_items_count': items_count,
        'auth_logs_count': auth_count,
        'collections': ['chat_logs', 'chat_feedback', 'reported_items', 'auth_logs'],
        'persistence_path': str(CHAT_LOGS_FILE)
    }
