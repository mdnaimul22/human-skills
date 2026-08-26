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
    r'|Access-Control-Allow-Origin["\']?\s*(?:[=:]|,)\s*["\']\*["\']'
    r'|\bCORS_ALLOW_ALL_ORIGINS\s*=\s*True',
    re.IGNORECASE,
)

# Credentials enabled
CREDENTIALS_ENABLED = re.compile(
    r'(?:allow_credentials|supports_credentials|CORS_ALLOW_CREDENTIALS|allowCredentials|credentials)\s*[=:]\s*'
    r'(?:True|true|"true"|true)',
    re.IGNORECASE,
)

# Explicit allowed methods (not wildcard)
METHODS_EXPLICIT = re.compile(
    r'(?:allow_methods|methods|CORS_ALLOW_METHODS|allowedMethods|AllowedMethods|AllowMethods)\s*[=:]\s*'
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
    r'(?:allow_headers|allowedHeaders|CORS_ALLOW_HEADERS|AllowedHeaders|AllowHeaders)\s*[=:]\s*\[',
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
    r'CrossOrigin|addCorsMappings|cors\.New\s*\(|'
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

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        # If no CORS middleware or header usage at all, score is 0.0
        if not CORS_MIDDLEWARE.search(source_code):
            return 0.0, ["CRITICAL: No CORS configuration found. All cross-origin browser requests will be blocked."]

        # ── OWASP Critical: wildcard + credentials → instant 0.0 ──────────────
        has_wildcard_origin = bool(WILDCARD_ORIGIN.search(source_code))
        has_credentials = bool(CREDENTIALS_ENABLED.search(source_code) or re.search(r'Access-Control-Allow-Credentials\b.*(?:true|["\']true["\'])', source_code, re.I))
        
        if has_wildcard_origin and has_credentials:
            return 0.0, ["CRITICAL: Wildcard CORS origins ('*') combined with credentials enabled allows cross-site request forgery. Change to explicit origins."]

        score = 0.0
        suggestions = []

        # 1. Explicit origin whitelist (0.30) or Wildcard (0.05)
        has_explicit_whitelist = (
            re.search(r'(?:allow_origins|origins|CORS_ALLOWED_ORIGINS|allowedOrigins|AllowOrigins)\s*[=:]\s*\[(?!\s*["\']?\*["\']?\s*\])', source_code, re.I) or
            re.search(r'allowedOrigins\s*=\s*\{[^}]*https', source_code, re.I) or
            re.search(r'origins\s*=\s*\{[^}]*https', source_code, re.I) or
            re.search(r'AllowOrigins.*\[.*https', source_code, re.I) or
            re.search(r'origin\s*:\s*\([^)]*\)', source_code, re.I) or
            re.search(r'origin\s*:\s*\[(?!\s*["\']?\*["\']?\s*\])', source_code, re.I)
        )
        
        if has_explicit_whitelist:
            score += 0.30
        elif has_wildcard_origin:
            score += 0.05
            suggestions.append("CRITICAL: Avoid wildcard CORS origins ('*') in production. Explicitly list trusted domains.")
        else:
            suggestions.append("Define explicit 'allowed_origins' to restrict API access strictly to trusted clients.")

        # 2. Credentials mode handled correctly (0.25)
        if has_credentials:
            score += 0.25
        elif re.search(r'(?:allow_credentials|supports_credentials|CORS_ALLOW_CREDENTIALS|allowCredentials)\s*[=:]\s*(?:False|false|"false")', source_code, re.I):
            score += 0.25
        else:
            pass

        # 3. Allowed methods restricted (not wildcard) (0.20)
        has_methods_explicit = (
            re.search(r'(?:allow_methods|methods|CORS_ALLOW_METHODS|allowedMethods|AllowedMethods|AllowMethods)\s*[=:]\s*\[(?!\s*["\']?\*["\']?\s*\])', source_code, re.I) or
            re.search(r'methods\s*=\s*\{[^}]*RequestMethod', source_code, re.I)
        )
        has_methods_wildcard = re.search(r'(?:allow_methods|methods)\s*[=:]\s*\[\s*["\']\*["\']\s*\]', source_code, re.I)
        
        if has_methods_explicit:
            score += 0.20
        elif not has_methods_wildcard and CORS_MIDDLEWARE.search(source_code):
            score += 0.10
            suggestions.append("Explicitly list allowed CORS methods (e.g., GET, POST, OPTIONS) instead of relying on permissive defaults.")
        else:
            suggestions.append("Avoid allowing all HTTP methods ('*') via CORS. Restrict exactly to what endpoints require.")

        # 4. Allowed headers declared explicitly (0.15)
        has_headers_explicit = (
            re.search(r'(?:allow_headers|allowedHeaders|CORS_ALLOW_HEADERS|AllowedHeaders|AllowHeaders)\s*[=:]\s*\[', source_code, re.I) or
            re.search(r'allowedHeaders\s*=\s*\{', source_code, re.I)
        )
        if has_headers_explicit:
            score += 0.15
        else:
            suggestions.append("Explicitly list allowed CORS headers (e.g. Authorization, Content-Type) instead of using wildcards ('*').")

        # 5. Preflight OPTIONS handled (0.10)
        has_preflight = (
            re.search(r'app\.options\s*\(|OPTIONS.*cors|cors.*OPTIONS', source_code, re.I) or
            re.search(r'RequestMethod\.OPTIONS|allowedMethods.*OPTIONS|methods.*OPTIONS|OPTIONS.*methods', source_code, re.I) or
            re.search(r'AllowMethods.*OPTIONS', source_code, re.I)
        )
        if has_preflight:
            score += 0.10
        else:
            suggestions.append("Handle CORS preflight (OPTIONS) requests explicitly to avoid browser rejection of non-simple requests.")

        return round(min(max(score, 0.0), 1.0), 4), suggestions
