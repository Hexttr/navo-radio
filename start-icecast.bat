@echo off
echo Starting Icecast (config from project folder)...
start "Icecast" "C:\Program Files\Icecast\bin\icecast.exe" -c "%~dp0icecast-data\icecast.xml"
echo Icecast started. Stream: http://localhost:8000/stream
echo Close this window when done.
pause
