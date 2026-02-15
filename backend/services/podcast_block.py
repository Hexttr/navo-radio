"""
NAVO RADIO — блок подкастов.
Файлы из podcasts/ по расписанию: 11→1.mp3, 16→2.mp3, 19→3.mp3, 22→4.mp4
"""
from pathlib import Path

from config import PODCASTS_DIR

from .streamer import enqueue_track, start_continuous_stream


def run_podcast_block(filename: str) -> bool:
    """Проиграть подкаст. Возвращает True если успешно."""
    path = PODCASTS_DIR / filename
    if not path.exists():
        print(f"[PODCAST] Файл не найден: {path}")
        return False

    if start_continuous_stream() and enqueue_track(None, path):
        print(f"[PODCAST] {filename}")
        return True
    return False
