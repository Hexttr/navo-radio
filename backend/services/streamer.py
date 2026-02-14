"""
NAVO RADIO — стриминг в Icecast.
FFmpeg: конкатенация аудио (intro + track) и отправка в Icecast.
"""
import subprocess
from pathlib import Path

from config import (
    FFMPEG_PATH,
    ICECAST_HOST,
    ICECAST_MOUNT,
    ICECAST_PASSWORD,
    ICECAST_PORT,
)


def stream_to_icecast(
    intro_path: Path | None,
    track_path: Path,
) -> subprocess.Popen | None:
    """
    Запустить FFmpeg: intro (если есть) + track → Icecast.
    Возвращает процесс. Для бесконечного цикла вызывающий код
    должен управлять процессом и перезапускать с новым контентом.
    """
    if not ICECAST_PASSWORD:
        print("[STREAMER] ICECAST_PASSWORD не задан, стрим не запущен")
        return None

    # Список файлов для конкатенации
    inputs = []
    if intro_path and intro_path.exists():
        inputs.append(str(intro_path))
    inputs.append(str(track_path))

    # FFmpeg: concat demuxer
    # Создаём временный файл-список для concat (пути с / для совместимости)
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in inputs:
            path_str = str(Path(p).resolve()).replace("\\", "/")
            f.write(f"file '{path_str}'\n")
        concat_list = f.name

    icecast_url = (
        f"icecast://source:{ICECAST_PASSWORD}@{ICECAST_HOST}:{ICECAST_PORT}/{ICECAST_MOUNT}"
    )

    ffmpeg_exe = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-loglevel", "warning",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "1",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        icecast_url,
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    # Удаляем concat-файл после того, как FFmpeg его прочитал (в фоне)
    def _cleanup():
        proc.wait()
        Path(concat_list).unlink(missing_ok=True)

    import threading
    threading.Thread(target=_cleanup, daemon=True).start()

    return proc


def check_ffmpeg() -> bool:
    """Проверить, установлен ли FFmpeg."""
    ffmpeg_exe = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"
    try:
        subprocess.run(
            [ffmpeg_exe, "-version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
