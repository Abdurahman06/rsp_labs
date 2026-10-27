"""Composition root: configuration -> pool -> repository -> service -> HTTP."""
import logging
import signal
import sys
from pathlib import Path
from threading import Event
from http.server import ThreadingHTTPServer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from internal.config.settings import Settings
from internal.database.postgres import connect
from internal.controller.lab6_handler import Lab6Handler
from internal.repository.postgres.uow import PostgresRepositories, PostgresUnitOfWork
from internal.service.catalog_service import CatalogService
from internal.service.booking_service import BookingService
from internal.repository.health_repository import PostgresHealthRepository
from internal.service.health_service import HealthService


def create_server(settings, pool):
    service = HealthService(settings, PostgresHealthRepository(pool))
    repos = PostgresRepositories.from_source(pool)
    catalog = CatalogService(repos.users, repos.hotels, repos.rooms, repos.bookings)
    booking = BookingService(PostgresUnitOfWork(pool))

    class RequestHandler(Lab6Handler):
        health_service = service
        catalog_service = catalog

    server = ThreadingHTTPServer((settings.host, settings.port), RequestHandler)
    server.daemon_threads = False
    server.timeout = 0.5
    server.booking_service = booking
    return server


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    try:
        settings = Settings.from_environment(PROJECT_ROOT / ".env")
        pool = connect(settings, stop)
    except (ValueError, RuntimeError) as exc:
        logging.error("Startup: %s", exc)
        return 1
    try:
        with create_server(settings, pool) as server:
            logging.info("%s listening on %s:%s", settings.name, settings.host, settings.port)
            while not stop.is_set():
                server.handle_request()
    finally:
        pool.close()
        logging.info("HTTP server and database pool closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
