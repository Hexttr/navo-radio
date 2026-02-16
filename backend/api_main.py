"""
NAVO RADIO — API для админки.
FastAPI: CRUD плейлистов, генерация, озвучка.
"""
from datetime import date, datetime
from pathlib import Path

import pytz
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import PROJECT_ROOT, TIMEZONE, TTS_CACHE_DIR
from playlist_generator import generate_playlist_for_day
from playlist_store import load_playlist, list_playlist_dates, playlist_exists, save_playlist
from schemas import (
    EntityType,
    TEXT_ENTITY_TYPES,
    compute_timings,
    entity_is_ready,
    get_entity_duration_seconds,
)

app = FastAPI(title="NAVO RADIO Admin API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models ---


class EntityUpdate(BaseModel):
    text: str | None = None


class VoiceRequest(BaseModel):
    indices: list[int] | None = None


class PlaylistResponse(BaseModel):
    date: str
    createdAt: str | None
    entities: list[dict]
    timings: list[str]


# --- Helpers ---


def _resolve_audio_duration(path: Path) -> float:
    """Получить длительность mp3 через ffprobe или 0."""
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


def _get_entity_audio_path(entity: dict) -> Path | None:
    """Путь к аудиофайлу сущности (абсолютный)."""
    audio = entity.get("audio")
    file_path = entity.get("file")
    path_str = audio or file_path
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_absolute():
        return PROJECT_ROOT / path_str.replace("\\", "/")
    return p


# --- Endpoints ---


@app.get("/api/playlists")
def get_playlist_dates():
    """Список дат с плейлистами."""
    return {"dates": list_playlist_dates()}


def _ensure_durations(entities: list[dict]) -> None:
    """Заполнить duration=0 для сущностей с файлом (через ffprobe)."""
    for ent in entities:
        if ent.get("duration"):
            continue
        path = _get_entity_audio_path(ent)
        if path and path.exists():
            ent["duration"] = _resolve_audio_duration(path)


@app.get("/api/playlists/{day}", response_model=PlaylistResponse)
def get_playlist(day: str):
    """Получить плейлист на день. Возвращает пустой плейлист, если не существует."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format (use YYYY-MM-DD)")
    data = load_playlist(d)
    if not data:
        return PlaylistResponse(
            date=day,
            createdAt=None,
            entities=[],
            timings=[],
        )
    entities = data.get("entities", [])
    _ensure_durations(entities)
    timings = compute_timings(entities)
    return PlaylistResponse(
        date=data["date"],
        createdAt=data.get("createdAt"),
        entities=entities,
        timings=timings,
    )


@app.post("/api/playlists/{day}/generate")
def generate_playlist(day: str, overwrite: bool = False, hours: int | None = None):
    """Сгенерировать плейлист на день. hours: только первые N часов (для теста, быстрее)."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format")
    if playlist_exists(d) and not overwrite:
        raise HTTPException(409, "Playlist exists. Use overwrite=true to replace.")
    try:
        data = generate_playlist_for_day(d, max_hours=hours)
        save_playlist(d, data)
        timings = compute_timings(data["entities"])
        return {"date": data["date"], "entitiesCount": len(data["entities"]), "timings": timings}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.put("/api/playlists/{day}/reorder")
def reorder_playlist(day: str, body: dict):
    """Изменить порядок сущностей. body: { "entityIndices": [2, 0, 1, ...] }"""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format")
    data = load_playlist(d)
    if not data:
        raise HTTPException(404, "Playlist not found")
    indices = body.get("entityIndices")
    if not indices or not isinstance(indices, list):
        raise HTTPException(400, "entityIndices required")
    entities = data["entities"]
    if len(indices) != len(entities):
        raise HTTPException(400, "entityIndices length must match entities count")
    new_entities = [entities[i] for i in indices if 0 <= i < len(entities)]
    data["entities"] = new_entities
    save_playlist(d, data)
    return {"ok": True}


