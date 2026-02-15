"""
NAVO RADIO — конфигурация.
Загрузка .env, время Москвы, расписание.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из директории backend
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

# Корень проекта (Radio4)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PODCASTS_DIR = PROJECT_ROOT / "podcasts"
CACHE_DIR = PROJECT_ROOT / "cache"
JINGLES_DIR = PROJECT_ROOT / "jingles"

# Аудиозаставка (короткий mp3, раз в час)
JINGLE_FILE = os.getenv("JINGLE_FILE", "jingle.mp3")

# Часовой пояс расписания
TIMEZONE = os.getenv("TZ", "Europe/Moscow")

# Режим теста: всегда музыка, игнорировать расписание
FORCE_MUSIC = os.getenv("FORCE_MUSIC", "1").lower() in ("1", "true", "yes")

# Расписание (часы по Москве)
NEWS_HOURS = (9, 12, 15, 18, 21)
WEATHER_HOURS = (10, 14, 17, 20)
PODCAST_HOURS = (11, 16, 19, 22)

# Подкасты по кругу: 11→1, 16→2, 19→3, 22→4
PODCAST_FILES = ("1.mp3", "2.mp3", "3.mp3", "4.mp4")

# API
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# FFmpeg (путь к ffmpeg.exe или пусто = из PATH)
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "")

# Icecast
ICECAST_HOST = os.getenv("ICECAST_HOST", "localhost")
ICECAST_PORT = int(os.getenv("ICECAST_PORT", "8000"))
ICECAST_MOUNT = os.getenv("ICECAST_MOUNT", "stream")
ICECAST_PASSWORD = os.getenv("ICECAST_PASSWORD", "")
