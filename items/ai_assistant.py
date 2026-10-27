import os
import re
import uuid
from typing import Dict, Any, Optional
from django.conf import settings
from .models import FAQ, SupportTicket
from .error_codes import ERROR_CATALOG, get_error_info
from .mongo_service import log_chat_interaction

STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'is', 'in', 'at', 'to', 'for', 'of', 'with',
    'how', 'what', 'why', 'can', 'do', 'does', 'did', 'i', 'my', 'me', 'please',
    'tell', 'explain', 'show', 'need', 'help', 'want'
}


def tokenize(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z0-9_-]+', text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


def find_matching_faq(query: str):
    """Fuzzy match user query against SQL FAQ records."""
    faqs = FAQ.objects.filter(is_active=True)
    query_tokens = tokenize(query)
    if not query_tokens:
        return None, 0.0

    best_faq = None
    best_score = 0.0

    for faq in faqs:
        q_tokens = tokenize(faq.question)
        a_tokens = tokenize(faq.answer)
        combined_tokens = q_tokens | a_tokens

        overlap = len(query_tokens & q_tokens) * 3 + len(query_tokens & a_tokens)
        score = overlap / max(len(query_tokens), 1)

        # Exact substring bonus
        if faq.question.lower() in query.lower() or query.lower() in faq.question.lower():
            score += 5.0

        if score > best_score:
            best_score = score
            best_faq = faq

    return best_faq, best_score


def find_matching_error(query: str):
    """Detect if the student is asking about an error code."""
    cleaned = query.upper()
    for code, info in ERROR_CATALOG.items():
        if code in cleaned or info['title'].upper() in cleaned:
            return info
    return None


def generate_ai_response(user_message: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Main AI reasoning pipeline:
    1. Check for error code queries
    2. Check for ticket submission requests
    3. Search SQL FAQ database
    4. Optional Gemini/OpenAI API enhancement
    5. Fallback with automatic support ticket offer
    6. Log interaction to MongoDB
    """
    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

    cleaned_msg = user_message.strip()
    username = user.username if user and user.is_authenticated else 'Student'

    matched_faq_id = None
    matched_error_code = None
    can_create_ticket = False
    ai_answer = ""

    # Common greetings handler (Instant friendly response, no support ticket needed)
    greetings = {'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', 'yo'}
    if cleaned_msg.lower().strip() in greetings:
        display_name = f" {username}" if username and username != 'Student' else ""
        ai_answer = (
            f"Hello{display_name}! I'm your Campus Lost & Found Assistant. "
            "I'm here to help you report lost belongings, find misplaced items, understand recovery claims, or explain error codes. "
            "What can I help you with today?"
        )
        can_create_ticket = False

    # 1. Error Code Explanation Query
    elif (error_info := find_matching_error(cleaned_msg)):
        matched_error_code = error_info['code']
        ai_answer = (
            f"⚠️ **Error {error_info['code']}: {error_info['title']}**\n\n"
            f"{error_info['student_explanation']}\n\n"
            f"**Campus Troubleshooting Steps:**\n" +
            "\n".join([f"• {step}" for step in error_info['campus_troubleshooting']]) +
            f"\n\n*If this error persists, you can submit a support ticket below!*"
        )
        can_create_ticket = True

    # 2. Check if student explicitly wants to create a ticket
    elif any(phrase in cleaned_msg.lower() for phrase in ['ticket', 'create ticket', 'contact admin', 'human help', 'support agent', 'file a complaint']):
        ai_answer = (
            "I'd be glad to help you create a formal Support Ticket for our campus administration team. "
            "Please click the **'Create Support Ticket'** button below to describe your issue and receive an official tracking number."
        )
        can_create_ticket = True

    # 3. Match against SQL FAQ database
    else:
        faq, score = find_matching_faq(cleaned_msg)
        if faq and score >= 2.0:
            matched_faq_id = faq.id
            ai_answer = (
                f"**{faq.question}**\n\n"
                f"{faq.answer}\n\n"
                f"*(Category: {faq.get_category_display()})*"
            )
        else:
            # 4. Google Gemini API Enhancement
            gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
            if gemini_key:
                try:
                    import requests
                    for model in ['gemini-3.1-flash-lite', 'gemini-3.5-flash', 'gemini-3-flash-preview']:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                        payload = {
                            "contents": [{
                                "parts": [{
                                    "text": (
                                        "You are the official friendly Campus Lost & Found AI Assistant for a college campus. "
                                        "Help the student with practical, warm advice on recovering lost belongings, reporting found items, "
                                        "campus safety verification, and visiting campus security/library desks. "
                                        "Keep your answer under 3-4 sentences.\n\n"
                                        f"Student: {cleaned_msg}"
                                    )
                                }]
                            }],
                            "generationConfig": {
                                "maxOutputTokens": 320,
                                "temperature": 0.6,
                                "thinkingConfig": {
                                    "thinkingBudget": 0
                                }
                            }
                        }
                        try:
                            resp = requests.post(url, json=payload, timeout=7.0)
                            if resp.status_code == 200:
                                data = resp.json()
                                candidates = data.get('candidates', [])
                                if candidates and 'content' in candidates[0]:
                                    parts = candidates[0]['content'].get('parts', [])
                                    if parts and 'text' in parts[0]:
                                        raw_text = parts[0]['text'].strip()
                                        ai_answer = f"{raw_text}\n\n*(Answered by Google Gemini AI - {model})*"
                                        can_create_ticket = True
                                        break
                        except Exception:
                            continue
                except Exception:
                    pass

            # 5. Fallback response with ticket creation offer
            if not ai_answer:
                ai_answer = (
                    f"I couldn't locate a verified answer for '{cleaned_msg}' in our campus knowledge base. "
                    "Don't worry! You can submit a **Support Ticket** directly to the college administration desk, "
                    "or browse all FAQs on our Help page."
                )
                can_create_ticket = True

    # 6. Log interaction to MongoDB
    log_doc = log_chat_interaction(
        session_id=session_id,
        user=username,
        user_message=cleaned_msg,
        ai_response=ai_answer,
        matched_faq_id=matched_faq_id,
        error_code=matched_error_code
    )

    return {
        'session_id': session_id,
        'answer': ai_answer,
        'matched_faq_id': matched_faq_id,
        'error_code': matched_error_code,
        'can_create_ticket': can_create_ticket,
        'storage': log_doc.get('storage', 'mongodb')
    }
