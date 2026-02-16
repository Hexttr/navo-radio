"""
NAVO RADIO — тестовый стрим в Icecast.
Стримит тишину 2 минуты для проверки подключения.
Запуск: cd backend && python test_stream.py
"""
import time
from pathlib import Path

from config import CACHE_DIR, FFMPEG_PATH
from services.streamer import enqueue_track, start_continuous_stream


def _ensure_silence() -> Path:
    """Создать 8 сек тишины."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / "silence_8s.mp3"
    if not path.exists():
        ffmpeg = FFMPEG_PATH or "ffmpeg"
        import subprocess
        subprocess.run(
            [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "8",
             "-q:a", "9", "-acodec", "libmp3lame", str(path)],
            capture_output=True,
            timeout=15,
        )
    return path


def main():
    print("NAVO RADIO — тестовый стрим (тишина 2 мин)")
    silence = _ensure_silence()
    if not start_continuous_stream():
        print("Ошибка: не удалось запустить стрим. Проверьте ICECAST_PASSWORD в .env")
        return
    for i in range(15):
        enqueue_track(None, silence)
        print(f"  Добавлено в очередь: {(i+1)*8} сек")
    print("Стрим идёт на http://localhost:8000/stream — проверьте в браузере.")
    print("Ожидание 2 минуты...")
    time.sleep(120)
    print("Готово.")


if __name__ == "__main__":
    main()
