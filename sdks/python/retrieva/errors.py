"""Custom exception classes for the Retrieva SDK."""

from __future__ import annotations

from typing import Any, Dict, Optional


class RetrievaError(Exception):
    """Base exception for all Retrieva SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.body = body or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"status_code={self.status_code!r})"
        )


class AuthenticationError(RetrievaError):
    """Raised when the API key is invalid or missing (HTTP 401/403)."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        status_code: Optional[int] = 401,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class NotFoundError(RetrievaError):
    """Raised when the requested resource is not found (HTTP 404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: Optional[int] = 404,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class ValidationError(RetrievaError):
    """Raised when request validation fails (HTTP 422)."""

    def __init__(
        self,
        message: str = "Validation error",
        status_code: Optional[int] = 422,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class RateLimitError(RetrievaError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: Optional[int] = 429,
        body: Optional[Dict[str, Any]] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message=message, status_code=status_code, body=body)


class ServerError(RetrievaError):
    """Raised when the server returns a 5xx error."""

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: Optional[int] = 500,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class ConnectionError(RetrievaError):
    """Raised when the SDK cannot connect to the API."""

    def __init__(
        self,
        message: str = "Failed to connect to the Retrieva API",
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class TimeoutError(RetrievaError):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)
