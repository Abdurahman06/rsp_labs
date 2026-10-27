from typing import Protocol
from psycopg import Error
from psycopg_pool import ConnectionPool, PoolTimeout, TooManyRequests


class HealthRepository(Protocol):
    def is_available(self) -> bool: ...


class PostgresHealthRepository:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def is_available(self) -> bool:
        try:
            with self.pool.connection(timeout=2) as conn:
                return conn.execute("SELECT 1").fetchone()[0] == 1
        except (Error, PoolTimeout, TooManyRequests):
            return False
