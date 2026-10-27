"""Integration tests: real PostgreSQL, exclusively in a newly created test database."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from decimal import Decimal
from threading import Barrier, Thread
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import HTTPError
from uuid import uuid4
import json
import unittest

from internal.config.settings import Settings
from internal.database.postgres import connect
from internal.domain.models import User, Hotel, Room, Booking, to_public
from internal.domain.errors import ErrNotFound, ErrAlreadyExists, ErrConflict, ErrInvalidInput, RepositoryError
from internal.repository.postgres.uow import PostgresRepositories, PostgresUnitOfWork
from internal.service.booking_service import BookingService
from internal.service.catalog_service import CatalogService
from internal.controller.lab6_handler import Lab6Handler


class RepositoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = Settings.from_environment()
        if not settings.db_name.startswith("lab6_test_"):
            raise RuntimeError("Integration tests require an isolated lab6_test_* database")
        cls.pool = connect(settings)
        cls.repos = PostgresRepositories.from_source(cls.pool)
        cls.uow = PostgresUnitOfWork(cls.pool)
        cls.service = BookingService(cls.uow)

    @classmethod
    def tearDownClass(cls):
        cls.pool.close()

    def setUp(self):
        # Safe only because setUpClass enforces the dedicated test database name.
        with self.pool.connection() as conn:
            conn.execute("TRUNCATE reviews, bookings, rooms, hotels, users")
        self.user = self.repos.users.create(User(full_name="Test Guest", email="guest@example.test",
                                                 password_hash="test-hash-not-a-real-password"))
        self.hotel = self.repos.hotels.create(Hotel(name="Central", city="Kazan", address="Test street 1"))
        self.room = self.repos.rooms.create(Room(hotel_id=self.hotel.id, room_number="101",
                                                category="STANDARD", price_per_night=Decimal("3000.50"), capacity=2))

    def booking(self, **kw):
        return Booking(user_id=self.user.id, room_id=self.room.id,
                       check_in_date=date(2027, 1, 10), check_out_date=date(2027, 1, 12),
                       total_cost=Decimal("6001.00"), **kw)

    def test_create_and_read_all_four_entities(self):
        booking = self.repos.bookings.create(self.booking())
        for repo, entity in [(self.repos.users, self.user), (self.repos.hotels, self.hotel),
                             (self.repos.rooms, self.room), (self.repos.bookings, booking)]:
            with self.subTest(entity=type(entity).__name__):
                self.assertIsNotNone(entity.id)
                self.assertIsNotNone(entity.created_at)
                self.assertIsNotNone(entity.created_at.tzinfo)
                self.assertEqual(repo.get_by_id(entity.id), entity)

    def test_database_generates_identity_and_timestamp(self):
        original = User(full_name="New", email="new@example.test", password_hash="hash")
        self.assertIsNone(original.id)
        self.assertIsNone(original.created_at)
        saved = self.repos.users.create(original)
        self.assertIsNotNone(saved.id)
        self.assertIsNotNone(saved.created_at)

    def test_missing_read_for_all_repositories(self):
        for repo in (self.repos.users, self.repos.hotels, self.repos.rooms, self.repos.bookings):
            with self.assertRaises(ErrNotFound):
                repo.get_by_id(uuid4())

    def test_duplicate_email_and_room_number(self):
        with self.assertRaises(ErrAlreadyExists) as caught:
            self.repos.users.create(replace(self.user, id=None))
        self.assertEqual(caught.exception.__cause__.sqlstate, "23505")
        with self.assertRaises(ErrAlreadyExists):
            self.repos.rooms.create(replace(self.room, id=None))
        # An error must not poison a connection returned to the pool.
        self.assertEqual(self.repos.users.get_by_email(self.user.email).id, self.user.id)

    def test_pagination_for_all_repositories(self):
        for i in range(4):
            self.repos.users.create(User(full_name=f"Guest {i}", email=f"guest{i}@example.test", password_hash="hash"))
            self.repos.hotels.create(Hotel(name=f"Hotel {i}", city="Kazan", address=f"Street {i}"))
            self.repos.rooms.create(replace(self.room, id=None, room_number=str(200+i)))
            self.repos.bookings.create(self.booking(status="CANCELED"))
        for repo in (self.repos.users, self.repos.hotels, self.repos.rooms, self.repos.bookings):
            first = repo.list(2, 0)
            second = repo.list(2, 2)
            self.assertEqual(len(first), 2)
            self.assertEqual(len(second), 2)
            self.assertFalse({x.id for x in first} & {x.id for x in second})
            self.assertEqual(first, repo.list(2, 0))

    def test_pagination_upper_limit_and_invalid_arguments(self):
        for i in range(105):
            self.repos.hotels.create(Hotel(name=str(i), city="Test", address=str(i)))
        self.assertEqual(len(self.repos.hotels.list(1000)), 100)
        for limit, offset in [(0, 0), (-1, 0), (1, -1), ("1", 0)]:
            with self.assertRaises(ErrInvalidInput):
                self.repos.hotels.list(limit, offset)

    def test_delete_and_subsequent_read_for_all_entities(self):
        booking = self.repos.bookings.create(self.booking())
        for repo, entity in [(self.repos.bookings, booking), (self.repos.rooms, self.room),
                             (self.repos.hotels, self.hotel), (self.repos.users, self.user)]:
            repo.delete(entity.id)
            with self.assertRaises(ErrNotFound):
                repo.get_by_id(entity.id)
            with self.assertRaises(ErrNotFound):
                repo.delete(entity.id)

    def test_sql_injection_is_literal_email(self):
        for email in ["' OR '1'='1", "'; DROP TABLE users; --"]:
            with self.assertRaises(ErrNotFound):
                self.repos.users.get_by_email(email)
        self.assertEqual(len(self.repos.users.list()), 1)
        self.assertEqual(self.repos.users.get_by_email(self.user.email).id, self.user.id)

    def test_room_update_and_missing_update(self):
        updated = self.repos.rooms.update(replace(self.room, capacity=4, price_per_night=Decimal("4100.99")))
        self.assertEqual(self.repos.rooms.get_by_id(self.room.id), updated)
        self.assertEqual(updated.capacity, 4)
        with self.assertRaises(ErrNotFound):
            self.repos.rooms.update(replace(self.room, id=uuid4()))

    def test_foreign_key_errors_and_delete_restrict(self):
        with self.assertRaises(ErrConflict):
            self.repos.rooms.create(replace(self.room, hotel_id=uuid4()))
        self.repos.bookings.create(self.booking())
        with self.assertRaises(ErrConflict):
            self.repos.rooms.delete(self.room.id)
        with self.assertRaises(ErrConflict):
            self.repos.users.delete(self.user.id)
        with self.assertRaises(ErrConflict):
            self.repos.hotels.delete(self.hotel.id)

    def test_check_null_and_invalid_uuid_mapping(self):
        with self.assertRaises(ErrInvalidInput):
            self.repos.rooms.create(replace(self.room, room_number="102", price_per_night=Decimal("-1")))
        with self.assertRaises(ErrInvalidInput):
            self.repos.users.create(replace(self.user, full_name=None, email="null@example.test"))
        for repo in (self.repos.users, self.repos.hotels, self.repos.rooms, self.repos.bookings):
            with self.assertRaises(ErrInvalidInput):
                repo.get_by_id("not-a-uuid")

    def test_decimal_exactness_and_private_json(self):
        self.assertEqual(self.repos.rooms.get_by_id(self.room.id).price_per_night, Decimal("3000.50"))
        public = json.dumps(to_public(self.user))
        self.assertNotIn("password_hash", public)
        self.assertNotIn(self.user.password_hash, public)
        self.assertNotIn(self.user.password_hash, repr(self.user))

    def test_transaction_commit_and_overlap_rejected(self):
        saved = self.service.book(self.user.id, self.room.id, date(2027, 1, 10), date(2027, 1, 12))
        self.assertEqual(saved.total_cost, Decimal("6001.00"))
        with self.assertRaises(ErrConflict):
            self.service.book(self.user.id, self.room.id, date(2027, 1, 11), date(2027, 1, 13))
        self.assertEqual(len(self.repos.bookings.list()), 1)

    def test_adjacent_dates_and_canceled_booking(self):
        self.repos.bookings.create(self.booking(status="CANCELED"))
        self.service.book(self.user.id, self.room.id, date(2027, 1, 10), date(2027, 1, 12))
        self.service.book(self.user.id, self.room.id, date(2027, 1, 12), date(2027, 1, 13))
        self.assertEqual(len(self.repos.bookings.list()), 3)

    def test_concurrent_overlapping_bookings_only_one_succeeds(self):
        barrier = Barrier(2)
        def attempt():
            barrier.wait(timeout=5)
            try:
                self.service.book(self.user.id, self.room.id, date(2027, 2, 10), date(2027, 2, 12))
                return "created"
            except ErrConflict:
                return "conflict"
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ["created", "conflict"])
        self.assertEqual(len(self.repos.bookings.list()), 1)

    def test_transaction_rolls_back_all_changes(self):
        with self.assertRaises(RuntimeError):
            with self.uow.transaction() as tx:
                tx.users.create(User(full_name="Rollback", email="rollback@example.test", password_hash="hash"))
                tx.bookings.create(self.booking())
                raise RuntimeError("Simulated failure after inserts")
        with self.assertRaises(ErrNotFound):
            self.repos.users.get_by_email("rollback@example.test")
        self.assertEqual(self.repos.bookings.list(), [])

    def test_invalid_dates_and_unavailable_room(self):
        with self.assertRaises(ErrInvalidInput):
            self.service.book(self.user.id, self.room.id, date(2027, 1, 12), date(2027, 1, 10))
        self.repos.rooms.update(replace(self.room, status="MAINTENANCE"))
        with self.assertRaises(ErrConflict):
            self.service.book(self.user.id, self.room.id, date(2027, 1, 10), date(2027, 1, 12))

    def test_unexpected_db_error_preserves_cause(self):
        from internal.repository.postgres.db import mapped_errors
        with self.assertRaises(RepositoryError) as caught:
            with mapped_errors():
                with self.pool.connection() as conn:
                    conn.execute("SELECT 1 / 0")
        self.assertEqual(caught.exception.__cause__.sqlstate, "22012")

    def test_http_demo_maps_data_and_domain_errors(self):
        catalog = CatalogService(self.repos.users, self.repos.hotels, self.repos.rooms, self.repos.bookings)
        class Handler(Lab6Handler):
            catalog_service = catalog
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            root = f"http://127.0.0.1:{server.server_port}"
            with urlopen(root + "/lab6/hotels?limit=1") as response:
                self.assertEqual(json.load(response)[0]["name"], "Central")
            for path, code in [("/lab6/rooms/invalid", 400),
                               ("/lab6/hotels/" + str(uuid4()), 404),
                               ("/lab6/hotels?limit=0", 400)]:
                with self.assertRaises(HTTPError) as caught:
                    urlopen(root + path)
                self.assertEqual(caught.exception.code, code)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main(verbosity=2)
