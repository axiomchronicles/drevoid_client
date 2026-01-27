"""Custom exceptions for Drevoid application."""


class DrevoidException(Exception):
    """Base exception for all Drevoid errors."""

    pass


class ConnectionException(DrevoidException):
    """Raised when connection-related errors occur."""

    pass


class AuthenticationException(DrevoidException):
    """Raised when authentication fails."""

    pass


class RoomException(DrevoidException):
    """Raised when room operations fail."""

    pass


class MessageException(DrevoidException):
    """Raised when message operations fail."""

    pass
