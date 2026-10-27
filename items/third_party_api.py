import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback campus environmental data if external API times out or is offline
DEFAULT_FALLBACK_DATA = {
    'temperature': 24.0,
    'weather_condition': 'Clear & Sunny',
    'wind_speed': 10.5,
    'campus_status': 'All Academic Blocks, Library & Grounds Open',
    'is_fallback': True,
    'source': 'Campus Emergency Cache (Local Fallback)'
}

# Weather code translation for Open-Meteo
WEATHER_CODES = {
    0: 'Clear Sky',
    1: 'Mainly Clear',
    2: 'Partly Cloudy',
    3: 'Overcast',
    45: 'Foggy',
    51: 'Light Drizzle',
    61: 'Light Rain',
    63: 'Moderate Rain',
    71: 'Light Snow',
    80: 'Rain Showers',
    95: 'Thunderstorm'
}


def get_campus_weather_and_status():
    """
    Fetch live environmental conditions for campus grounds via external API.
    Strictly enforced timeout (default 3.0 seconds) with reliable local fallback.
    """
    timeout = getattr(settings, 'THIRD_PARTY_API_TIMEOUT', 3.0)
    api_url = "https://api.open-meteo.com/v1/forecast?latitude=12.9716&longitude=77.5946&current_weather=true"

    try:
        response = requests.get(api_url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current_weather', {})
            w_code = current.get('weathercode', 0)
            condition = WEATHER_CODES.get(w_code, 'Fair Conditions')

            return {
                'temperature': current.get('temperature', 24.0),
                'weather_condition': condition,
                'wind_speed': current.get('windspeed', 8.0),
                'campus_status': 'All Grounds & Outdoor Spots Operational',
                'is_fallback': False,
                'source': 'Live Open-Meteo External API'
            }
        else:
            logger.warning(f"Third-party API returned status {response.status_code}. Using fallback.")
    except requests.exceptions.Timeout:
        logger.warning(f"Third-party API timed out after {timeout}s. Engaging graceful fallback.")
    except Exception as e:
        logger.warning(f"Third-party API request failed: {e}. Engaging graceful fallback.")

    return DEFAULT_FALLBACK_DATA


def check_third_party_health():
    """Health check helper for the third-party API integration."""
    timeout = getattr(settings, 'THIRD_PARTY_API_TIMEOUT', 3.0)
    try:
        res = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=12.9716&longitude=77.5946&current_weather=true",
            timeout=timeout
        )
        if res.status_code == 200:
            return {'status': 'reachable', 'http_code': 200, 'timeout_sec': timeout}
        return {'status': 'degraded', 'http_code': res.status_code, 'timeout_sec': timeout}
    except Exception as e:
        return {'status': 'offline_fallback_active', 'error': str(e), 'timeout_sec': timeout}
