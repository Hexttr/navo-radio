@echo off
chcp 65001 >nul
echo NAVO RADIO — запуск
echo.

:: Запуск Icecast (конфиг из папки проекта — без ошибок прав доступа)
echo [1/2] Запуск Icecast...
start "Icecast" /min "C:\Program Files\Icecast\bin\icecast.exe" -c "%~dp0icecast-data\icecast.xml"
timeout /t 3 /nobreak >nul

:: Запуск бэкенда
echo [2/2] Запуск бэкенда...
cd /d "%~dp0backend"
start "NAVO Backend" cmd /c "chcp 65001 >nul && set PYTHONIOENCODING=utf-8 && python main.py"

echo.
echo Готово. Откройте radio.html и нажмите Play.
echo Не закрывайте окна Icecast и Backend.
pause
