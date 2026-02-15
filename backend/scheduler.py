"""
NAVO RADIO — планировщик.
Определяет, что играть в текущий момент по московскому времени.
"""
from datetime import datetime
from enum import Enum

import pytz

from config import (
    FORCE_MUSIC,
    NEWS_HOURS,
    PODCAST_FILES,
    PODCAST_HOURS,
    TIMEZONE,
    WEATHER_HOURS,
)


class BlockType(str, Enum):
    """Тип контента для эфира."""
    JINGLE = "jingle"
    NEWS = "news"
    WEATHER = "weather"
    PODCAST = "podcast"
    MUSIC = "music"


def get_moscow_now() -> datetime:
    """Текущее время по Москве."""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


_jingle_played_hour: int | None = None


def mark_jingle_played() -> None:
    """Вызвать после проигрывания заставки — не повторять в этом часу."""
    global _jingle_played_hour
    _jingle_played_hour = get_moscow_now().hour


def get_current_block() -> tuple[BlockType, str | None]:
    """
    Возвращает (тип блока, дополнительный аргумент).
    JINGLE — в :00 каждого часа (один раз).
    Для podcast — имя файла подкаста.
    """
    global _jingle_played_hour
    if FORCE_MUSIC:
        return BlockType.MUSIC, None

    now = get_moscow_now()
    hour = now.hour
    minute = now.minute

    # Аудиозаставка — раз в час в :00 (не повторять в том же часу)
    if minute == 0 and _jingle_played_hour != hour:
        return BlockType.JINGLE, None

    if hour in NEWS_HOURS:
        return BlockType.NEWS, None

    if hour in WEATHER_HOURS:
        return BlockType.WEATHER, None

    if hour in PODCAST_HOURS:
        idx = PODCAST_HOURS.index(hour)
        filename = PODCAST_FILES[idx]
        return BlockType.PODCAST, filename

    return BlockType.MUSIC, None
