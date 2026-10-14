"""Domain/service layer for the health use case."""

from __future__ import annotations

import time

from internal.config.settings import Settings
from internal.repository.health_repository import RuntimeHealthRepository


class HealthService:
    def __init__(self, settings: Settings, repository: RuntimeHealthRepository) -> None:
        self._settings = settings
        self._repository = repository
        self._started_at = time.monotonic()

    def get_status(self) -> dict:
        """Return service status without exposing transport or database details."""
        return {
            "status": "ok",
            "service": self._settings.name,
            "version": self._settings.version,
            "uptime_seconds": round(time.monotonic() - self._started_at, 3),
            "dependencies": self._repository.check(),
        }
