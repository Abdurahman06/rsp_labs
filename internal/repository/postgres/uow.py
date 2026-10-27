from contextlib import contextmanager
from dataclasses import dataclass
from internal.repository.postgres.db import TransactionConnection, mapped_errors
from internal.repository.postgres.user import PostgresUserRepository
from internal.repository.postgres.hotel import PostgresHotelRepository
from internal.repository.postgres.room import PostgresRoomRepository
from internal.repository.postgres.booking import PostgresBookingRepository


@dataclass
class PostgresRepositories:
    users: PostgresUserRepository
    hotels: PostgresHotelRepository
    rooms: PostgresRoomRepository
    bookings: PostgresBookingRepository

    @classmethod
    def from_source(cls, source):
        return cls(PostgresUserRepository(source), PostgresHotelRepository(source),
                   PostgresRoomRepository(source), PostgresBookingRepository(source))


class PostgresUnitOfWork:
    def __init__(self, pool):
        self.pool = pool

    @contextmanager
    def transaction(self):
        with mapped_errors():
            with self.pool.connection() as conn:
                # Explicit transaction commits on success and rolls back on any exception.
                with conn.transaction():
                    yield PostgresRepositories.from_source(TransactionConnection(conn))
