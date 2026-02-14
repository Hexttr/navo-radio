# Где задать пароль Icecast

Файл конфигурации:
```
C:\Program Files\Icecast\icecast.xml
```

Откройте в блокноте и найдите секцию `<authentication>`:

```xml
<authentication>
    <!-- Пароль для источника (FFmpeg, наш бэкенд) -->
    <source-password>hackme</source-password>
    
    <!-- Пароль для админ-панели (http://localhost:8000/admin) -->
    <admin-user>admin</admin-user>
    <admin-password>hackme</admin-password>
</authentication>
```

**Важно:** после изменения пароля:
1. Сохраните `icecast.xml`
2. Скопируйте новый `source-password` в `backend/.env` → `ICECAST_PASSWORD=...`
3. Перезапустите Icecast
4. Перезапустите бэкенд (`python main.py`)
