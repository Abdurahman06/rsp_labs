"""HTTP DTOs deliberately separate the JSON contract from database models."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from internal.domain.errors import ErrInvalidInput
from internal.domain.models import Booking, Hotel, Room


@dataclass
class CreateHotelRequest:
    name: str
    city: str
    address: str
    description: str = ""
    rating: Decimal = Decimal("0")

    @classmethod
    def parse(cls, body):
        return cls(body.get("name"), body.get("city"), body.get("address"),
                   body.get("description", ""), body.get("rating", 0))


@dataclass
class CreateBookingRequest:
    user_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date

    @classmethod
    def parse(cls, body):
        try:
            return cls(UUID(body["userId"]), UUID(body["roomId"]),
                       date.fromisoformat(body["checkInDate"]),
                       date.fromisoformat(body["checkOutDate"]))
        except (KeyError, ValueError, TypeError):
            raise ErrInvalidInput("userId, roomId and ISO dates checkInDate/checkOutDate are required") from None


def response_dto(value):
    """Map domain objects to public camelCase DTOs; never expose password_hash."""
    if isinstance(value, list):
        return [response_dto(item) for item in value]
    if isinstance(value, Hotel):
        return {"id": str(value.id), "name": value.name, "city": value.city,
                "address": value.address, "rating": float(value.rating),
                "description": value.description, "createdAt": value.created_at.isoformat() if value.created_at else None}
    if isinstance(value, Room):
        return {"id": str(value.id), "hotelId": str(value.hotel_id), "roomNumber": value.room_number,
                "category": value.category, "pricePerNight": float(value.price_per_night),
                "status": value.status, "capacity": value.capacity}
    if isinstance(value, Booking):
        return {"id": str(value.id), "userId": str(value.user_id), "roomId": str(value.room_id),
                "checkInDate": value.check_in_date.isoformat(), "checkOutDate": value.check_out_date.isoformat(),
                "totalCost": float(value.total_cost), "status": value.status}
    return value
