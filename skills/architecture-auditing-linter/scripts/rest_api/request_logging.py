"""
Tool: Structured Request Logging Score
Category: Observability

Evaluates whether API request/response lifecycle is properly logged.

Sources:
  - Google API Design Guide (AIP-0151: observability, request IDs)
  - Microsoft REST API Guidelines (request-id, correlation ID)
  - GitHub REST API conventions (X-GitHub-Request-Id header)
  - OpenTelemetry specification (trace context propagation)
  - OWASP Logging Cheat Sheet

Scoring model (additive, max 1.0):
  0.25 — Request ID / correlation ID generated and propagated
  0.25 — Structured logger (not print) with method + path + status
  0.20 — Latency / response time logged
  0.15 — X-Request-ID or X-Correlation-ID header returned to client
  0.10 — Middleware/before+after_request lifecycle hooks present
  0.05 — MDC / structured fields (JSON format or key=value pairs)

Penalty:
  -0.30 — print() used for request logging (OWASP violation)
  -1.00 — Sensitive fields (password/token/secret) appear in log lines → 0.0
"""
import re
from typing import Any
from helpers.tool import Tool


# ── Detection patterns ─────────────────────────────────────────────────────────

# Request ID / Correlation ID generation or propagation
REQUEST_ID = re.compile(
    r'\b(?:request_id|requestId|correlation_id|correlationId|'
    r'X-Request-ID|X-Correlation-ID|X-GitHub-Request-Id|'
    r'uuid\.uuid4|uuid\.New\(\)|UUID\.randomUUID)',
    re.IGNORECASE,
)

# Structured logger usage (not print)
STRUCTURED_LOGGER = re.compile(
    r'\b(?:logger\.\w+|log\.\w+|logging\.\w+|'
    r'LoggerFactory\.getLogger|log\.With|'
    r'winston\.\w+|pino\.\w+|bunyan\.\w+)\s*\(',
    re.IGNORECASE,
)

# Method + path logged
METHOD_PATH_LOGGED = re.compile(
    r'(?:method|path|url|uri|request\.method|req\.method|'
    r'c\.Request\.Method|request\.getMethod)',
    re.IGNORECASE,
)

# Status code logged
STATUS_LOGGED = re.compile(
    r'(?:status_code|status|statusCode|response\.status|'
    r'c\.Writer\.Status|response\.getStatus)',
    re.IGNORECASE,
)

# Latency / response time
LATENCY_LOGGED = re.compile(
    r'\b(?:latency|latency_ms|response.?time|elapsed|duration|'
    r'time\.time\(\)|System\.currentTimeMillis|time\.Now\(\)|'
    r'time\.Since|perf_hooks)',
    re.IGNORECASE,
)

# X-Request-ID returned in response header
REQUEST_ID_HEADER_RETURNED = re.compile(
    r'(?:response\.headers|res\.setHeader|response\.addHeader|'
    r'c\.Header|response\[)\s*[\["\(]*'
    r'(?:X-Request-ID|X-Correlation-ID|X-GitHub-Request-Id)',
    re.IGNORECASE,
)

# Middleware / lifecycle hooks
MIDDLEWARE_HOOK = re.compile(
    r'@app\.middleware|@app\.before_request|@app\.after_request|'
    r'app\.use\s*\(|OncePerRequestFilter|doFilter|'
    r'class.*Middleware|def __call__\s*\(self.*request',
    re.IGNORECASE,
)

# Structured field format (JSON keys or key=value)
STRUCTURED_FIELDS = re.compile(
    r'json\.dumps\s*\(\s*\{|log\.WithFields|MDC\.put|'
    r'key=value|%s.*%s.*%s|f["\'].*=.*=',
    re.IGNORECASE,
)

# print() used for logging — anti-pattern
PRINT_LOGGING = re.compile(
    r'\bprint\s*\([^)]*(?:method|path|status|request|response)',
    re.IGNORECASE,
)

# Sensitive data in logs — OWASP critical
SENSITIVE_IN_LOG = re.compile(
    r'(?:logger\.\w+|log\.\w+|print)\s*\([^)]*'
    r'(?:password|passwd|secret|token|Authorization|api_key)',
    re.IGNORECASE,
)

# morgan structured logging (Node.js)
MORGAN = re.compile(r'\bmorgan\b', re.IGNORECASE)


class RequestLogging(Tool):
    def __init__(self):
        super().__init__(
            name="request_logging",
            description=(
                "Scores structured request logging quality: checks for request ID propagation, "
                "HTTP method/path/status/latency logging, X-Request-ID header, and "
                "structured log format. Penalises print() and sensitive data in logs."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        # ── OWASP Critical: sensitive data in log lines → instant 0.0 ─────────
        if SENSITIVE_IN_LOG.search(source_code):
            return 0.0, ["CRITICAL: Sensitive data (password, token, secret) detected in log statements! This is a severe OWASP violation."]

        score = 0.0
        suggestions = []

        # 1. Request ID / correlation ID (0.25)
        if REQUEST_ID.search(source_code):
            score += 0.25
        else:
            suggestions.append("Generate and log a unique Request ID (Correlation ID) for every incoming request to trace issues.")

        # 2. Structured logger + method/path/status (0.25)
        has_logger = bool(STRUCTURED_LOGGER.search(source_code) or MORGAN.search(source_code))
        has_method_path = bool(METHOD_PATH_LOGGED.search(source_code))
        has_status = bool(STATUS_LOGGED.search(source_code))

        if has_logger and has_method_path and has_status:
            score += 0.25
        elif has_logger and (has_method_path or has_status):
            score += 0.15
            suggestions.append("Ensure your logger captures both the HTTP method/path and the response status code.")
        elif has_logger:
            score += 0.05
            suggestions.append("Log the HTTP method, path, and status code for each request.")
        else:
            suggestions.append("Use a structured logging library (e.g., standard logging, winston, morgan) instead of basic prints.")

        # 3. Latency logged (0.20)
        if LATENCY_LOGGED.search(source_code):
            score += 0.20
        else:
            suggestions.append("Measure and log the request latency/duration to monitor performance.")

        # 4. X-Request-ID returned to client (0.15)
        if REQUEST_ID_HEADER_RETURNED.search(source_code):
            score += 0.15
        else:
            suggestions.append("Return the X-Request-ID in the HTTP response headers so clients can report it when facing errors.")

        # 5. Middleware / lifecycle hooks (0.10)
        if MIDDLEWARE_HOOK.search(source_code):
            score += 0.10
        else:
            suggestions.append("Use global middleware or lifecycle hooks (e.g. @app.before_request) to centralize request logging.")

        # 6. Structured format (0.05)
        if STRUCTURED_FIELDS.search(source_code):
            score += 0.05

        # Penalty: print() used for logging
        if PRINT_LOGGING.search(source_code):
            score = max(score - 0.30, 0.0)
            suggestions.append("CRITICAL: Do not use print() for logging requests. Use a proper logging framework with severity levels.")

        return round(min(max(score, 0.0), 1.0), 4), suggestions
