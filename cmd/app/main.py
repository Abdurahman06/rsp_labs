"""Application entry point for the City Hotels Booking API."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python cmd/app/main.py` as well as `python -m cmd.app.main`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from internal.config.settings import Settings  # noqa: E402
from internal.controller.health_handler import HealthHandler  # noqa: E402
from internal.repository.health_repository import RuntimeHealthRepository  # noqa: E402
from internal.service.health_service import HealthService  # noqa: E402


def create_server(settings: Settings):
    """Build the HTTP server and wire the layers together."""
    from http.server import ThreadingHTTPServer

    repository = RuntimeHealthRepository(settings)
    service = HealthService(settings, repository)

    class RequestHandler(HealthHandler):
        health_service = service

    return ThreadingHTTPServer((settings.host, settings.port), RequestHandler)


def main() -> None:
    settings = Settings.from_environment(PROJECT_ROOT / ".env")
    server = create_server(settings)
    print(f"{settings.name} listening on http://{settings.host}:{settings.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
