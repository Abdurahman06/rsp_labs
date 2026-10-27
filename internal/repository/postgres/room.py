from internal.domain.models import Room
from internal.repository.postgres.base import PostgresRepository


class PostgresRoomRepository(PostgresRepository[Room]):
    model = Room
    insert_fields = ("hotel_id", "room_number", "category", "price_per_night", "status", "capacity",)
    insert_sql = """INSERT INTO rooms (hotel_id, room_number, category, price_per_night, status, capacity)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, hotel_id, room_number, category, price_per_night, status, capacity, created_at"""
    select_sql = """SELECT id, hotel_id, room_number, category, price_per_night, status, capacity, created_at
        FROM rooms WHERE id = %s"""
    list_sql = """SELECT id, hotel_id, room_number, category, price_per_night, status, capacity, created_at
        FROM rooms ORDER BY created_at DESC, id LIMIT %s OFFSET %s"""
    delete_sql = "DELETE FROM rooms WHERE id = %s"

    def update(self, room):
        from psycopg.rows import dict_row
        from internal.domain.errors import ErrNotFound
        from internal.repository.postgres.db import mapped_errors
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""UPDATE rooms SET hotel_id=%s, room_number=%s, category=%s,
                        price_per_night=%s, status=%s, capacity=%s WHERE id=%s
                        RETURNING id, hotel_id, room_number, category, price_per_night, status, capacity, created_at""",
                        tuple(getattr(room, f) for f in self.insert_fields) + (room.id,))
                    if cur.rowcount == 0:
                        raise ErrNotFound("Room not found")
                    return Room(**cur.fetchone())

    def get_for_update(self, room_id):
        # Only meaningful when the repository is bound to a Unit of Work transaction.
        return self._one("""SELECT id, hotel_id, room_number, category, price_per_night, status, capacity, created_at
            FROM rooms WHERE id = %s FOR UPDATE""", (room_id,))
