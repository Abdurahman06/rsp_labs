from time import monotonic
from internal.config.settings import Settings
from internal.repository.health_repository import HealthRepository


class HealthService:
    def __init__(self, settings: Settings, repository: HealthRepository):
        self.settings = settings
        self.repository = repository
        self.started_at = monotonic()

    def get_status(self) -> dict:
        available = self.repository.is_available()
        return {
            "status": "ok" if available else "unavailable",
            "db": "up" if available else "down",
            "service": self.settings.name,
            "version": self.settings.version,
            "uptime_seconds": round(monotonic() - self.started_at, 3),
        }
