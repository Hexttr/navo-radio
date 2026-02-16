"""
NAVO RADIO — Jamendo API.
Загрузка треков (восточная, world, folk музыка).
"""
import random
from dataclasses import dataclass
from pathlib import Path

import requests

from config import JAMENDO_CLIENT_ID, SONGS_CACHE_DIR

API_BASE = "https://api.jamendo.com/v3.0/tracks"
# Теги: восточная музыка, приоритет — Таджикистан и Центральная Азия
# tajik — таджикские артисты; oriental — восточная; persian — персидская; asia — азиатская
TAGS = ["tajik", "oriental", "persian", "asia", "world", "folk", "ethnic"]

# История воспроизведённых треков — не повторять последние N
_RECENTLY_PLAYED: list[str] = []
_RECENTLY_PLAYED_MAX = 150


def mark_track_played(track_id: str) -> None:
    """Отметить трек как воспроизведённый (исключить из выбора на время)."""
    global _RECENTLY_PLAYED
    _RECENTLY_PLAYED = [tid for tid in _RECENTLY_PLAYED if tid != track_id]
    _RECENTLY_PLAYED.append(track_id)
    if len(_RECENTLY_PLAYED) > _RECENTLY_PLAYED_MAX:
        _RECENTLY_PLAYED = _RECENTLY_PLAYED[-_RECENTLY_PLAYED_MAX:]


@dataclass
class Track:
    """Трек из Jamendo."""
    id: str
    name: str
    artist_name: str
    album_name: str
    duration: int
    audio_url: str


def fetch_tracks(limit: int = 50, tag: str | None = None) -> list[Track]:
    """Получить треки из Jamendo API."""
    if not JAMENDO_CLIENT_ID:
        raise ValueError("JAMENDO_CLIENT_ID не задан в .env")

    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": limit,
    }
    if tag:
        params["tags"] = tag

    resp = requests.get(API_BASE, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("headers", {}).get("status") != "success":
        raise RuntimeError(f"Jamendo API error: {data}")

    results = data.get("results", [])
    tracks = []
    for r in results:
        audio = r.get("audio")
        if not audio:
            continue
        tracks.append(
            Track(
                id=str(r["id"]),
                name=r["name"],
                artist_name=r["artist_name"],
                album_name=r.get("album_name", ""),
                duration=int(r.get("duration", 0)),
                audio_url=audio,
            )
        )
    return tracks


def get_next_track() -> Track | None:
    """Получить случайный трек из объединённого пула по всем тегам, исключая недавно сыгранные."""
    global _RECENTLY_PLAYED
    excluded = set(_RECENTLY_PLAYED)
    all_tracks: list[Track] = []
    seen_ids: set[str] = set()

    for tag in TAGS:
        try:
            tracks = fetch_tracks(limit=100, tag=tag)
            for t in tracks:
                if t.id not in seen_ids and t.id not in excluded:
                    all_tracks.append(t)
                    seen_ids.add(t.id)
        except Exception:
            continue

    if not all_tracks:
        # Все треки уже недавно играли — очищаем историю и пробуем снова
        excluded.clear()
        _RECENTLY_PLAYED = []
        for tag in TAGS:
            try:
                tracks = fetch_tracks(limit=100, tag=tag)
                for t in tracks:
                    if t.id not in seen_ids:
                        all_tracks.append(t)
                        seen_ids.add(t.id)
            except Exception:
                continue

    if all_tracks:
        return random.choice(all_tracks)
    return None


def download_track(track: Track) -> Path:
    """Скачать трек в кэш, вернуть путь к файлу."""
    SONGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = SONGS_CACHE_DIR / f"track_{track.id}.mp3"

    if path.exists():
        return path

    resp = requests.get(track.audio_url, timeout=120, stream=True)
    resp.raise_for_status()

    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return path
