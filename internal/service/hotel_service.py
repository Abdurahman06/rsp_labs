from decimal import Decimal, InvalidOperation

from internal.domain.errors import ErrInvalidInput
from internal.domain.models import Hotel


class HotelService:
    """Hotel business operations. The repository is injected by the composition root."""
    def __init__(self, hotels):
        self.hotels = hotels

    @staticmethod
    def _validate(name, city, address, rating, description):
        if not all(isinstance(v, str) and v.strip() for v in (name, city, address)):
            raise ErrInvalidInput("name, city and address are required")
        if len(name) > 200 or len(city) > 100 or len(address) > 300:
            raise ErrInvalidInput("Hotel field is too long")
        try:
            rating = Decimal(str(rating))
        except (InvalidOperation, ValueError):
            raise ErrInvalidInput("rating must be a number") from None
        if not rating.is_finite() or rating < 0 or rating > 5:
            raise ErrInvalidInput("rating must be between 0 and 5")
        if not isinstance(description, str):
            raise ErrInvalidInput("description must be a string")
        return rating

    def create(self, data):
        rating = self._validate(data.name, data.city, data.address, data.rating, data.description)
        return self.hotels.create(Hotel(name=data.name.strip(), city=data.city.strip(),
                                        address=data.address.strip(), rating=rating,
                                        description=data.description))

    def get(self, hotel_id):
        return self.hotels.get_by_id(hotel_id)

    def list(self, limit=20, offset=0):
        if not 1 <= limit <= 100 or offset < 0:
            raise ErrInvalidInput("limit must be 1..100 and offset must be >= 0")
        return self.hotels.list(limit, offset)

    def update(self, hotel_id, data):
        old = self.get(hotel_id)
        name = data.get("name", old.name)
        city = data.get("city", old.city)
        address = data.get("address", old.address)
        rating = data.get("rating", old.rating)
        description = data.get("description", old.description)
        rating = self._validate(name, city, address, rating, description)
        old.name, old.city, old.address = name.strip(), city.strip(), address.strip()
        old.rating, old.description = rating, description
        return self.hotels.update(old)

    def delete(self, hotel_id):
        self.get(hotel_id)
        self.hotels.delete(hotel_id)
