"""
NAVO RADIO — блок погоды.
WeatherAPI.com (Душанбе) → Groq → TTS → эфир.
"""
import requests

from config import WEATHER_API_KEY

from .groq_client import generate_weather_script
from .streamer import enqueue_track, start_continuous_stream
from .tts import text_to_speech

# Душанбе
LAT, LON = 38.54, 68.78
WEATHER_API_URL = "https://api.weatherapi.com/v1/current.json"


def _fetch_weather_data() -> str:
    """Получить данные погоды."""
    if not WEATHER_API_KEY:
        return ""

    try:
        resp = requests.get(
            WEATHER_API_URL,
            params={"key": WEATHER_API_KEY, "q": f"{LAT},{LON}", "lang": "ru"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        loc = data.get("location", {})
        temp = current.get("temp_c", "?")
        condition = current.get("condition", {}).get("text", "")
        wind = current.get("wind_kph", 0)
        return f"Город: {loc.get('name', 'Душанбе')}. Температура {temp}°C. {condition}. Ветер {wind} км/ч."
    except Exception as e:
        print(f"[WEATHER] API ошибка: {e}")
        return ""


def run_weather_block() -> bool:
    """Прогноз погоды. Возвращает True если успешно."""
    weather_data = _fetch_weather_data()
    script = generate_weather_script(weather_data)

    try:
        path = text_to_speech(script, filename="weather_latest.mp3")
    except Exception as e:
        print(f"[WEATHER] TTS ошибка: {e}")
        return False

    if start_continuous_stream() and enqueue_track(None, path):
        print("[WEATHER] Прогноз погоды")
        return True
    return False
