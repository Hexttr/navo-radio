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
