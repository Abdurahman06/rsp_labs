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
