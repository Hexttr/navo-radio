"""
NAVO RADIO — TTS (Text-to-Speech).
Edge TTS по умолчанию, ElevenLabs опционально.
"""
import asyncio
from pathlib import Path

from config import CACHE_DIR, ELEVENLABS_API_KEY, TTS_PROVIDER

# Русский голос Edge TTS (мужской, нейтральный)
EDGE_VOICE = "ru-RU-DmitryNeural"


async def _edge_tts(text: str, output_path: Path) -> None:
    """Озвучить текст через Edge TTS."""
    import edge_tts

    communicate = edge_tts.Communicate(text, EDGE_VOICE)
    await communicate.save(str(output_path))


def text_to_speech(text: str, filename: str = "intro.mp3") -> Path:
    """
    Озвучить текст, сохранить в кэш.
    Возвращает путь к файлу.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CACHE_DIR / filename

    if TTS_PROVIDER == "elevenlabs" and ELEVENLABS_API_KEY:
        _elevenlabs_tts(text, output_path)
    else:
        asyncio.run(_edge_tts(text, output_path))

    return output_path


def _elevenlabs_tts(text: str, output_path: Path) -> None:
    """Озвучить через ElevenLabs API."""
    import requests

    url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
    }

    resp = requests.post(url, json=data, headers=headers, timeout=30)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)
