"""
NAVO RADIO — стриминг в Icecast.
Один долгоживущий FFmpeg читает MP3 из pipe — бесшовная смена треков без 409.
"""
import queue
import subprocess
import threading
from pathlib import Path

from config import (
    FFMPEG_PATH,
    ICECAST_HOST,
    ICECAST_MOUNT,
    ICECAST_PASSWORD,
    ICECAST_PORT,
)

# Очередь: (intro_path | None, track_path). Feeder пишет в FFmpeg stdin.
_stream_queue: queue.Queue[tuple[Path | None, Path] | None] = queue.Queue(maxsize=4)
_feeder_thread: threading.Thread | None = None
_ffmpeg_proc: subprocess.Popen | None = None
_running = False


def _feed_worker() -> None:
    """Поток: читает из очереди, конкатенирует MP3, пишет в FFmpeg stdin."""
    global _ffmpeg_proc
    ffmpeg_exe = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"
    icecast_url = (
        f"icecast://source:{ICECAST_PASSWORD}@{ICECAST_HOST}:{ICECAST_PORT}/{ICECAST_MOUNT}"
    )
    cmd = [
        ffmpeg_exe,
        "-loglevel", "warning",
        "-re",
        "-f", "mp3",
        "-i", "pipe:0",
        "-c:a", "copy",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        icecast_url,
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _ffmpeg_proc = proc
    assert proc.stdin is not None

    def _read_stderr():
        if proc.stderr:
            for line in proc.stderr:
                s = line.decode("utf-8", errors="replace").strip()
                if s:
                    print(f"[FFmpeg] {s}")

    threading.Thread(target=_read_stderr, daemon=True).start()

    try:
        while _running:
            item = _stream_queue.get()
            if item is None:
                break
            intro_path, track_path = item
            files = []
            if intro_path and intro_path.exists():
                files.append(intro_path)
            files.append(track_path)
            for p in files:
                with open(p, "rb") as f:
                    while chunk := f.read(65536):
                        proc.stdin.write(chunk)
            proc.stdin.flush()
    except BrokenPipeError:
        print("[STREAMER] FFmpeg pipe closed (Icecast disconnect?)")
    except Exception as e:
        print(f"[STREAMER] Feeder error: {e}")
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()
        _ffmpeg_proc = None


def start_continuous_stream() -> bool:
    """Запустить непрерывный стрим. Возвращает True если успешно."""
    global _feeder_thread, _running
    if not ICECAST_PASSWORD:
        print("[STREAMER] ICECAST_PASSWORD не задан")
        return False
    if _feeder_thread and _feeder_thread.is_alive():
        return True
    _running = True
    _feeder_thread = threading.Thread(target=_feed_worker, daemon=True)
    _feeder_thread.start()
    return True


def enqueue_track(intro_path: Path | None, track_path: Path) -> bool:
    """Добавить трек в очередь. Блокирует если очередь полна."""
    try:
        _stream_queue.put((intro_path, track_path), timeout=120)
        return True
    except queue.Full:
        print("[STREAMER] Queue full, drop")
        return False


def stream_to_icecast(
    intro_path: Path | None,
    track_path: Path,
) -> subprocess.Popen | None:
    """
    Режим совместимости: если непрерывный стрим запущен — добавляет в очередь.
    Иначе — fallback на старый способ (отдельный FFmpeg на трек).
    """
    if _running and _feeder_thread and _feeder_thread.is_alive():
        enqueue_track(intro_path, track_path)
        # Возвращаем фейковый процесс, который "ждёт" пока трек отыграет
        # Для run_music_track нужен proc.wait() — но мы не ждём, трек в очереди
        class _FakeProc:
            returncode = 0
            def wait(self): pass
        return _FakeProc()  # type: ignore

    # Fallback: один раз на трек (для обратной совместимости)
    return _stream_single(intro_path, track_path)


def _stream_single(intro_path: Path | None, track_path: Path) -> subprocess.Popen | None:
    """Один FFmpeg на трек (legacy)."""
    if not ICECAST_PASSWORD:
        return None
    inputs = []
    if intro_path and intro_path.exists():
        inputs.append(str(intro_path))
    inputs.append(str(track_path))

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
        ffmpeg_exe, "-y", "-loglevel", "warning",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "1",
        "-content_type", "audio/mpeg", "-f", "mp3", icecast_url,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def _cleanup():
        proc.wait()
        Path(concat_list).unlink(missing_ok=True)

    threading.Thread(target=_cleanup, daemon=True).start()
    return proc


def check_ffmpeg() -> bool:
    ffmpeg_exe = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"
    try:
        subprocess.run([ffmpeg_exe, "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
