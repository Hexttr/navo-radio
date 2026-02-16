# NAVO RADIO

Онлайн-радио: восточная музыка (Таджикистан), DJ-интро, новости, погода, подкасты.

## Быстрый старт (новая архитектура с админкой)

1. **Установить**: Python 3.10+, FFmpeg, Icecast, Node.js
2. **Конфиг**: `backend/.env` — заполнить `JAMENDO_CLIENT_ID`, `GROQ_API_KEY`, `ICECAST_PASSWORD`
3. **Запуск**: `start-all.bat` — Icecast + API + Playback
4. **Фронтенд** (отдельный терминал): `cd online-radio-page && npm run dev`
5. **Админка**: http://localhost:3000/admin — сгенерировать эфир на день
6. **Плеер**: http://localhost:3000 или `radio.html`

## Структура

- `backend/` — Python: Jamendo, Groq, TTS, стриминг в Icecast
- `online-radio-page/` — фронтенд (HTML/React)
- `podcasts/` — подкасты 1.mp3, 2.mp3, 3.mp3, 4.mp4
- `jingles/` — аудиозаставка jingle.mp3 (раз в час)
- `icecast-data/` — конфиг Icecast (логи, пароли)

## Расписание (FORCE_MUSIC=0)

- **:00** — заставка
- **9, 12, 15, 18, 21** — новости
- **10, 14, 17, 20** — погода
- **11, 16, 19, 22** — подкасты
- Остальное — музыка

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md)
