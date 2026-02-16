"""
NAVO RADIO — хранение и загрузка плейлистов (JSON).
"""
import json
from datetime import date
from pathlib import Path

from config import PLAYLISTS_DIR


def _playlist_path(day: date) -> Path:
    PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)
    return PLAYLISTS_DIR / f"{day.isoformat()}.json"


def load_playlist(day: date) -> dict | None:
    """Загрузить плейлист на день. None если не существует."""
    path = _playlist_path(day)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_playlist(day: date, data: dict) -> None:
    """Сохранить плейлист."""
    path = _playlist_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def playlist_exists(day: date) -> bool:
    """Проверить, есть ли плейлист на день."""
    return _playlist_path(day).exists()


def list_playlist_dates() -> list[str]:
    """Список дат, для которых есть плейлисты (YYYY-MM-DD)."""
    if not PLAYLISTS_DIR.exists():
        return []
    dates = []
    for p in PLAYLISTS_DIR.glob("*.json"):
        try:
            dates.append(p.stem)
        except ValueError:
            continue
    return sorted(dates)
