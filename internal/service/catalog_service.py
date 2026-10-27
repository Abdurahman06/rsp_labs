from internal.repository.interfaces import UserRepository, HotelRepository, RoomRepository, BookingRepository


class CatalogService:
    def __init__(self, users: UserRepository, hotels: HotelRepository,
                 rooms: RoomRepository, bookings: BookingRepository):
        self.users, self.hotels = users, hotels
        self.rooms, self.bookings = rooms, bookings

    def list_hotels(self, limit=20, offset=0):
        return self.hotels.list(limit, offset)

    def get_hotel(self, hotel_id):
        return self.hotels.get_by_id(hotel_id)

    def get_room(self, room_id):
        return self.rooms.get_by_id(room_id)
