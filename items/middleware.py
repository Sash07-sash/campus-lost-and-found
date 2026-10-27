import os
import time
import logging
from datetime import datetime
from pathlib import Path
from django.conf import settings

logger = logging.getLogger('request_logger')

# In-memory metrics tracking for the /health/ endpoint
REQUEST_METRICS = {
    'total_requests': 0,
    'total_errors': 0,
    'total_duration_ms': 0.0,
    'recent_requests': []
}


class RequestLoggingMiddleware:
    """
    Middleware that records HTTP method, endpoint path, response status,
    client IP, and request duration (in milliseconds) into logs/request.log.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_dir = Path(settings.BASE_DIR) / 'logs'
        try:
            self.log_dir.mkdir(exist_ok=True)
        except Exception:
            pass
        self.log_file = self.log_dir / 'request.log'

    def __call__(self, request):
        start_time = time.time()

        # Capture response
        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        status_code = getattr(response, 'status_code', 500)
        user_repr = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'Anonymous'
        ip = self._get_client_ip(request)

        log_line = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{request.method} {request.get_full_path()} "
            f"Status:{status_code} "
            f"Time:{duration_ms}ms "
            f"IP:{ip} "
            f"User:{user_repr}\n"
        )

        # Write to logs/request.log
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            logger.error(f"Error writing to request log: {e}")

        # Update live metrics
        REQUEST_METRICS['total_requests'] += 1
        REQUEST_METRICS['total_duration_ms'] += duration_ms
        if status_code >= 400:
            REQUEST_METRICS['total_errors'] += 1

        REQUEST_METRICS['recent_requests'].insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'method': request.method,
            'path': request.path,
            'status': status_code,
            'duration_ms': duration_ms,
            'user': user_repr
        })
        if len(REQUEST_METRICS['recent_requests']) > 50:
            REQUEST_METRICS['recent_requests'].pop()

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
