from internal.domain.models import Hotel
from internal.repository.postgres.base import PostgresRepository


class PostgresHotelRepository(PostgresRepository[Hotel]):
    model = Hotel
    insert_fields = ("name", "city", "address", "rating", "description",)
    insert_sql = """INSERT INTO hotels (name, city, address, rating, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, city, address, rating, description, created_at"""
    select_sql = """SELECT id, name, city, address, rating, description, created_at
        FROM hotels WHERE id = %s"""
    list_sql = """SELECT id, name, city, address, rating, description, created_at
        FROM hotels ORDER BY created_at DESC, id LIMIT %s OFFSET %s"""
    delete_sql = "DELETE FROM hotels WHERE id = %s"

    def update(self, hotel):
        from psycopg.rows import dict_row
        from internal.domain.errors import ErrNotFound
        from internal.repository.postgres.db import mapped_errors
        with mapped_errors():
            with self.source.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""UPDATE hotels SET name=%s, city=%s, address=%s,
                        rating=%s, description=%s WHERE id=%s
                        RETURNING id, name, city, address, rating, description, created_at""",
                        (hotel.name, hotel.city, hotel.address, hotel.rating,
                         hotel.description, hotel.id))
                    if cur.rowcount == 0:
                        raise ErrNotFound("Hotel not found")
                    return Hotel(**cur.fetchone())
