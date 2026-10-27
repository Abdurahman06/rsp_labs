from internal.domain.models import User
from internal.repository.postgres.base import PostgresRepository


class PostgresUserRepository(PostgresRepository[User]):
    model = User
    insert_fields = ("role", "full_name", "email", "phone", "password_hash",)
    insert_sql = """INSERT INTO users (role, full_name, email, phone, password_hash)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, role, full_name, email, phone, password_hash, created_at"""
    select_sql = """SELECT id, role, full_name, email, phone, password_hash, created_at
        FROM users WHERE id = %s"""
    list_sql = """SELECT id, role, full_name, email, phone, password_hash, created_at
        FROM users ORDER BY created_at DESC, id LIMIT %s OFFSET %s"""
    delete_sql = "DELETE FROM users WHERE id = %s"

    def get_by_email(self, email):
        return self._one("""SELECT id, role, full_name, email, phone, password_hash, created_at
            FROM users WHERE email = %s""", (email,))
