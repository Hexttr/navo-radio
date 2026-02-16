@echo off
REM NAVO RADIO — Запуск API админки и Playback Engine
REM Используйте start-all.bat для полного запуска (Icecast + API + Playback).
REM Этот скрипт — только API и Playback (если Icecast уже запущен).

cd /d "%~dp0"

echo Starting API on port 8001...
start "NAVO API" cmd /k "cd /d %~dp0backend && python -m uvicorn api_main:app --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul

echo Starting Playback Engine...
start "NAVO Playback" cmd /k "cd /d %~dp0backend && set PYTHONIOENCODING=utf-8 && python playback_engine.py"

echo.
echo API: http://localhost:8001
echo Admin: http://localhost:3000/admin
pause
