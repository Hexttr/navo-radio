@echo off
REM NAVO RADIO — Старая версия (real-time scheduler без админки)
REM Используйте start-all.bat для новой архитектуры с админкой.

chcp 65001 >nul
echo NAVO RADIO - Legacy (real-time)...
echo.

echo [1/2] Starting Icecast...
start "Icecast" /min "C:\Program Files\Icecast\bin\icecast.exe" -c "%~dp0icecast-data\icecast.xml"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Backend (main.py)...
cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
start "NAVO Backend" python main.py

echo.
echo Done. Open radio.html and press Play.
pause
