"""A real repository/service demo. Run only against an isolated lab6_test_* database."""
from datetime import date
from decimal import Decimal
import json
from internal.config.settings import Settings
from internal.database.postgres import connect
from internal.domain.models import User, Hotel, Room, to_public
from internal.domain.errors import ErrConflict
from internal.repository.postgres.uow import PostgresRepositories, PostgresUnitOfWork
from internal.service.booking_service import BookingService


def main():
    settings = Settings.from_environment()
    if not settings.db_name.startswith("lab6_test_"):
        raise RuntimeError("Demo must use an isolated lab6_test_* database")
    with connect(settings) as pool:
        repos = PostgresRepositories.from_source(pool)
        user = repos.users.create(User(full_name="Demo Guest", email="demo@example.test", password_hash="demo-only-hash"))
        hotel = repos.hotels.create(Hotel(name="Demo Hotel", city="Kazan", address="Demo street"))
        room = repos.rooms.create(Room(hotel_id=hotel.id, room_number="101", category="STANDARD",
                                       price_per_night=Decimal("3000.50"), capacity=2))
        service = BookingService(PostgresUnitOfWork(pool))
        booking = service.book(user.id, room.id, date(2027, 3, 10), date(2027, 3, 12))
        print("CREATED: room 101, two nights at 3000.50 = 6001.00")
        print(json.dumps(to_public(booking), ensure_ascii=False, indent=2))
        try:
            service.book(user.id, room.id, date(2027, 3, 11), date(2027, 3, 13))
        except ErrConflict as exc:
            print("OVERLAP REJECTED: " + str(exc))
        else:
            raise AssertionError("Overlapping booking was incorrectly accepted")
        print("USER JSON (password hash excluded): " + json.dumps(to_public(user), ensure_ascii=False))


if __name__ == "__main__":
    main()
