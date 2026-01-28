"""Custom exceptions for the Tonie Cloud API."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requests import Response


class TonieAPIError(Exception):
    """Base exception for Tonie API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Response | None = None,
    ) -> None:
        """Initialize TonieAPIError.

        Args:
            message: Error message.
            status_code: HTTP status code.
            response: Original response object.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(TonieAPIError):
    """Raised when authentication fails (401/403)."""


class NotFoundError(TonieAPIError):
    """Raised when a resource is not found (404)."""


class RateLimitError(TonieAPIError):
    """Raised when rate limit is exceeded (429)."""


class ValidationError(TonieAPIError):
    """Raised when request validation fails (400)."""


class ServerError(TonieAPIError):
    """Raised when server error occurs (5xx)."""
