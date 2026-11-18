from datetime import date, datetime, timezone
from internal.domain.models import Booking
from internal.domain.errors import ErrInvalidInput, ErrConflict
from internal.repository.interfaces import UnitOfWork


class BookingService:
    def __init__(self, uow: UnitOfWork, clock=lambda: datetime.now(timezone.utc).date()):
        self.uow, self.clock = uow, clock

    def book(self, user_id, room_id, check_in: date, check_out: date) -> Booking:
        if type(check_in) is not date or type(check_out) is not date or check_out <= check_in:
            raise ErrInvalidInput("Check-out must be after check-in")
        if check_in < self.clock():
            raise ErrInvalidInput("Check-in cannot be in the past")
        if not user_id or not room_id:
            raise ErrInvalidInput("userId and roomId are required")
        with self.uow.transaction() as repos:
            # All bookings for this room use the same lock, including simultaneous requests.
            room = repos.rooms.get_for_update(room_id)
            repos.users.get_by_id(user_id)
            if room.status != "AVAILABLE":
                raise ErrConflict("Room is not available for booking")
            if repos.bookings.has_overlap(room_id, check_in, check_out):
                raise ErrConflict("Room is already booked for these dates")
            booking = repos.bookings.create(Booking(
                user_id=user_id, room_id=room_id,
                check_in_date=check_in, check_out_date=check_out,
                total_cost=room.price_per_night * (check_out - check_in).days,
            ))
        return booking

    def get(self, booking_id):
        with self.uow.transaction() as repos:
            return repos.bookings.get_by_id(booking_id)

    def cancel(self, booking_id):
        with self.uow.transaction() as repos:
            booking = repos.bookings.get_by_id(booking_id)
            if booking.status == "CANCELED":
                raise ErrConflict("Booking is already canceled")
            booking.status = "CANCELED"
            return repos.bookings.update(booking)
