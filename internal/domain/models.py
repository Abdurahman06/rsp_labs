from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(kw_only=True)
class Entity:
    id: UUID | None = None
    created_at: datetime | None = None


@dataclass(kw_only=True)
class User(Entity):
    full_name: str
    email: str
    password_hash: str = field(repr=False, metadata={"private": True})
    role: str = "GUEST"
    phone: str | None = None


@dataclass(kw_only=True)
class Hotel(Entity):
    name: str
    city: str
    address: str
    rating: Decimal = Decimal("0")
    description: str = ""


@dataclass(kw_only=True)
class Room(Entity):
    hotel_id: UUID
    room_number: str
    category: str
    price_per_night: Decimal
    capacity: int
    status: str = "AVAILABLE"


@dataclass(kw_only=True)
class Booking(Entity):
    user_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    total_cost: Decimal
    status: str = "CONFIRMED"


@dataclass(kw_only=True)
class Review(Entity):
    user_id: UUID
    hotel_id: UUID
    rating: int
    comment: str = ""


def to_public(value):
    """The only JSON DTO converter: never serializes private dataclass fields."""
    if is_dataclass(value):
        return {f.name: to_public(getattr(value, f.name))
                for f in fields(value) if not f.metadata.get("private")}
    if isinstance(value, (list, tuple)):
        return [to_public(item) for item in value]
    if isinstance(value, dict):
        return {key: to_public(item) for key, item in value.items()}
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
