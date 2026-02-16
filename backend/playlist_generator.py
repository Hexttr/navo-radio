"""
NAVO RADIO — генерация плейлиста на день.
Создаёт последовательность сущностей по расписанию (МСК).
Тексты генерируются, озвучка — отдельным шагом.
"""
from datetime import date, datetime
from pathlib import Path

import pytz

from config import (
    FFMPEG_PATH,
    JINGLES_DIR,
    NEWS_HOURS,
    PODCASTS_DIR,
    PODCAST_FILES,
    PODCAST_HOURS,
    PROJECT_ROOT,
    SONGS_CACHE_DIR,
    TIMEZONE,
    WEATHER_HOURS,
)
from schemas import EntityType

from services.jamendo import download_track, get_next_track, mark_track_played
from services.groq_client import generate_dj_intro, generate_news_script, generate_weather_script
from services.news_block import _fetch_news_text
from services.weather_block import _fetch_weather_data


def _get_jingle_files() -> list[Path]:
    """Список доступных интро (mp3 в jingles/). При отсутствии — создаём тишину как fallback."""
    if JINGLES_DIR.exists():
        files = sorted(JINGLES_DIR.glob("*.mp3"))
        if files:
            return files
    # Fallback: тишина 3 сек
    JINGLES_DIR.mkdir(parents=True, exist_ok=True)
    fallback = JINGLES_DIR / "jingle.mp3"
    if not fallback.exists():
        import subprocess
        ffmpeg = FFMPEG_PATH or "ffmpeg"
        subprocess.run(
            [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "3",
             "-q:a", "9", "-acodec", "libmp3lame", str(fallback)],
            capture_output=True,
            timeout=10,
        )
    return [fallback] if fallback.exists() else []


def _get_podcast_files() -> list[Path]:
    """Список доступных подкастов."""
    if not PODCASTS_DIR.exists():
        return []
    files = []
    for f in PODCAST_FILES:
        p = PODCASTS_DIR / f
        if p.exists():
            files.append(p)
    for ext in ("*.mp3", "*.mp4"):
        for p in PODCASTS_DIR.glob(ext):
            if p not in files:
                files.append(p)
    return sorted(set(files), key=lambda x: x.name)


def generate_playlist_for_day(day: date, max_hours: int | None = None) -> dict:
    """
    Генерация плейлиста: для каждого часа — intro, затем якорное (news/weather/podcast),
    затем музыка (DJ+Song) до конца часа.
    max_hours: только первые N часов (для быстрого теста).
    """
    jingles = _get_jingle_files()
    podcasts = _get_podcast_files()
    tz = pytz.timezone(TIMEZONE)
    hour_limit = max_hours if max_hours else 24

    entities: list[dict] = []
    podcast_idx = 0

    for hour in range(hour_limit):
        # Интро в начале часа
        if jingles:
            j = jingles[hour % len(jingles)]
            rel = str(j.relative_to(PROJECT_ROOT)).replace("\\", "/")
            entities.append({
                "type": EntityType.INTRO.value,
                "file": rel,
                "duration": 0,
                "text": None,
                "audio": None,
            })
        else:
            default = JINGLES_DIR / "jingle.mp3"
            if default.exists():
                entities.append({
                    "type": EntityType.INTRO.value,
                    "file": f"jingles/jingle.mp3",
                    "duration": 0,
                    "text": None,
                    "audio": None,
                })

        # Якорное событие
        if hour in NEWS_HOURS:
            news_text = _fetch_news_text()
            script = generate_news_script(news_text)
            entities.append({
                "type": EntityType.NEWS.value,
                "text": script,
                "audio": None,
                "file": None,
                "duration": 0,
            })
        elif hour in WEATHER_HOURS:
            wdata = _fetch_weather_data()
            script = generate_weather_script(wdata)
            entities.append({
                "type": EntityType.WEATHER.value,
                "text": script,
                "audio": None,
                "file": None,
                "duration": 0,
            })
        elif hour in PODCAST_HOURS:
            if podcasts:
                p = podcasts[podcast_idx % len(podcasts)]
                podcast_idx += 1
                rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
                entities.append({
                    "type": EntityType.PODCAST.value,
                    "file": rel,
                    "duration": 0,
                    "text": None,
                    "audio": None,
                })

        # Музыка: 3-4 трека на час
        for _ in range(4):
            track = get_next_track()
            if not track:
                break
            try:
                track_path = download_track(track)
                mark_track_played(track.id)
                file_rel = str(track_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except Exception:
                continue

            dj_text = generate_dj_intro(
                track_name=track.name,
                artist_name=track.artist_name,
                album_name=track.album_name,
            )

            entities.append({
                "type": EntityType.DJ.value,
                "text": dj_text,
                "audio": None,
                "file": None,
                "duration": 0,
                "linkedTo": f"song_{track.id}",
            })
            entities.append({
                "type": EntityType.SONG.value,
                "id": f"song_{track.id}",
                "file": file_rel,
                "duration": track.duration,
                "artist": track.artist_name,
                "name": track.name,
            })

    return {
        "date": day.isoformat(),
        "createdAt": datetime.now(tz).isoformat(),
        "entities": entities,
    }
