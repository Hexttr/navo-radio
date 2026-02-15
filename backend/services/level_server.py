"""
NAVO RADIO — HTTP endpoint для уровня звука (Safari fallback).
Эквалайзер в Safari не получает данные из стрима — используем серверный уровень.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

LEVEL_PORT = 8765


def _get_level():
    from services.streamer import get_audio_level
    return get_audio_level()


class LevelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/level" or self.path == "/level/":
            level = _get_level()
            body = json.dumps({"level": level}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_level_server():
    """Запустить HTTP-сервер в фоновом потоке."""
    server = HTTPServer(("127.0.0.1", LEVEL_PORT), LevelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
