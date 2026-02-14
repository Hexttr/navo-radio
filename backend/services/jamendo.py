"""
NAVO RADIO — Jamendo API.
Загрузка треков (восточная, world, folk музыка).
"""
import random
from dataclasses import dataclass
from pathlib import Path

import requests

from config import CACHE_DIR, JAMENDO_CLIENT_ID

API_BASE = "https://api.jamendo.com/v3.0/tracks"
# Теги для восточной/мировой музыки
TAGS = ["world", "folk", "ethnic"]


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
    """Получить случайный трек из пула восточной музыки."""
    tag = random.choice(TAGS)
    tracks = fetch_tracks(limit=20, tag=tag)
    if not tracks:
        return None
    return random.choice(tracks)


def download_track(track: Track) -> Path:
    """Скачать трек в кэш, вернуть путь к файлу."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"track_{track.id}.mp3"

    if path.exists():
        return path

    resp = requests.get(track.audio_url, timeout=120, stream=True)
    resp.raise_for_status()

    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return path
