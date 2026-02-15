"""
NAVO RADIO — аудиозаставка.
Короткий mp3 (название радио) раз в час.
"""
from pathlib import Path

from config import JINGLES_DIR, JINGLE_FILE

from .streamer import enqueue_track, start_continuous_stream


def run_jingle_block() -> bool:
    """Проиграть заставку. Возвращает True если успешно."""
    JINGLES_DIR.mkdir(parents=True, exist_ok=True)
    jingle_path = JINGLES_DIR / JINGLE_FILE
    if not jingle_path.exists():
        print(f"[JINGLE] Файл не найден: {jingle_path}. Положите jingle.mp3 в папку jingles/")
        return False

    if start_continuous_stream() and enqueue_track(None, jingle_path):
        print("[JINGLE] Заставка")
        return True
    return False
