from datetime import date
from internal.domain.models import Booking
from internal.domain.errors import ErrInvalidInput, ErrConflict
from internal.repository.interfaces import UnitOfWork


class BookingService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def book(self, user_id, room_id, check_in: date, check_out: date) -> Booking:
        if type(check_in) is not date or type(check_out) is not date or check_out <= check_in:
            raise ErrInvalidInput("Check-out must be after check-in")
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
