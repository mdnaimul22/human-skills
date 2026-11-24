import enum
import re

class ErrorClassification(str, enum.Enum):
    CLIENT_ERROR = "client_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    UPSTREAM_DEPENDENCY = "upstream_dependency"
    SYSTEM_ERROR = "system_error"

class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
        error_code: str = "INTERNAL_ERROR",
        classification: ErrorClassification = ErrorClassification.SYSTEM_ERROR,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code
        self.classification = classification

class NotFoundError(AppError):
    def __init__(
        self,
        resource: str,
        identifier: str = "",
        details: dict | None = None,
        error_code: str = "RESOURCE_NOT_FOUND",
        classification: ErrorClassification = ErrorClassification.CLIENT_ERROR,
    ):
        detail = f"'{resource}' not found" + (f": {identifier}" if identifier else "")
        super().__init__(
            detail,
            status_code=404,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class ValidationError(AppError, ValueError):
    def __init__(
        self,
        message: str,
        details: dict | None = None,
        error_code: str = "VALIDATION_ERROR",
        classification: ErrorClassification = ErrorClassification.CLIENT_ERROR,
    ):
        AppError.__init__(
            self,
            message,
            status_code=400,
            details=details,
            error_code=error_code,
            classification=classification,
        )
        ValueError.__init__(self, message)

class ExternalServiceError(AppError):
    def __init__(
        self,
        service: str,
        message: str,
        details: dict | None = None,
        error_code: str = "UPSTREAM_SERVICE_ERROR",
        classification: ErrorClassification = ErrorClassification.UPSTREAM_DEPENDENCY,
    ):
        super().__init__(
            f"{service} error: {message}",
            status_code=502,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class PermissionDeniedError(AppError):
    def __init__(
        self,
        message: str = "Permission denied",
        details: dict | None = None,
        error_code: str = "PERMISSION_DENIED",
        classification: ErrorClassification = ErrorClassification.AUTH_ERROR,
    ):
        super().__init__(
            message,
            status_code=403,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class AuthenticationError(AppError):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict | None = None,
        error_code: str = "AUTHENTICATION_FAILED",
        classification: ErrorClassification = ErrorClassification.AUTH_ERROR,
    ):
        super().__init__(
            message,
            status_code=401,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class ConflictError(AppError):
    def __init__(
        self,
        message: str,
        details: dict | None = None,
        error_code: str = "CONFLICT",
        classification: ErrorClassification = ErrorClassification.CLIENT_ERROR,
    ):
        super().__init__(
            message,
            status_code=409,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class MediaFormatError(AppError):
    def __init__(
        self,
        message: str,
        details: dict | None = None,
        error_code: str = "MEDIA_FORMAT_MISMATCH",
        classification: ErrorClassification = ErrorClassification.CLIENT_ERROR,
    ):
        super().__init__(
            message,
            status_code=422,
            details=details,
            error_code=error_code,
            classification=classification,
        )

class MediaProcessingError(AppError):
    def __init__(
        self,
        message: str,
        details: dict | None = None,
        error_code: str = "MEDIA_PROCESSING_ERROR",
        classification: ErrorClassification = ErrorClassification.SYSTEM_ERROR,
    ):
        super().__init__(
            message,
            status_code=500,
            details=details,
            error_code=error_code,
            classification=classification,
        )


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict | None = None,
        error_code: str = "RATE_LIMIT_EXCEEDED",
        classification: ErrorClassification = ErrorClassification.RATE_LIMIT,
    ):
        d = dict(details) if details else {}
        if retry_after is not None:
            d["retry_after"] = retry_after
        super().__init__(
            message,
            status_code=429,
            details=d,
            error_code=error_code,
            classification=classification,
        )

_PATH_PATTERN = re.compile(
    r"(?<![:/])(?:/home/[^\s\"':;]+|/(?:var|tmp|etc|usr|opt|root|bin|sbin)/[^\s\"':;]+|/(?:[a-zA-Z0-9_\.\-]+/){2,}[^\s\"':;]+|[A-Za-z]:\\[^\s\"':;]+)"
)
_SECRET_PATTERN = re.compile(r"(Bearer\s+)[\"']?[^\s,;\"']+[\"']?", re.IGNORECASE)
_COOKIE_PATTERN = re.compile(r"((?:session|token|auth|cookie|jwt|key|secret)\s*=\s*)[\"']?[^;\s,\"']+[\"']?", re.IGNORECASE)

def mask_sensitive_data(text: str | None) -> str | None:
    if text is None:
        return None
    if not text:
        return ""
    masked = _SECRET_PATTERN.sub(r"\1[MASKED]", text)
    masked = _COOKIE_PATTERN.sub(r"\1[MASKED]", masked)
    masked = _PATH_PATTERN.sub("<path>", masked)
    return masked

def sanitize_client_error(exc: BaseException | str | None) -> str:
    match exc:
        case AppError() if exc.message:
            raw = exc.message
        case BaseException():
            raw = str(exc)
        case str():
            raw = exc
        case _:
            raw = "An unexpected error occurred"

    raw_lower = raw.lower()
    if any(p in raw_lower for p in ["path traversal", "etc/passwd", "..\\", "../"]):
        return "Invalid file path or destination"

    if any(t in raw_lower for t in ["timeout", "timed out"]):
        return "The request timed out. Please try again"

    if any(k in raw_lower for k in ["403", "forbidden", "sabr", "bot", "sign in", "confirm", "login_required", "sorry, you are facing a problem"]):
        return "Video provider temporarily restricted requests. Please try again in a few moments"

    if any(p in raw_lower for p in ["permission", "database", "disk image"]):
        return "Server storage error. Please contact support"

    if any(p in raw_lower for p in ["/home/", "tmp/downloads"]):
        return "Invalid file path or destination"

    cleaned = mask_sensitive_data(raw) or ""
    cleaned = re.sub(r"\byt-dlp\b", "engine", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > 160:
        cleaned = cleaned[:157] + "..."

    return cleaned or "An unexpected error occurred. Please try again"
