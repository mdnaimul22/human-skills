"""
Universal Exception Hierarchy
==============================
Base exception classes for any Python project.
All project-specific errors should extend AppError.

Usage:
    from src.helpers.exceptions import AppError, NotFoundError, ValidationError

    raise NotFoundError("User", user_id)
    raise ValidationError("Email format is invalid")
    raise ExternalServiceError("Stripe", "Payment declined")

After scaffolding: rename AppError to your project's name if desired
(e.g., ChainCVError, EpicADBError) — all subclasses inherit automatically.
"""


class AppError(Exception):
    """
    Base exception for all project-specific errors.

    Attributes:
        message:     Human-readable error description.
        status_code: Suggested HTTP status code (used by global error handler).
        details:     Optional dict with structured debug info (never leaked to client).
    """

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str = ""):
        detail = f"'{resource}' not found" + (f": {identifier}" if identifier else "")
        super().__init__(detail, status_code=404)


class ValidationError(AppError):
    """Client input validation failure (400)."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=400, details=details)


class ExternalServiceError(AppError):
    """Third-party or external service failure (502)."""

    def __init__(self, service: str, message: str, details: dict | None = None):
        super().__init__(f"{service} error: {message}", status_code=502, details=details)


class PermissionDeniedError(AppError):
    """Authorization failure (403)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class AuthenticationError(AppError):
    """Authentication failure (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)



class ConflictError(AppError):
    """Duplicate or conflicting resource state (409)."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=409, details=details)


class RateLimitError(AppError):
    """Too many requests (429)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(message, status_code=429, details=details)
