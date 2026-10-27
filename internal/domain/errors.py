"""Domain failures are independent of SQL drivers and HTTP."""
class DomainError(Exception):
    pass


class ErrNotFound(DomainError):
    pass


class ErrAlreadyExists(DomainError):
    pass


class ErrConflict(DomainError):
    pass


class ErrInvalidInput(DomainError):
    pass


class RepositoryError(DomainError):
    """Unexpected storage failure; original exception is kept as __cause__."""
