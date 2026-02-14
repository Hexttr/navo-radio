"""
NAVO RADIO — музыкальный блок.
Оркестрация: Jamendo → Groq → TTS → Stream.
"""
from pathlib import Path

from config import CACHE_DIR

from .groq_client import generate_dj_intro
from .jamendo import download_track, get_next_track
from .streamer import stream_to_icecast
from .tts import text_to_speech


def run_music_track(intro_enabled: bool = True) -> bool:
    """
    Воспроизвести один трек с DJ-интро.
    Возвращает True при успехе, False при ошибке.
    """
    track = get_next_track()
    if not track:
        print("[MUSIC] Не удалось получить трек из Jamendo")
        return False

    print(f"[MUSIC] {track.artist_name} — {track.name}")

    intro_path = None
    if intro_enabled:
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
        track_path = download_track(track)
    except Exception as e:
        print(f"[MUSIC] Ошибка загрузки трека: {e}")
        return False

    proc = stream_to_icecast(intro_path, track_path)
    if proc:
        proc.wait()
        return True

    # Fallback: просто логируем, стрим не настроен
    print("[MUSIC] Стрим не запущен (нет Icecast)")
    return True
