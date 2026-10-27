from internal.domain.models import Booking
from internal.repository.postgres.base import PostgresRepository


class PostgresBookingRepository(PostgresRepository[Booking]):
    model = Booking
    insert_fields = ("user_id", "room_id", "check_in_date", "check_out_date", "total_cost", "status",)
    insert_sql = """INSERT INTO bookings (user_id, room_id, check_in_date, check_out_date, total_cost, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, room_id, check_in_date, check_out_date, total_cost, status, created_at"""
    select_sql = """SELECT id, user_id, room_id, check_in_date, check_out_date, total_cost, status, created_at
        FROM bookings WHERE id = %s"""
    list_sql = """SELECT id, user_id, room_id, check_in_date, check_out_date, total_cost, status, created_at
        FROM bookings ORDER BY created_at DESC, id LIMIT %s OFFSET %s"""
    delete_sql = "DELETE FROM bookings WHERE id = %s"

    def has_overlap(self, room_id, start, end):
        from internal.repository.postgres.db import mapped_errors
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""SELECT EXISTS (
                        SELECT id FROM bookings
                        WHERE room_id = %s AND status IN ('PENDING', 'CONFIRMED')
                        AND check_in_date < %s AND check_out_date > %s
                    )""", (room_id, end, start))
                    return cur.fetchone()[0]
