from contextlib import contextmanager
from psycopg import Error
from psycopg_pool import PoolTimeout, TooManyRequests
from internal.domain.errors import (
    ErrAlreadyExists, ErrConflict, ErrInvalidInput, RepositoryError,
)


def translate_error(exc):
    code = getattr(exc, "sqlstate", None)
    if code == "23505":
        return ErrAlreadyExists("A record with this unique value already exists")
    if code == "23503":
        return ErrConflict("Related record is missing or still in use")
    if code in ("23514", "23502", "22P02", "22001", "22003", "22007", "22008"):
        return ErrInvalidInput("Invalid field value")
    return RepositoryError("Database operation failed")


@contextmanager
def mapped_errors():
    try:
        yield
    except (Error, PoolTimeout, TooManyRequests) as exc:
        raise translate_error(exc) from exc


class TransactionConnection:
    """Same connection() contract as a pool; commit belongs to the Unit of Work."""
    def __init__(self, connection):
        self._connection = connection

    @contextmanager
    def connection(self):
        yield self._connection
