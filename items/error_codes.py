"""
Catalog of 8 standard and site-specific error codes for Campus Lost & Found.
Covers: 400, 401, 403, 404, 429, 500, 503, and site-specific CLF-1001.
"""

ERROR_CATALOG = {
    '400': {
        'code': '400',
        'title': 'Bad Request',
        'category': 'Client Error',
        'summary': 'The server could not understand the request due to malformed syntax or invalid parameters.',
        'student_explanation': 'This usually happens if an invalid form value, an unsupported date format, or corrupted form data was submitted.',
        'campus_troubleshooting': [
            'Check your input fields for unsupported special characters.',
            'Ensure dates follow the standard calendar format (YYYY-MM-DD).',
            'Refresh the page and re-submit the form.'
        ],
        'http_status': 400,
    },
    '401': {
        'code': '401',
        'title': 'Unauthorized',
        'category': 'Authentication Error',
        'summary': 'Authentication credentials are required to access this campus resource.',
        'student_explanation': 'You must be signed in with your college account to view personal dashboards, report items, or submit recovery claims.',
        'campus_troubleshooting': [
            'Sign in using your student or staff username and password.',
            'If you do not have an account, click Register on the top navigation bar.',
            'Check if your browser session expired after inactivity.'
        ],
        'http_status': 401,
    },
    '403': {
        'code': '403',
        'title': 'Forbidden',
        'category': 'Permission / Security Error',
        'summary': 'Access to the requested resource is denied by campus safety policies.',
        'student_explanation': 'You are logged in, but you do not have permission to modify this listing (e.g. only the owner can edit listings), or a CSRF token mismatch occurred.',
        'campus_troubleshooting': [
            'Ensure you are logged into the account that originally created the listing.',
            'If you see a CSRF token error, hard refresh the page (Ctrl + F5) and try again.',
            'Remember: you cannot file a recovery claim on an item you reported yourself.'
        ],
        'http_status': 403,
    },
    '404': {
        'code': '404',
        'title': 'Page or Item Not Found',
        'category': 'Resource Error',
        'summary': 'The requested page, item ID, or URL path could not be found on the campus server.',
        'student_explanation': 'The listing you are trying to view may have been removed by the owner, marked as recovered, or the URL address contains a typo.',
        'campus_troubleshooting': [
            'Double-check the web address or item ID number.',
            'Use the Browse Listings page to search for the item by title or location.',
            'Ask the AI Assistant in the bottom right corner for help locating the item.'
        ],
        'http_status': 404,
    },
    '429': {
        'code': '429',
        'title': 'Too Many Requests',
        'category': 'Rate Limiting',
        'summary': 'The client has sent too many requests in a given amount of time.',
        'student_explanation': 'To prevent automated spam and protect campus services, rapid successive submissions are temporarily throttled.',
        'campus_troubleshooting': [
            'Wait 30-60 seconds before submitting another search query or claim.',
            'Avoid rapid repeated clicking on form submit buttons.'
        ],
        'http_status': 429,
    },
    '500': {
        'code': '500',
        'title': 'Internal Server Error',
        'category': 'Server Error',
        'summary': 'The campus server encountered an unexpected condition that prevented it from fulfilling the request.',
        'student_explanation': 'An unexpected technical glitch occurred on the server. Our campus IT team has been automatically logged with the incident.',
        'campus_troubleshooting': [
            'Refresh the page after a few seconds.',
            'Use the "Ask the Assistant" button to report the issue or file a Support Ticket.',
            'Check the /health/ endpoint to verify campus service status.'
        ],
        'http_status': 500,
    },
    '503': {
        'code': '503',
        'title': 'Service Unavailable',
        'category': 'Availability Error',
        'summary': 'The campus service is temporarily offline due to maintenance or capacity overload.',
        'student_explanation': 'The database or college web server is undergoing scheduled updates or temporary maintenance.',
        'campus_troubleshooting': [
            'Wait a few minutes and try again.',
            'Check campus announcements or contact the IT Helpdesk.',
            'Review our status on the /health/ check page.'
        ],
        'http_status': 503,
    },
    'CLF-1001': {
        'code': 'CLF-1001',
        'title': 'Item Report Processing Failure',
        'category': 'Site-Specific Error (Campus Lost & Found)',
        'summary': 'An error occurred while validating or attaching media to a campus item report.',
        'student_explanation': 'This custom campus code indicates that an uploaded photo failed validation (exceeded 5MB limit, corrupt file, or unsupported format like PDF/EXE instead of JPG/PNG/WEBP).',
        'campus_troubleshooting': [
            'Ensure the uploaded photo is under 5MB in file size.',
            'Convert the image to JPG, PNG, or WEBP format before uploading.',
            'Try submitting the listing without an image first, then add it later.'
        ],
        'http_status': 422,
    }
}


def get_all_error_codes():
    """
    Retrieve all error codes from SQL table items_errorcode.
    Assessment Requirement: Minimum 8 Error Codes stored in SQL.
    Falls back gracefully to ERROR_CATALOG dictionary.
    """
    try:
        from .models import ErrorCode
        sql_codes = ErrorCode.objects.filter(is_active=True)
        if sql_codes.count() >= 8:
            result = {}
            for ec in sql_codes:
                result[ec.code] = {
                    'code': ec.code,
                    'title': ec.title,
                    'category': ec.category,
                    'summary': ec.summary,
                    'student_explanation': ec.student_explanation,
                    'campus_troubleshooting': ec.get_troubleshooting_list(),
                    'http_status': ec.http_status,
                }
            return result
    except Exception:
        pass
    return ERROR_CATALOG


def get_error_info(code: str):
    """Retrieve detailed metadata for an error code from SQL or dictionary fallback."""
    code_str = str(code).strip().upper()
    try:
        from .models import ErrorCode
        ec = ErrorCode.objects.filter(code__iexact=code_str, is_active=True).first()
        if ec:
            return {
                'code': ec.code,
                'title': ec.title,
                'category': ec.category,
                'summary': ec.summary,
                'student_explanation': ec.student_explanation,
                'campus_troubleshooting': ec.get_troubleshooting_list(),
                'http_status': ec.http_status,
            }
    except Exception:
        pass
    return ERROR_CATALOG.get(code_str)

