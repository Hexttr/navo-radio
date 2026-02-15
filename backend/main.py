"""
NAVO RADIO — точка входа.
Планировщик проверяет время Москвы и определяет, что играть.
"""
import time

from config import FORCE_MUSIC, JINGLES_DIR, JINGLE_FILE, PROJECT_ROOT
from services.level_server import start_level_server
from scheduler import BlockType, get_current_block, get_moscow_now, mark_anchor_played, mark_jingle_played
from services.jingle_block import run_jingle_block
from services.music_block import _ensure_silence_file, run_music_track
from services.news_block import run_news_block
from services.podcast_block import run_podcast_block
from services.streamer import enqueue_track, start_continuous_stream
from services.weather_block import run_weather_block


def run_block(block_type: BlockType, arg: str | None) -> None:
    """Запуск блока."""
    if block_type == BlockType.JINGLE:
        run_jingle_block()
        mark_jingle_played()  # всегда, чтобы не зациклиться при отсутствии файла
    elif block_type == BlockType.NEWS:
        run_news_block()
        mark_anchor_played()  # до конца часа — MUSIC
    elif block_type == BlockType.WEATHER:
        run_weather_block()
        mark_anchor_played()
    elif block_type == BlockType.PODCAST:
        run_podcast_block(arg or "")
        mark_anchor_played()
    elif block_type == BlockType.MUSIC:
        # Цикл треков — проверяем расписание перед каждым треком
        while get_current_block()[0] == BlockType.MUSIC:
            if not run_music_track(intro_enabled=True):
                print("[MUSIC] Не удалось загрузить трек, пауза 30 сек")
                time.sleep(30)


def _warmup_stream(block_type: BlockType) -> None:
    """Быстрый старт: сразу подключаем источник. Для NEWS/WEATHER — 2–3 тишины, т.к. генерация 15–30 сек."""
    # JINGLE и PODCAST — мгновенно, warmup не нужен
    if block_type in (BlockType.JINGLE, BlockType.PODCAST):
        return
    if not start_continuous_stream():
        return
    silence = _ensure_silence_file()
    jingle = JINGLES_DIR / JINGLE_FILE
    if jingle.exists():
        enqueue_track(None, jingle)
    # NEWS/WEATHER: генерация долгая — подкладываем 2 тишины (16 сек) на время fetch+Groq+TTS
    if block_type in (BlockType.NEWS, BlockType.WEATHER) and silence.exists():
        for _ in range(2):
            enqueue_track(None, silence, block=False)
    elif silence.exists():
        enqueue_track(None, silence)


def main() -> None:
    start_level_server()
    print("NAVO RADIO — Backend")
    print(f"Проект: {PROJECT_ROOT}")
    if FORCE_MUSIC:
        print("Режим: FORCE_MUSIC (всегда музыка)")
    else:
        print("Режим: расписание (врезки включены)")
    print("---")

    while True:
        now = get_moscow_now()
        block_type, arg = get_current_block()
        print(f"[{now.strftime('%H:%M:%S')} MSK] {block_type.value}" + (f" ({arg})" if arg else ""))
        _warmup_stream(block_type)
        run_block(block_type, arg)
        if block_type != BlockType.MUSIC:
            # Подложить тишину, чтобы эфир не молчал во время паузы до следующей проверки
            silence = _ensure_silence_file()
            if silence.exists():
                enqueue_track(None, silence, block=False)
            time.sleep(5)


if __name__ == "__main__":
    main()
