"""
NAVO RADIO — Groq AI.
Генерация текстов: DJ-интро, сценарии новостей и погоды.
"""
from groq import Groq

from config import GROQ_API_KEY

DJ_INTRO_PROMPT = """Ты — ведущий радио NAVO RADIO. Перед треком нужно сказать 2-3 короткие фразы на русском.
Трек: "{track_name}"
Исполнитель: {artist_name}
Альбом: {album_name}

Напиши ТОЛЬКО текст для озвучки, без кавычек и пояснений. 1-3 предложения. Неформально, тепло. Не упоминай название трека в конце."""


def _fallback_intro(track_name: str, artist_name: str) -> str:
    return f"Сейчас в эфире — {artist_name} с композицией {track_name}."


def generate_dj_intro(track_name: str, artist_name: str, album_name: str = "") -> str:
    """Сгенерировать DJ-интро перед треком."""
    if not GROQ_API_KEY:
        return _fallback_intro(track_name, artist_name)

    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = DJ_INTRO_PROMPT.format(
            track_name=track_name,
            artist_name=artist_name,
            album_name=album_name or "—",
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )

        text = response.choices[0].message.content.strip()
        return text if text else _fallback_intro(track_name, artist_name)
    except Exception as e:
        print(f"[GROQ] Ошибка, используем fallback: {e}")
        return _fallback_intro(track_name, artist_name)


NEWS_SCRIPT_PROMPT = """Ты — ведущий радио NAVO RADIO. На основе этих новостей из Таджикистана/Душанбе составь короткий выпуск новостей на русском.
Текст должен быть 3-5 предложений для озвучки. Только факты, без комментариев. Напиши ТОЛЬКО текст для озвучки.

Новости:
{news_text}"""


def generate_news_script(news_text: str) -> str:
    """Сгенерировать сценарий выпуска новостей."""
    if not GROQ_API_KEY or not news_text.strip():
        return "Новости временно недоступны."

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": NEWS_SCRIPT_PROMPT.format(news_text=news_text[:3000])}],
            max_tokens=300,
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        return text if text else "Новости временно недоступны."
    except Exception as e:
        print(f"[GROQ] Ошибка новостей: {e}")
        return "Новости временно недоступны."


WEATHER_SCRIPT_PROMPT = """Ты — ведущий радио NAVO RADIO. Озвучь прогноз погоды для Душанбе на русском.
Данные: {weather_data}
Напиши 2-4 короткие фразы для озвучки. Только текст, без пояснений."""


def generate_weather_script(weather_data: str) -> str:
    """Сгенерировать сценарий погоды."""
    if not GROQ_API_KEY or not weather_data.strip():
        return "Прогноз погоды временно недоступен."

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": WEATHER_SCRIPT_PROMPT.format(weather_data=weather_data)}],
            max_tokens=150,
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        return text if text else "Прогноз погоды временно недоступен."
    except Exception as e:
        print(f"[GROQ] Ошибка погоды: {e}")
        return "Прогноз погоды временно недоступен."
