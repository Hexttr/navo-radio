@echo off
chcp 65001 >nul
echo NAVO RADIO - Starting (new architecture)...
echo.

echo [1/3] Starting Icecast...
start "Icecast" /min "C:\Program Files\Icecast\bin\icecast.exe" -c "%~dp0icecast-data\icecast.xml"
timeout /t 3 /nobreak >nul

echo [2/3] Starting API (admin) on port 8001...
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
start "NAVO API" cmd /k "cd /d %~dp0backend && python -m uvicorn api_main:app --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul

echo [3/3] Starting Playback Engine...
start "NAVO Playback" cmd /k "cd /d %~dp0backend && set PYTHONIOENCODING=utf-8 && python playback_engine.py"

echo.
echo Done. Open http://localhost:3000/admin to generate broadcast.
echo Playback: http://localhost:3000 (or radio.html)
echo Do not close Icecast, API and Playback windows.
pause
