"""Contracts only. This module does not import psycopg or PostgreSQL code."""
from contextlib import AbstractContextManager
from datetime import date
from typing import Protocol, TypeVar
from uuid import UUID
from internal.domain.models import User, Hotel, Room, Booking

T = TypeVar("T")


class Repository(Protocol[T]):
    def create(self, entity: T) -> T: ...
    def get_by_id(self, entity_id: UUID | str) -> T: ...
    def list(self, limit: int = 20, offset: int = 0) -> list[T]: ...
    def delete(self, entity_id: UUID | str) -> None: ...


class UserRepository(Repository[User], Protocol):
    def get_by_email(self, email: str) -> User: ...


class HotelRepository(Repository[Hotel], Protocol):
    pass


class RoomRepository(Repository[Room], Protocol):
    def update(self, room: Room) -> Room: ...
    def get_for_update(self, room_id: UUID | str) -> Room: ...


class BookingRepository(Repository[Booking], Protocol):
    def has_overlap(self, room_id: UUID | str, start: date, end: date) -> bool: ...


class Repositories(Protocol):
    users: UserRepository
    hotels: HotelRepository
    rooms: RoomRepository
    bookings: BookingRepository


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractContextManager[Repositories]: ...
