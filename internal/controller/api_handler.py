"""Thin HTTP adapter: JSON/DTO parsing, service calls and one error-to-HTTP mapping."""
import json
from urllib.parse import urlsplit, parse_qs

from internal.controller.lab6_handler import Lab6Handler
from internal.domain.errors import (ErrNotFound, ErrAlreadyExists, ErrConflict,
                                    ErrInvalidInput, RepositoryError)
from internal.controller.dto import CreateBookingRequest, CreateHotelRequest, response_dto


def error_response(handler, error):
    if isinstance(error, ErrNotFound):
        status, code = 404, "not_found"
    elif isinstance(error, (ErrAlreadyExists, ErrConflict)):
        status, code = 409, "conflict"
    elif isinstance(error, (ErrInvalidInput, ValueError, TypeError, json.JSONDecodeError)):
        status, code = 400, "invalid_input"
    elif isinstance(error, RepositoryError):
        status, code = 500, "internal_error"
        handler._write_json(status, {"code": code, "message": "Database operation failed"})
        return
    else:
        status, code = 500, "internal_error"
        handler._write_json(status, {"code": code, "message": "Internal server error"})
        return
    handler._write_json(status, {"code": code, "message": str(error)})


class ApiHandler(Lab6Handler):
    hotel_service = None
    booking_service = None

    def _body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1024 * 1024:
                raise ErrInvalidInput("A JSON body up to 1 MB is required")
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict):
                raise ErrInvalidInput("JSON body must be an object")
            return value
        except (ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, ErrInvalidInput):
                raise
            raise ErrInvalidInput("Malformed JSON") from None

    def _run(self, callback):
        try:
            callback()
        except Exception as exc:
            error_response(self, exc)

    def _create(self, payload, location):
        self._write_json(201, response_dto(payload), headers={"Location": location})

    def do_GET(self):
        path = urlsplit(self.path).path
        if not path.startswith("/api/v1/"):
            return super().do_GET()
        def run():
            parts = path.strip("/").split("/")
            if parts == ["api", "v1", "hotels"]:
                q = parse_qs(urlsplit(self.path).query)
                limit, offset = int(q.get("limit", ["20"])[0]), int(q.get("offset", ["0"])[0])
                self._write_json(200, response_dto(self.hotel_service.list(limit, offset)))
            elif len(parts) == 4 and parts[:3] == ["api", "v1", "hotels"]:
                self._write_json(200, response_dto(self.hotel_service.get(parts[3])))
            elif len(parts) == 4 and parts[:3] == ["api", "v1", "bookings"]:
                self._write_json(200, response_dto(self.booking_service.get(parts[3])))
            else:
                raise ErrNotFound("Endpoint not found")
        self._run(run)

    def do_POST(self):
        path = urlsplit(self.path).path
        if not path.startswith("/api/v1/"):
            return super().do_POST() if hasattr(super(), "do_POST") else self._write_json(404, {"code":"not_found","message":"Endpoint not found"})
        def run():
            parts, data = path.strip("/").split("/"), self._body()
            if parts == ["api", "v1", "hotels"]:
                hotel = self.hotel_service.create(CreateHotelRequest.parse(data))
                self._create(hotel, f"/api/v1/hotels/{hotel.id}")
            elif parts == ["api", "v1", "bookings"]:
                request = CreateBookingRequest.parse(data)
                booking = self.booking_service.book(request.user_id, request.room_id,
                                                    request.check_in_date, request.check_out_date)
                self._create(booking, f"/api/v1/bookings/{booking.id}")
            elif len(parts) == 5 and parts[:3] == ["api", "v1", "bookings"] and parts[4] == "cancel":
                self._write_json(200, response_dto(self.booking_service.cancel(parts[3])))
            else:
                raise ErrNotFound("Endpoint not found")
        self._run(run)

    def do_PUT(self):
        parts = urlsplit(self.path).path.strip("/").split("/")
        if len(parts) != 4 or parts[:3] != ["api", "v1", "hotels"]:
            return error_response(self, ErrNotFound("Endpoint not found"))
        def run():
            data = self._body()
            required = {"name", "city", "address"}
            if not required.issubset(data):
                raise ErrInvalidInput("PUT requires name, city and address")
            self._write_json(200, response_dto(self.hotel_service.update(parts[3], data)))
        self._run(run)

    def do_DELETE(self):
        parts = urlsplit(self.path).path.strip("/").split("/")
        if len(parts) != 4 or parts[:3] != ["api", "v1", "hotels"]:
            return error_response(self, ErrNotFound("Endpoint not found"))
        def run():
            self.hotel_service.delete(parts[3])
            self.send_response(204)
            self.end_headers()
        self._run(run)
