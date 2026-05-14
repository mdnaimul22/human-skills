"""
Tool: CORS Implementation Score
Category: Security

Evaluates Cross-Origin Resource Sharing (CORS) configuration quality.

Sources:
  - Google API Design Guide (security policies)
  - Microsoft REST API Guidelines §CORS
  - GitHub REST API conventions (origin whitelisting)
  - OWASP CORS Cheat Sheet
  - RFC 6454 (Origin), W3C CORS specification

Scoring model (additive, max 1.0):
  0.30 — Explicit origin whitelist (not wildcard *)
  0.25 — Credentials mode handled correctly
  0.20 — Allowed methods restricted (not wildcard *)
  0.15 — Allowed headers declared explicitly
  0.10 — Preflight (OPTIONS) handled

Penalty:
  -1.0 — Wildcard origin (*) + credentials=True → floor to 0.0 (OWASP critical)
  -0.60 — No CORS configuration at all (routes exist but no CORS)
"""
import re
from typing import Any
from helpers.tool import Tool


# ── Detection patterns ─────────────────────────────────────────────────────────

# Explicit origin whitelist (list/set of domain strings, not wildcard)
ORIGIN_WHITELIST = re.compile(
    r'(?:allow_origins|origins|CORS_ALLOWED_ORIGINS|allowedOrigins|AllowedOrigins)\s*[=:]\s*'
    r'\[(?!\s*["\']?\*["\']?\s*\])'   # list that does NOT start with *
    r'|allowedOrigins\s*=\s*\{[^}]*https'   # Spring/Gin set literal
    r'|origins\s*=\s*\{[^}]*https'          # Spring @CrossOrigin origins={...}
    r'|AllowOrigins.*\[.*https',             # Gin AllowOrigins array
    re.IGNORECASE,
)

# Wildcard origin — permissive
WILDCARD_ORIGIN = re.compile(
    r'(?:allow_origins|origins)\s*[=:]\s*\[\s*["\']\*["\']\s*\]'
    r'|Access-Control-Allow-Origin["\']?\s*[=:]\s*["\']\*["\']'
    r'|\bCORS_ALLOW_ALL_ORIGINS\s*=\s*True',
    re.IGNORECASE,
)

# Credentials enabled
CREDENTIALS_ENABLED = re.compile(
    r'(?:allow_credentials|supports_credentials|CORS_ALLOW_CREDENTIALS|allowCredentials)\s*[=:]\s*'
    r'(?:True|true|"true"|true)',
    re.IGNORECASE,
)

# Explicit allowed methods (not wildcard)
METHODS_EXPLICIT = re.compile(
    r'(?:allow_methods|methods|CORS_ALLOW_METHODS|allowedMethods|AllowedMethods)\s*[=:]\s*'
    r'\[(?!\s*["\']?\*)',
    re.IGNORECASE,
)

# Wildcard methods
METHODS_WILDCARD = re.compile(
    r'(?:allow_methods|methods)\s*[=:]\s*\[\s*["\']?\*["\']?\s*\]',
    re.IGNORECASE,
)

# Explicit allowed headers
HEADERS_EXPLICIT = re.compile(
    r'(?:allow_headers|allowedHeaders|CORS_ALLOW_HEADERS|AllowedHeaders)\s*[=:]\s*\[',
    re.IGNORECASE,
)

# Preflight OPTIONS handler
PREFLIGHT_HANDLER = re.compile(
    r'app\.options\s*\(|OPTIONS.*cors|cors.*OPTIONS'
    r'|RequestMethod\.OPTIONS|allowedMethods.*OPTIONS'
    r'|methods.*OPTIONS|OPTIONS.*methods',
    re.IGNORECASE,
)

# CORS middleware / decorator usage (any kind)
CORS_MIDDLEWARE = re.compile(
    r'\b(?:CORSMiddleware|CORS\s*\(|flask_cors|cors\s*\(|'
    r'@CrossOrigin|addCorsMappings|cors\.New\s*\(|'
    r'django.*cors|corsheaders|cors\.Config|'
    r'CORS_ALLOWED_ORIGINS|CORS_ALLOW_ALL_ORIGINS)'
    r'|Access-Control-Allow-Origin',
    re.IGNORECASE,
)

# Route presence
HAS_ROUTES = re.compile(
    r'@(?:app|router|r)\.\s*(?:get|post|put|delete|patch|route)\s*\('
    r'|router\.\s*(?:get|post|put|delete)\s*\(',
    re.IGNORECASE,
)


class CorsImplementation(Tool):
    def __init__(self):
        super().__init__(
            name="cors_implementation",
            description=(
                "Scores CORS configuration quality in REST API code: checks for explicit "
                "origin whitelisting, credential mode handling, method/header restrictions, "
                "preflight handling, and absence of wildcard origins on credentialed endpoints."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        # ── OWASP Critical: wildcard + credentials → instant 0.0 ──────────────
        if WILDCARD_ORIGIN.search(source_code) and CREDENTIALS_ENABLED.search(source_code):
            return 0.0

        has_cors = bool(CORS_MIDDLEWARE.search(source_code))
        has_routes = bool(HAS_ROUTES.search(source_code))

        # No CORS config at all
        if not has_cors:
            return 0.0

        score = 0.0

        # 1. Explicit origin whitelist (0.30)
        if ORIGIN_WHITELIST.search(source_code):
            score += 0.30
        elif WILDCARD_ORIGIN.search(source_code):
            score += 0.05   # Wildcard present — minimal credit only

        # 2. Credentials handled correctly (0.25)
        if CREDENTIALS_ENABLED.search(source_code):
            score += 0.25

        # 3. Explicit methods list (0.20)
        if METHODS_EXPLICIT.search(source_code):
            score += 0.20
        elif not METHODS_WILDCARD.search(source_code):
            score += 0.10   # Not wildcard but not explicit either — partial

        # 4. Explicit allowed headers (0.15)
        if HEADERS_EXPLICIT.search(source_code):
            score += 0.15

        # 5. Preflight OPTIONS handled (0.10)
        if PREFLIGHT_HANDLER.search(source_code):
            score += 0.10

        return round(min(max(score, 0.0), 1.0), 4)