@app.put("/api/playlists/{day}")
def update_playlist(day: str, body: dict):
    """Обновить плейлист (полная замена entities)."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format")
    data = load_playlist(d)
    if not data:
        raise HTTPException(404, "Playlist not found")
    if "entities" in body:
        data["entities"] = body["entities"]
    save_playlist(d, data)
    return {"ok": True}


@app.patch("/api/playlists/{day}/entities/{index}")
def update_entity(day: str, index: int, body: EntityUpdate):
    """Обновить сущность (текст)."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format")
    data = load_playlist(d)
    if not data:
        raise HTTPException(404, "Playlist not found")
    entities = data["entities"]
    if index < 0 or index >= len(entities):
        raise HTTPException(404, "Entity not found")
    if body.text is not None:
        entities[index]["text"] = body.text
        # Сбросить audio при изменении текста
        if entities[index].get("type") in [t.value for t in TEXT_ENTITY_TYPES]:
            entities[index]["audio"] = None
            entities[index]["duration"] = 0
    save_playlist(d, data)
    return {"ok": True}


@app.post("/api/playlists/{day}/voice")
def voice_playlist(day: str, body: VoiceRequest = VoiceRequest()):
    """
    Озвучить текстовые сущности.
    body.indices: список индексов для озвучки выбранных; если пусто — озвучить все.
    """
    indices = body.indices if body.indices else None
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "Invalid date format")
    data = load_playlist(d)
    if not data:
        raise HTTPException(404, "Playlist not found")

    from services.tts import text_to_speech

    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entities = data["entities"]
    to_voice = indices if indices is not None else list(range(len(entities)))
    voiced = 0

    for i in to_voice:
        if i < 0 or i >= len(entities):
            continue
        ent = entities[i]
        if ent.get("type") not in [t.value for t in TEXT_ENTITY_TYPES]:
            continue
        text = ent.get("text", "").strip()
        if not text:
            continue
        filename = f"tts_{d.isoformat()}_{i}.mp3"
        out_path = TTS_CACHE_DIR / filename
        try:
            text_to_speech(text, filename=filename, output_dir=TTS_CACHE_DIR)
            try:
                rel_path = str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except ValueError:
                rel_path = str(out_path).replace("\\", "/")
            entities[i]["audio"] = rel_path
            entities[i]["duration"] = _resolve_audio_duration(out_path)
            voiced += 1
        except Exception as e:
            raise HTTPException(500, f"TTS error for entity {i}: {e}")

    save_playlist(d, data)
    timings = compute_timings(data["entities"])
    return {"voiced": voiced, "timings": timings}


@app.post("/api/test-stream")
def test_stream():
    """
    Тестовый стрим: 2 минуты тишины в Icecast.
    Позволяет проверить, что mountpoint появился.
    """
    import threading
    from pathlib import Path
    from config import CACHE_DIR, FFMPEG_PATH
    from services.streamer import enqueue_track, start_continuous_stream

    def _run():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        silence = CACHE_DIR / "silence_8s.mp3"
        if not silence.exists():
            import subprocess
            ffmpeg = FFMPEG_PATH or "ffmpeg"
            subprocess.run(
                [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "8",
                 "-q:a", "9", "-acodec", "libmp3lame", str(silence)],
                capture_output=True,
                timeout=15,
            )
        if start_continuous_stream():
            for _ in range(15):
                enqueue_track(None, silence)

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "message": "Тестовый стрим запущен на 2 мин. Проверьте http://localhost:8000/stream"}


@app.get("/api/jingles")
def list_jingles():
    """Список доступных интро."""
    from config import JINGLES_DIR
    files = []
    if JINGLES_DIR.exists():
        for p in sorted(JINGLES_DIR.glob("*.mp3")):
            rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
            files.append({"name": p.name, "path": rel})
    return {"jingles": files}


@app.get("/api/podcasts")
def list_podcasts():
    """Список доступных подкастов."""
    from config import PODCASTS_DIR, PODCAST_FILES
    files = []
    if PODCASTS_DIR.exists():
        for f in PODCAST_FILES:
            p = PODCASTS_DIR / f
            if p.exists():
                rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
                files.append({"name": p.name, "path": rel})
        for ext in ("*.mp3", "*.mp4"):
            for p in PODCASTS_DIR.glob(ext):
                if p.name not in PODCAST_FILES:
                    rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
                    files.append({"name": p.name, "path": rel})
    return {"podcasts": files}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
