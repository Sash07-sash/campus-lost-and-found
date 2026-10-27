from .third_party_api import get_campus_weather_and_status


def campus_environment(request):
    """Make campus environmental data and live status available across all templates."""
    try:
        env_data = get_campus_weather_and_status()
    except Exception:
        env_data = {
            'temperature': 24.0,
            'weather_condition': 'Clear',
            'campus_status': 'All Campus Facilities & Grounds Open',
            'is_fallback': True
        }
    return {
        'campus_env': env_data
    }
