from typing import Generic, TypeVar
from psycopg.rows import dict_row
from internal.domain.errors import ErrNotFound, ErrInvalidInput
from internal.repository.postgres.db import mapped_errors

T = TypeVar("T")


def pagination(limit, offset):
    if type(limit) is not int or type(offset) is not int:
        raise ErrInvalidInput("limit and offset must be integers")
    if limit <= 0 or offset < 0:
        raise ErrInvalidInput("limit must be positive; offset must be nonnegative")
    return min(limit, 100), offset


class PostgresRepository(Generic[T]):
    """Subclasses contain fixed, explicit SQL; no user input forms SQL text."""
    model = None
    insert_fields = ()
    insert_sql = select_sql = list_sql = delete_sql = ""

    def __init__(self, source):
        self.source = source

    def _one(self, query, params) -> T:
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if row is None:
                        raise ErrNotFound("Record not found")
                    return self.model(**row)

    def create(self, entity: T) -> T:
        return self._one(self.insert_sql, tuple(getattr(entity, f) for f in self.insert_fields))

    def get_by_id(self, entity_id) -> T:
        return self._one(self.select_sql, (entity_id,))

    def list(self, limit=20, offset=0) -> list[T]:
        limit, offset = pagination(limit, offset)
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(self.list_sql, (limit, offset))
                    return [self.model(**row) for row in cur.fetchall()]

    def delete(self, entity_id) -> None:
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(self.delete_sql, (entity_id,))
                    if cur.rowcount == 0:
                        raise ErrNotFound("Record not found")
