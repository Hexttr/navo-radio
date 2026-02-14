# NAVO RADIO

Онлайн-радио: восточная музыка (Таджикистан), DJ-интро, новости, погода, подкасты.

## Быстрый старт

1. **Установить**: Python 3.10+, FFmpeg, Icecast
2. **Скопировать конфиг**: `cp backend/.env.example backend/.env` — заполнить API ключи
3. **Icecast**: скопировать `icecast-data/icecast.xml.example` → `icecast-data/icecast.xml`, указать пароль и пути
4. **Запуск**: `start-all.bat` (или вручную: Icecast → `python backend/main.py`)
5. **Открыть**: `online-radio-page/public/radio.html`

## Структура

- `backend/` — Python: Jamendo, Groq, TTS, стриминг в Icecast
- `online-radio-page/` — фронтенд (HTML/React)
- `podcasts/` — подкасты 1.mp3, 2.mp3, 3.mp3, 4.mp4
- `icecast-data/` — конфиг Icecast (логи, пароли)

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md)
