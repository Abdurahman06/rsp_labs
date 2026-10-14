"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE pairs without adding a third-party dependency."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    name: str
    version: str
    host: str
    port: int

    @classmethod
    def from_environment(cls, dotenv_path: Path | None = None) -> "Settings":
        if dotenv_path:
            _load_dotenv(dotenv_path)
        try:
            port = int(os.getenv("APP_PORT", "8080"))
        except ValueError as exc:
            raise ValueError("APP_PORT must be an integer") from exc
        if not 1 <= port <= 65535:
            raise ValueError("APP_PORT must be between 1 and 65535")
        return cls(
            name=os.getenv("APP_NAME", "City Hotels Booking API"),
            version=os.getenv("APP_VERSION", "0.1.0"),
            host=os.getenv("APP_HOST", "127.0.0.1"),
            port=port,
        )
