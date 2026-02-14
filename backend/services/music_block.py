"""
NAVO RADIO — музыкальный блок.
Оркестрация: Jamendo → Groq → TTS → Stream.
Предзагрузка следующего трека — минимум паузы между треками.
"""
import threading
from pathlib import Path
from config import CACHE_DIR

from .groq_client import generate_dj_intro
from .jamendo import download_track, get_next_track
from .streamer import stream_to_icecast
from .tts import text_to_speech

# Предзагруженные данные для следующего трека (фоновый поток)
_next_track_data: tuple[Path | None, Path, str] | None = None
_next_lock = threading.Lock()


def _prepare_track_data() -> tuple[Path | None, Path, str] | None:
    """Подготовить intro + track. Возвращает (intro_path, track_path, display_name) или None."""
    try:
        track = get_next_track()
    except Exception as e:
        print(f"[MUSIC] Jamendo ошибка: {e}")
        return None
    if not track:
        return None

    intro_path = None
    try:
        text = generate_dj_intro(
            track_name=track.name,
            artist_name=track.artist_name,
            album_name=track.album_name,
        )
        intro_path = text_to_speech(text, filename=f"intro_{track.id}.mp3")
    except Exception as e:
        print(f"[MUSIC] TTS/Groq ошибка, без интро: {e}")
        try:
            fallback = f"Сейчас в эфире — {track.artist_name} с композицией {track.name}."
            intro_path = text_to_speech(fallback, filename=f"intro_fb_{track.id}.mp3")
        except Exception:
            pass

    try:
        track_path = download_track(track)
    except Exception as e:
        print(f"[MUSIC] Ошибка загрузки трека: {e}")
        return None

    return (intro_path, track_path, f"{track.artist_name} — {track.name}")


def _prepare_next_async() -> None:
    """В фоне подготовить следующий трек."""
    global _next_track_data
    try:
        data = _prepare_track_data()
        with _next_lock:
            _next_track_data = data
    except Exception as e:
        print(f"[MUSIC] Предзагрузка не удалась: {e}")
        with _next_lock:
            _next_track_data = None


def run_music_track(intro_enabled: bool = True) -> bool:
    """
    Воспроизвести один трек с DJ-интро.
    Использует предзагруженные данные, если есть — минимум паузы.
    """
    global _next_track_data

    with _next_lock:
        data = _next_track_data
        _next_track_data = None

    if data is None:
        data = _prepare_track_data()
        if data is None:
            return False

    intro_path, track_path, display_name = data
    safe_name = display_name.encode("ascii", errors="replace").decode("ascii")
    print(f"[MUSIC] {safe_name}")

    # Запускаем предзагрузку следующего в фоне (пока играет текущий)
    t = threading.Thread(target=_prepare_next_async, daemon=True)
    t.start()

    proc = stream_to_icecast(intro_path, track_path)
    if proc:
        proc.wait()
        return True

    print("[MUSIC] Стрим не запущен (нет Icecast)")
    return True
