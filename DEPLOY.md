# NAVO RADIO — развёртывание на Ubuntu

Подробная инструкция для развёртывания приложения на сервере Ubuntu. Подходит для другой копии Cursor или любого разработчика.

---

## Требования

- Ubuntu 22.04 LTS (или 20.04+)
- Python 3.10+
- FFmpeg
- Icecast2
- Доступ к интернету (API: Jamendo, Groq, WeatherAPI)

---

## 1. Подготовка сервера

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg icecast2
```

### Icecast2: настройка при установке

При `apt install icecast2` может появиться диалог:
- **Configure icecast2?** → Yes
- **Run icecast2 as daemon?** → Yes

Или настройка вручную:

```bash
sudo systemctl edit icecast2
# Добавить: Environment="ICECAST_USERNAME=icecast"
sudo systemctl enable icecast2
sudo systemctl start icecast2
```

---

## 2. Клонирование репозитория

```bash
cd /opt  # или /home/youruser
git clone https://github.com/Hexttr/navo-radio.git
cd navo-radio
```

---

## 3. Чувствительные данные (.env)

Файл `.env` **не коммитится** в git (в `.gitignore`). Создайте его вручную на сервере.

### Вариант A: Копирование шаблона

```bash
cd /opt/navo-radio/backend
cp .env.example .env
nano .env   # или vim, заполните значения
```

### Вариант B: Безопасная передача с локальной машины

На **локальной** машине (где есть рабочий .env):

```bash
scp backend/.env user@your-server:/opt/navo-radio/backend/.env
```

Проверьте, что `.env` не попал в git: `git status` не должен показывать `backend/.env`.

### Переменные для заполнения

| Переменная | Где взять | Обязательно |
|------------|-----------|-------------|
| `JAMENDO_CLIENT_ID` | https://devportal.jamendo.com | Да |
| `GROQ_API_KEY` | https://console.groq.com | Да |
| `WEATHER_API_KEY` | https://www.weatherapi.com | Нет (погода будет «временно недоступна») |
| `ICECAST_PASSWORD` | Должен совпадать с `source-password` в icecast.xml | Да |

### Проверка .env

```bash
cd /opt/navo-radio/backend
cat .env | grep -v PASSWORD | grep -v KEY  # показать без секретов
```

---

## 4. Конфигурация Icecast

### Стандартный icecast2 (Debian/Ubuntu)

Конфиг: `/etc/icecast2/icecast.xml`

Отредактируйте пароль источника:

```bash
sudo nano /etc/icecast2/icecast.xml
```

Найдите `<source-password>` и установите тот же пароль, что в `ICECAST_PASSWORD` в `.env`.

### Кастомный Icecast (как в проекте)

Если используете `icecast-data/icecast.xml` из репозитория:

```bash
cd /opt/navo-radio
# Скопировать example и настроить пути
cp icecast-data/icecast.xml.example icecast-data/icecast.xml
nano icecast-data/icecast.xml
```

Замените:
- `ABSOLUTE_PATH_TO_PROJECT` → `/opt/navo-radio`
- `YOUR_PASSWORD` → пароль (тот же, что в .env)
- `basedir`, `webroot`, `adminroot` — пути к Icecast (обычно `/usr/share/icecast2`)

---

## 5. Виртуальное окружение Python

```bash
cd /opt/navo-radio/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 6. Подкасты и джинглы

Создайте директории и положите файлы:

```bash
mkdir -p /opt/navo-radio/podcasts
mkdir -p /opt/navo-radio/jingles
mkdir -p /opt/navo-radio/cache
```

- **podcasts/** — `1.mp3`, `2.mp3`, `3.mp3`, `4.mp3` (по расписанию: 11→1, 16→2, 19→3, 22→4)
- **jingles/** — `jingle.mp3` (короткая заставка, раз в час в :00)

---

## 7. Запуск

### Ручной запуск (проверка)

```bash
cd /opt/navo-radio/backend
source .venv/bin/activate
export PYTHONIOENCODING=utf-8
python main.py
```

Убедитесь, что Icecast запущен:

```bash
sudo systemctl status icecast2
# или, если кастомный: icecast -c /opt/navo-radio/icecast-data/icecast.xml
```

Стрим: `http://localhost:8000/stream` (или `http://your-server-ip:8000/stream`)

---

## 8. Systemd — автозапуск

Создайте unit-файл:

```bash
sudo nano /etc/systemd/system/navo-radio.service
```

Содержимое:

```ini
[Unit]
Description=NAVO RADIO Backend
After=network.target icecast2.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/navo-radio/backend
Environment="PYTHONIOENCODING=utf-8"
Environment="PATH=/opt/navo-radio/backend/.venv/bin:/usr/bin:/bin"
ExecStart=/opt/navo-radio/backend/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable navo-radio
sudo systemctl start navo-radio
sudo systemctl status navo-radio
```

Логи:

```bash
journalctl -u navo-radio -f
```

---

## 9. Файрвол (если нужен внешний доступ)

```bash
sudo ufw allow 8000/tcp   # Icecast
sudo ufw enable
```

---

## 10. Чеклист перед запуском

- [ ] Python 3.10+, FFmpeg, Icecast установлены
- [ ] Репозиторий склонирован
- [ ] `.env` создан и заполнен (JAMENDO, GROQ, ICECAST_PASSWORD)
- [ ] Icecast запущен, пароль в icecast.xml совпадает с .env
- [ ] `podcasts/` и `jingles/` содержат файлы
- [ ] `python main.py` запускается без ошибок
- [ ] Стрим доступен по `http://server:8000/stream`

---

## Безопасность секретов

- **Никогда** не коммитьте `.env` в git
- `.env.example` — только шаблон без реальных ключей
- На сервере: `chmod 600 backend/.env`
- Рекомендуется: хранить секреты в менеджере паролей (1Password, Bitwarden) и вручную переносить при развёртывании

---

## Структура проекта

```
navo-radio/
├── backend/
│   ├── .env          # создать вручную, не в git
│   ├── .env.example  # шаблон
│   ├── main.py
│   ├── config.py
│   ├── scheduler.py
│   ├── requirements.txt
│   └── services/
├── podcasts/         # 1.mp3, 2.mp3, 3.mp3, 4.mp3
├── jingles/          # jingle.mp3
├── cache/            # создаётся автоматически
├── icecast-data/     # конфиг Icecast (если кастомный)
├── online-radio-page/ # веб-плеер (опционально)
├── DEPLOY.md         # эта инструкция
└── BROADCAST_LOGIC.md
```
