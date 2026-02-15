"""
NAVO RADIO — точка входа.
Планировщик проверяет время Москвы и определяет, что играть.
"""
import time

from config import FORCE_MUSIC, PROJECT_ROOT
from scheduler import BlockType, get_current_block, get_moscow_now, mark_jingle_played
from services.jingle_block import run_jingle_block
from services.music_block import run_music_track
from services.news_block import run_news_block
from services.podcast_block import run_podcast_block
from services.weather_block import run_weather_block


def run_block(block_type: BlockType, arg: str | None) -> None:
    """Запуск блока."""
    if block_type == BlockType.JINGLE:
        run_jingle_block()
        mark_jingle_played()  # всегда, чтобы не зациклиться при отсутствии файла
    elif block_type == BlockType.NEWS:
        run_news_block()
        while get_current_block()[0] == BlockType.NEWS:
            time.sleep(60)
    elif block_type == BlockType.WEATHER:
        run_weather_block()
        while get_current_block()[0] == BlockType.WEATHER:
            time.sleep(60)
    elif block_type == BlockType.PODCAST:
        run_podcast_block(arg or "")
        while get_current_block()[0] == BlockType.PODCAST:
            time.sleep(60)
    elif block_type == BlockType.MUSIC:
        # Цикл треков — проверяем расписание перед каждым треком
        while get_current_block()[0] == BlockType.MUSIC:
            if not run_music_track(intro_enabled=True):
                print("[MUSIC] Не удалось загрузить трек, пауза 30 сек")
                time.sleep(30)


def main() -> None:
    print("NAVO RADIO — Backend")
    print(f"Проект: {PROJECT_ROOT}")
    if FORCE_MUSIC:
        print("Режим: FORCE_MUSIC (всегда музыка)")
    print("---")

    while True:
        now = get_moscow_now()
        block_type, arg = get_current_block()
        print(f"[{now.strftime('%H:%M:%S')} MSK] {block_type.value}" + (f" ({arg})" if arg else ""))
        run_block(block_type, arg)
        if block_type != BlockType.MUSIC:
            time.sleep(10)


if __name__ == "__main__":
    main()
