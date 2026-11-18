"""Fast unit tests: no HTTP listener and no PostgreSQL required."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
import unittest

from internal.domain.errors import ErrConflict, ErrInvalidInput
from internal.domain.models import Room
from internal.service.booking_service import BookingService


class FakeUow:
    def __init__(self, room_status="AVAILABLE", overlap=False):
        self.booking_rows = []
        self.repos = SimpleNamespace(
            rooms=SimpleNamespace(get_for_update=lambda _: Room(
                hotel_id=uuid4(), room_number="101", category="STANDARD",
                price_per_night=Decimal("100"), capacity=2, status=room_status)),
            users=SimpleNamespace(get_by_id=lambda _: object()),
            bookings=SimpleNamespace(
                has_overlap=lambda *args: overlap,
                create=self._create,
                get_by_id=lambda _: self.booking_rows[0],
                update=lambda booking: booking))

    def _create(self, booking):
        booking.id = uuid4()
        self.booking_rows.append(booking)
        return booking

    @contextmanager
    def transaction(self):
        yield self.repos


class BookingServiceTests(unittest.TestCase):
 def test_booking_rejects_past_check_in(self):
    service = BookingService(FakeUow(), clock=lambda: date(2026, 11, 18))
    with self.assertRaisesRegex(ErrInvalidInput, "past"):
        service.book(uuid4(), uuid4(), date(2026, 11, 17), date(2026, 11, 20))


 def test_booking_success_calculates_total_and_persists(self):
    uow = FakeUow()
    service = BookingService(uow, clock=lambda: date(2026, 11, 18))
    result = service.book(uuid4(), uuid4(), date(2026, 11, 20), date(2026, 11, 23))
    assert result.total_cost == Decimal("300")
    assert result.status == "CONFIRMED"
    assert len(uow.booking_rows) == 1


 def test_booking_rejects_occupied_room(self):
    service = BookingService(FakeUow(room_status="MAINTENANCE"), clock=lambda: date(2026, 11, 18))
    with self.assertRaisesRegex(ErrConflict, "not available"):
        service.book(uuid4(), uuid4(), date(2026, 11, 20), date(2026, 11, 22))


if __name__ == "__main__":
    unittest.main()
