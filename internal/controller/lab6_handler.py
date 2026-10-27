"""Read-only demonstration routes for the Repository lab, separate from the future API."""
from urllib.parse import urlsplit, parse_qs
from internal.controller.health_handler import HealthHandler
from internal.domain.models import to_public
from internal.domain.errors import (
    ErrNotFound, ErrAlreadyExists, ErrConflict, ErrInvalidInput, RepositoryError,
)


class Lab6Handler(HealthHandler):
    catalog_service = None

    def do_GET(self):
        path = urlsplit(self.path).path
        if not path.startswith("/lab6/"):
            return super().do_GET()
        try:
            parts = path.strip("/").split("/")
            if parts == ["lab6", "hotels"]:
                params = parse_qs(urlsplit(self.path).query)
                try:
                    limit = int(params.get("limit", ["20"])[0])
                    offset = int(params.get("offset", ["0"])[0])
                except ValueError:
                    raise ErrInvalidInput("limit and offset must be integers") from None
                result = self.catalog_service.list_hotels(limit, offset)
            elif len(parts) == 3 and parts[1] == "hotels":
                result = self.catalog_service.get_hotel(parts[2])
            elif len(parts) == 3 and parts[1] == "rooms":
                result = self.catalog_service.get_room(parts[2])
            else:
                raise ErrNotFound("Endpoint not found")
            self._write_json(200, to_public(result))
        except ErrNotFound as exc:
            self._write_json(404, {"error": "not_found", "message": str(exc)})
        except (ErrAlreadyExists, ErrConflict) as exc:
            self._write_json(409, {"error": "conflict", "message": str(exc)})
        except ErrInvalidInput as exc:
            self._write_json(400, {"error": "invalid_input", "message": str(exc)})
        except RepositoryError:
            self._write_json(500, {"error": "internal_error", "message": "Database operation failed"})
