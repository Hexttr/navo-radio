"""
NAVO RADIO — Playback Engine.
В 00:00 МСК загружает плейлист на день и стримит сущности в Icecast.
"""
import threading
import time
from datetime import date, datetime
from pathlib import Path

import pytz

from config import PROJECT_ROOT, TIMEZONE
from playlist_store import load_playlist
from services.streamer import enqueue_track, start_continuous_stream


def _resolve_entity_path(entity: dict) -> Path | None:
    """Получить абсолютный путь к аудиофайлу сущности."""
    audio = entity.get("audio")
    file_path = entity.get("file")
    path_str = audio or file_path
    if not path_str:
        return None
    return PROJECT_ROOT / path_str.replace("\\", "/")


def _get_entity_duration(entity: dict) -> float:
    """Длительность в секундах."""
    return float(entity.get("duration", 0) or 0)


def run_playlist(day: date) -> None:
    """
    Проиграть плейлист на день.
    Читает сущности по порядку, для каждой с аудио — enqueue в streamer.
    """
    data = load_playlist(day)
    if not data:
        print(f"[PLAYBACK] Плейлист на {day} не найден")
        return

    entities = data.get("entities", [])
    if not entities:
        print(f"[PLAYBACK] Плейлист пуст")
        return

    if not start_continuous_stream():
        print("[PLAYBACK] Не удалось запустить стрим")
        return

    for i, ent in enumerate(entities):
        etype = ent.get("type", "")
        path = _resolve_entity_path(ent)

        if path and path.exists():
            # Один файл: intro, song, podcast, news, weather, dj
            enqueue_track(None, path)
            dur = _get_entity_duration(ent)
            name = ent.get("name", ent.get("artist", "")) or etype
            print(f"[PLAYBACK] [{i+1}/{len(entities)}] {etype}: {name[:50]}")
        else:
            # Нет файла — пропускаем (неозвученный текст)
            print(f"[PLAYBACK] [{i+1}/{len(entities)}] {etype}: пропуск (нет файла)")


def get_moscow_now() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def main() -> None:
    """Основной цикл: в 00:00 МСК загружаем плейлист и стримим."""
    print("NAVO RADIO — Playback Engine")
    print("Ожидание 00:00 МСК для старта эфира...")
    print("---")

    last_day: date | None = None

    while True:
        now = get_moscow_now()
        today = now.date()

        # В полночь — загрузить плейлист на сегодня
        if last_day != today:
            if now.hour == 0 and now.minute < 2:
                print(f"[{now.strftime('%H:%M:%S')} MSK] Загрузка плейлиста на {today}")
                t = threading.Thread(target=run_playlist, args=(today,), daemon=True)
                t.start()
                last_day = today
            elif last_day is None:
                # Первый запуск — сразу запустить плейлист на сегодня (если есть)
                data = load_playlist(today)
                if data:
                    print(f"[{now.strftime('%H:%M:%S')} MSK] Запуск плейлиста на {today}")
                    t = threading.Thread(target=run_playlist, args=(today,), daemon=True)
                    t.start()
                    last_day = today

        time.sleep(60)  # Проверять каждую минуту


if __name__ == "__main__":
    main()
