"""
NAVO RADIO — схемы сущностей и плейлиста.
"""
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    """Тип сущности в эфире."""
    SONG = "song"
    DJ = "dj"
    PODCAST = "podcast"
    NEWS = "news"
    WEATHER = "weather"
    INTRO = "intro"


# Сущности с текстом (редактируемые, требуют озвучки)
TEXT_ENTITY_TYPES = (EntityType.DJ, EntityType.NEWS, EntityType.WEATHER)

# Сущности с готовым файлом (без текста)
FILE_ENTITY_TYPES = (EntityType.SONG, EntityType.PODCAST, EntityType.INTRO)


def entity_is_ready(entity: dict[str, Any]) -> bool:
    """
    Сущность готова: текст утверждён и есть озвучка (для текстовых),
    или файл существует (для файловых).
    """
    etype = entity.get("type")
    if etype in TEXT_ENTITY_TYPES:
        text = entity.get("text", "").strip()
        audio = entity.get("audio")
        return bool(text and audio)
    if etype in FILE_ENTITY_TYPES:
        return bool(entity.get("file"))
    return False


def entity_has_editable_text(entity: dict[str, Any]) -> bool:
    """Сущность имеет редактируемый текст."""
    return entity.get("type") in TEXT_ENTITY_TYPES


def get_entity_duration_seconds(entity: dict[str, Any]) -> float:
    """Длительность сущности в секундах (0 если неизвестно)."""
    return float(entity.get("duration", 0) or 0)


def compute_timings(entities: list[dict[str, Any]]) -> list[str]:
    """
    Вычислить тайминг для каждой сущности.
    Возвращает список строк вида "00:00", "00:03:45", "01:15:22".
    """
    result: list[str] = []
    total_sec = 0.0
    for ent in entities:
        result.append(_format_duration(total_sec))
        total_sec += get_entity_duration_seconds(ent)
    return result


def _format_duration(seconds: float) -> str:
    """Форматировать секунды в HH:MM:SS или MM:SS."""
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
