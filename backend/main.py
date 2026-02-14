"""
NAVO RADIO — точка входа.
Планировщик проверяет время Москвы и определяет, что играть.
"""
import time

from config import FORCE_MUSIC, PODCASTS_DIR, PROJECT_ROOT
from scheduler import BlockType, get_current_block, get_moscow_now
from services.music_block import run_music_track


def run_block(block_type: BlockType, arg: str | None) -> None:
    """Запуск блока."""
    if block_type == BlockType.NEWS:
        print("[NEWS] Выпуск новостей (Этап 3)")
    elif block_type == BlockType.WEATHER:
        print("[WEATHER] Прогноз погоды (Этап 3)")
    elif block_type == BlockType.PODCAST:
        path = PODCASTS_DIR / (arg or "")
        if path.exists():
            print(f"[PODCAST] {arg}")
        else:
            print(f"[PODCAST] Файл не найден: {path}")
    elif block_type == BlockType.MUSIC:
        # Непрерывный цикл треков — поток не прерывается между треками
        while get_current_block()[0] == BlockType.MUSIC:
            run_music_track(intro_enabled=True)


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
