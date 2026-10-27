"""HTTP transport layer: routing, response serialization and status codes."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler


class HealthHandler(BaseHTTPRequestHandler):
    health_service = None

    def do_GET(self) -> None:  # noqa: N802 (required by BaseHTTPRequestHandler)
        if self.path not in ("/health", "/api/v1/health"):
            self._write_json(404, {"error": "not_found", "message": "Endpoint not found"})
            return
        payload = self.health_service.get_status()
        self._write_json(200 if payload["status"] == "ok" else 503, payload)

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        # Keep the sample server quiet unless a caller explicitly logs requests.
        return
