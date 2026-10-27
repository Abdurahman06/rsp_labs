"""A bounded connection pool with startup retries and query timeouts."""
import logging
from threading import Event
from psycopg import Error
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool, PoolTimeout
from internal.config.settings import Settings

LOG = logging.getLogger(__name__)


def connect(settings: Settings, stop: Event | None = None, attempts: int = 10) -> ConnectionPool:
    stop = stop or Event()
    dsn = make_conninfo(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, dbname=settings.db_name,
        connect_timeout=2, sslmode="disable",
        options="-c statement_timeout=2000 -c lock_timeout=1500",
    )
    for attempt in range(1, attempts + 1):
        if stop.is_set():
            raise RuntimeError("Database startup cancelled")
        pool = ConnectionPool(
            dsn, min_size=1, max_size=settings.db_max_conns, open=False,
            timeout=2, max_waiting=100, max_lifetime=1800, max_idle=300,
            reconnect_timeout=30, check=ConnectionPool.check_connection,
        )
        try:
            pool.open(wait=True, timeout=3)
            with pool.connection() as conn:
                conn.execute("SELECT 1").fetchone()
            LOG.info("Connected to PostgreSQL at %s:%s (max connections=%s)",
                     settings.db_host, settings.db_port, settings.db_max_conns)
            return pool
        except (Error, PoolTimeout):
            pool.close()
            LOG.warning("Database connection attempt %s/%s failed", attempt, attempts)
            if attempt < attempts:
                stop.wait(min(attempt, 5))
    raise RuntimeError(f"Database unavailable after {attempts} attempts")
