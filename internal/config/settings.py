"""Validated environment configuration; secrets are excluded from repr."""
from dataclasses import dataclass, field
import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if path.is_file():
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def _integer(name: str, default: str, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except ValueError:
        raise ValueError(f"{name} must be an integer") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class Settings:
    name: str
    version: str
    host: str
    port: int
    db_host: str
    db_port: int
    db_user: str
    db_password: str = field(repr=False)
    db_name: str
    db_max_conns: int

    @classmethod
    def from_environment(cls, dotenv_path: Path | None = None) -> "Settings":
        if dotenv_path:
            _load_dotenv(dotenv_path)
        return cls(
            name=os.getenv("APP_NAME", "City Hotels Booking API"),
            version=os.getenv("APP_VERSION", "0.5.0"),
            host=os.getenv("APP_HOST", "127.0.0.1"),
            port=_integer("APP_PORT", "8085", 1, 65535),
            db_host=_required("DB_HOST"),
            db_port=_integer("DB_PORT", "5432", 1, 65535),
            db_user=_required("DB_USER"),
            db_password=_required("DB_PASSWORD"),
            db_name=_required("DB_NAME"),
            db_max_conns=_integer("DB_MAX_CONNS", "10", 1, 100),
        )
