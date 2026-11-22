import re

_STANDARD_METHODS: frozenset[str] = frozenset({
    "GET", "POST", "PUT", "DELETE",
    "PATCH", "HEAD", "OPTIONS"
})

_SQL_RE = re.compile(
    r"\b(union|select|insert|delete|update|drop|alter|create|exec|execute)\b|"
    r"(\'|\"|`).*?(or|and).*?=.*?\2|--|/\*|\*/|#|\b(sql|mysql|postgres|oracle|mssql)\b",
    re.IGNORECASE,
)
_XSS_RE = re.compile(
    r"<[^>]*(script|iframe|object|embed|onerror|onload|onclick)|"
    r"javascript:|data:text/html|eval\s*\(|expression\s*\(",
    re.IGNORECASE,
)
_CMD_RE = re.compile(
    r"[;&|`]\s*(ls|cat|pwd|whoami|id|uname|wget|curl)|"
    r"\$\{|\$\(|`.*?`",
    re.IGNORECASE,
)
_TRAVERSAL_RE = re.compile(r"\.\./|\.\.\\|/etc/passwd|/proc/self|/windows/system32", re.IGNORECASE)
_EXEC_PATH_RE = re.compile(r"\.(php|jsp|asp|aspx|sh|bat|exe|cgi)$", re.IGNORECASE)
_URL_ENCODED_RE = re.compile(r"%[0-9a-fA-F]{2}")
_HEX_ENCODED_RE = re.compile(r"\\x[0-9a-fA-F]{2}")

_SUSPICIOUS_HEADER_NAMES: frozenset[str] = frozenset({
    "x-original-url", "x-rewrite-url",
    "proxy-authorization", "x-forwarded-host"
})

class AnomalyScorer:
    def __init__(self, threshold: float = 50.0) -> None:
        self.threshold = threshold

    def score(
        self,
        method: str,
        path: str,
        query: str,
        headers: dict[str, str],
    ) -> tuple[float, dict[str, float], bool]:
        score = 0.0
        indicators: dict[str, float] = {}
        combined = f"{method} {path} {query}"

        if method.upper() not in _STANDARD_METHODS:
            score += 20.0
            indicators["unusual_method"] = 20.0

        if _SQL_RE.search(combined):
            score += 30.0
            indicators["sql_indicator"] = 30.0

        if _XSS_RE.search(combined):
            score += 25.0
            indicators["xss_indicator"] = 25.0

        if _CMD_RE.search(combined):
            score += 35.0
            indicators["cmd_indicator"] = 35.0

        if _TRAVERSAL_RE.search(combined):
            score += 40.0
            indicators["traversal_indicator"] = 40.0

        if _EXEC_PATH_RE.search(path):
            score += 25.0
            indicators["executable_path"] = 25.0

        for h in headers:
            if h.lower() in _SUSPICIOUS_HEADER_NAMES:
                score += 15.0
                indicators["suspicious_header"] = 15.0
                break

        enc_count = len(_URL_ENCODED_RE.findall(combined)) + len(_HEX_ENCODED_RE.findall(combined))
        if enc_count > 0:
            score += 10.0
            indicators["encoded_payload"] = 10.0
        if enc_count > 2:
            score += 15.0
            indicators["multiple_encoding"] = 15.0

        final_score = min(score, 100.0)
        return final_score, indicators, final_score >= self.threshold
