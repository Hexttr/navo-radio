@echo off
chcp 65001 >nul
echo NAVO RADIO - Starting...
echo.

echo [1/2] Starting Icecast...
start "Icecast" /min "C:\Program Files\Icecast\bin\icecast.exe" -c "%~dp0icecast-data\icecast.xml"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Backend...
cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
start "NAVO Backend" python main.py

echo.
echo Done. Open radio.html and press Play.
echo Do not close Icecast and Backend windows.
pause
