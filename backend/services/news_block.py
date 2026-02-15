"""
NAVO RADIO — блок новостей.
RSS ASIA-Plus (Таджикистан) → Groq → TTS → эфир.
"""
import feedparser
import requests

from .groq_client import generate_news_script
from .streamer import enqueue_track, start_continuous_stream
from .tts import text_to_speech

# ASIA-Plus — независимое агентство, Душанбе
RSS_URL = "https://asiaplustj.info/en/rss"


def _fetch_news_text() -> str:
    """Получить текст новостей из RSS."""
    try:
        resp = requests.get(RSS_URL, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        items = feed.get("entries", [])[:5]
        texts = []
        for item in items:
            title = item.get("title", "")
            summary = item.get("summary", item.get("description", ""))
            if title or summary:
                texts.append(f"{title}. {summary[:500]}")
        return "\n\n".join(texts) if texts else ""
    except Exception as e:
        print(f"[NEWS] RSS ошибка: {e}")
        return ""


def run_news_block() -> bool:
    """Выпуск новостей. Возвращает True если успешно."""
    news_text = _fetch_news_text()
    script = generate_news_script(news_text)

    try:
        path = text_to_speech(script, filename="news_latest.mp3")
    except Exception as e:
        print(f"[NEWS] TTS ошибка: {e}")
        return False

    if start_continuous_stream() and enqueue_track(None, path):
        print("[NEWS] Выпуск новостей")
        return True
    return False
