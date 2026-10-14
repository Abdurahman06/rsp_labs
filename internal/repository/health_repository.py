"""Data-access adapter used by the health use case.

The real PostgreSQL/Redis adapters will be added in later iterations. Keeping
the dependency behind this class prevents the service layer from knowing how
the infrastructure is implemented.
"""

from __future__ import annotations

from internal.config.settings import Settings


class RuntimeHealthRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check(self) -> dict[str, str]:
        """Return checks available in the minimal, dependency-free skeleton."""
        return {"application": "ok"}
