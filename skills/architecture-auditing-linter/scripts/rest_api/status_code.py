"""
Tool: Status Code Appropriate Usage Score
Category: Design Quality

Evaluates whether HTTP status codes are used semantically correctly.
Designed as a universal, framework-agnostic judge covering:
  - Flask, FastAPI, Django REST Framework, aiohttp, Starlette
  - Express/Node.js, Gin (Go), Spring Boot (Java)
  - Python HTTPStatus enum, abort(), make_response(), Response()

Industry standard references:
  - RFC 7231 (HTTP/1.1 Semantics), RFC 6585 (Additional Status Codes)
  - Google API Design Guide
  - Microsoft REST API Guidelines
  - GitHub REST API Conventions
  - OWASP API Security Top 10

Correct semantics enforced:
  200 OK              → successful reads
  201 Created         → successful resource creation (POST)
  202 Accepted        → async job accepted (queued)
  204 No Content      → successful DELETE / PUT with no body
  301/302/307/308     → redirects
  400 Bad Request     → malformed / missing required fields
  401 Unauthorized    → not authenticated (missing/invalid token)
  403 Forbidden       → authenticated but no permission
  404 Not Found       → missing resource
  409 Conflict        → duplicate / state conflict
  422 Unprocessable   → semantic validation failure (Pydantic, schema)
  429 Too Many        → rate limit exceeded
  500 Internal Error  → unexpected server exception
  503 Unavailable     → downstream dependency down

Penalises:
  - Returning 200 for every response including errors
  - Returning 200 when auth/not-found/conflict context is present
"""
import re
from typing import Any, List, Tuple
from helpers.tool import Tool

# ---------------------------------------------------------------------------
# STEP 1 — Strip strings and comments before analysis
# This prevents false positives where "404" or "not found" appears in
# a message string or comment but is not an actual status code assignment.
# ---------------------------------------------------------------------------

_STRING_RE = re.compile(
    r'""".*?"""|' + r"'''.*?'''" + r'|"(?:[^"\\]|\\.)*"|' + r"'(?:[^'\\]|\\.)*'",
    re.DOTALL,
)
_COMMENT_RE = re.compile(r'#.*?$|//.*?$', re.MULTILINE)
_BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)


def _clean(source: str) -> str:
    """Remove string literals and comments to avoid false positives."""
    out = _STRING_RE.sub(' __STR__ ', source)
    out = _COMMENT_RE.sub('', out)
    out = _BLOCK_COMMENT_RE.sub('', out)
    return out


# ---------------------------------------------------------------------------
# STEP 2 — Status code extraction patterns (framework-agnostic)
# Covers Python, JavaScript/TypeScript, Go, Java syntax.
# ---------------------------------------------------------------------------

_CODE_PATTERNS = [
    # Python: status_code=201, status=201, code=201, http_status=201
    re.compile(r'\b(?:status_code|status|code|http_status)\s*[=:]\s*(\d{3})\b', re.I),

    # Python HTTPStatus enum: HTTPStatus.CREATED, HTTPStatus.NOT_FOUND
    re.compile(
        r'HTTPStatus\.(\w+)',
        re.I,
    ),

    # Flask/FastAPI jsonify tuple: return jsonify(...), 201
    re.compile(r'jsonify\b[^)]*\)\s*,\s*(\d{3})\b'),
    # Flask: jsonify(...nested...), 422  — handles nested calls via line-end anchor
    re.compile(r',\s*(\d{3})\s*$', re.MULTILINE),

    # Flask string tuple: return "...", 201  or  return {...}, 201
    re.compile(r'return\s+[^,\n]+,\s*(\d{3})\b'),

    # Flask abort(404), abort(500)
    re.compile(r'\babort\s*\(\s*(\d{3})\s*\)'),

    # Flask raise HTTPException(401) / raise HTTP_400()
    re.compile(r'raise\s+HTTP(?:Exception)?\s*\(\s*(\d{3})'),

    # FastAPI HTTPException(status_code=422)
    re.compile(r'HTTPException\s*\([^)]*status_code\s*=\s*(\d{3})'),

    # FastAPI/Starlette JSONResponse(status_code=201) / Response(status_code=204)
    re.compile(r'(?:JSONResponse|Response)\s*\([^)]*status_code\s*=\s*(\d{3})'),

    # aiohttp web.Response(status=201)
    re.compile(r'web\.Response\s*\([^)]*status\s*=\s*(\d{3})'),

    # Flask make_response(..., 401)  — last positional arg is status
    re.compile(r'make_response\s*\([^)]+,\s*(\d{3})\s*\)'),

    # DRF: Response(..., status=status.HTTP_201_CREATED) or status.HTTP_XXX
    re.compile(r'status\.HTTP_(\d{3})_\w+'),

    # DRF: Response(status=status.HTTP_204_NO_CONTENT) bare status kwarg
    re.compile(r'Response\s*\([^)]*status\s*=\s*status\.HTTP_(\d{3})'),

    # Express/Node.js: res.status(201) / res.status(404).json(...)
    re.compile(r'\.status\s*\(\s*(\d{3})\s*\)'),

    # Gin Go: c.JSON(201, ...) / c.JSON(404, ...)
    re.compile(r'\bc\.(?:JSON|String|Data|HTML|XML|YAML|AbortWithStatus)\s*\(\s*(\d{3})'),

    # Spring Boot: ResponseEntity.status(201) / .status(HttpStatus.CREATED)
    re.compile(r'ResponseEntity\.status\s*\(\s*(\d{3})\s*\)'),

    # Spring HttpStatus enum: HttpStatus.CREATED, HttpStatus.NOT_FOUND
    re.compile(r'HttpStatus\.(\w+)'),

    # Spring: ResponseEntity.notFound() / ResponseEntity.noContent() / ResponseEntity.ok()
    # These map to fixed codes — handled via SPRING_SEMANTIC below

    # Flask redirect(url, code=301)
    re.compile(r'redirect\s*\([^)]*code\s*=\s*(\d{3})'),
]

# HTTPStatus enum name → int
_HTTPSTATUS_MAP = {
    # 2xx
    'OK': 200, 'CREATED': 201, 'ACCEPTED': 202,
    'NON_AUTHORITATIVE_INFORMATION': 203, 'NO_CONTENT': 204,
    'RESET_CONTENT': 205, 'PARTIAL_CONTENT': 206,
    # 3xx
    'MULTIPLE_CHOICES': 300, 'MOVED_PERMANENTLY': 301,
    'FOUND': 302, 'SEE_OTHER': 303, 'NOT_MODIFIED': 304,
    'TEMPORARY_REDIRECT': 307, 'PERMANENT_REDIRECT': 308,
    # 4xx
    'BAD_REQUEST': 400, 'UNAUTHORIZED': 401, 'PAYMENT_REQUIRED': 402,
    'FORBIDDEN': 403, 'NOT_FOUND': 404, 'METHOD_NOT_ALLOWED': 405,
    'NOT_ACCEPTABLE': 406, 'CONFLICT': 409, 'GONE': 410,
    'UNPROCESSABLE_ENTITY': 422, 'TOO_MANY_REQUESTS': 429,
    # 5xx
    'INTERNAL_SERVER_ERROR': 500, 'NOT_IMPLEMENTED': 501,
    'BAD_GATEWAY': 502, 'SERVICE_UNAVAILABLE': 503,
    'GATEWAY_TIMEOUT': 504,
}

# Spring HttpStatus enum name → int (superset of HTTPStatus)
_SPRING_STATUS_MAP = {**_HTTPSTATUS_MAP, 'UNPROCESSABLE_ENTITY': 422}

# Spring semantic shorthand methods → fixed code
_SPRING_SEMANTIC_RE = re.compile(
    r'ResponseEntity\.'
    r'(?P<method>ok|notFound|noContent|created|badRequest|'
    r'unprocessableEntity|conflict|forbidden|unauthorized|'
    r'internalServerError|accepted)\s*\(',
    re.I,
)
_SPRING_SEMANTIC_MAP = {
    'ok': 200, 'notfound': 404, 'nocontent': 204, 'created': 201,
    'badrequest': 400, 'unprocessableentity': 422, 'conflict': 409,
    'forbidden': 403, 'unauthorized': 401, 'internalservererror': 500,
    'accepted': 202,
}


def _extract_codes(clean_source: str) -> List[int]:
    """Extract all explicit status codes from cleaned source."""
    codes: List[int] = []

    # Spring semantic shorthands first
    for m in _SPRING_SEMANTIC_RE.finditer(clean_source):
        method = m.group('method').lower()
        if method in _SPRING_SEMANTIC_MAP:
            codes.append(_SPRING_SEMANTIC_MAP[method])

    for pattern in _CODE_PATTERNS:
        for m in pattern.finditer(clean_source):
            raw = m.group(1)
            if raw.isdigit():
                codes.append(int(raw))
            else:
                # Enum name — check both maps
                upper = raw.upper()
                if upper in _HTTPSTATUS_MAP:
                    codes.append(_HTTPSTATUS_MAP[upper])
                elif upper in _SPRING_STATUS_MAP:
                    codes.append(_SPRING_STATUS_MAP[upper])

    # Deduplicate while preserving order (count still possible)
    seen = set()
    result = []
    for c in codes:
        key = (c, len([x for x in result if x == c]))  # allow duplicates by count
        result.append(c)
    return result


# ---------------------------------------------------------------------------
# STEP 3 — Context signals → expected status codes
# Patterns match operation semantics in the cleaned code body.
# ---------------------------------------------------------------------------

CONTEXT_SIGNALS: List[Tuple[re.Pattern, List[int]]] = [
    # Creation — call expression on any db/ORM object
    # db.insert_one(), col.insert(), session.add(), serializer.save(), .objects.create()
    (re.compile(
        r'\.(?:insert|insert_one|insert_many|add|create|save|persist|save_one|save_all)\s*\('
        r'|serializer\.save\s*\('
        r'|\.objects\.create\s*\('
        r'|userRepository\.save\s*\('
        r'|teamRepository\.save\s*\(',
        re.I,
    ), [201, 200]),

    # Deletion — call expression on any db/ORM object
    (re.compile(
        r'\.(?:delete|delete_one|delete_many|remove|deleteById|deletebyid|'  
        r'delete_all)\s*\('
        r'|\.objects\.(?:filter|get)\b.*?\.delete\s*\(',
        re.I,
    ), [204, 200]),

    # Auth failure → 401
    (re.compile(
        r'\b(?:unauthorized|not_authenticated|invalid_token|missing_token|'
        r'authentication_required|invalid_credentials|invalid_password|'
        r'login_failed|is_authenticated\s*(?:==\s*False|is\s+False|not\b)|'
        r'verify_token|decode_token|not\s+token|not\s+authenticated)\b',
        re.I,
    ), [401]),

    # Permission denied → 403
    (re.compile(
        r'\b(?:forbidden|permission_denied|not_allowed|access_denied|'
        r'has_perm|is_admin|check_permission|AllowAny|IsAuthenticated)\b',
        re.I,
    ), [403]),

    # Not found — explicit not-found exception or ORM method raising 404
    # Deliberately exclude find_one() — it is a query, not a not-found assertion
    (re.compile(
        r'\b(?:not_found|DoesNotExist|does_not_exist|no_such|'
        r'first_or_404|get_or_404|orElse.*notFound|'
        r'raise.*NotFound|raise.*404|NotFoundException)\b',
        re.I,
    ), [404]),

    # Validation error → 400 or 422
    # Require call or attribute form to avoid matching variable names
    (re.compile(
        r'\b(?:ValidationError|validation_error|bad_request|malformed)\b'
        r'|pydantic\.'
        r'|serializer\.errors\b'
        r'|\.is_valid\s*\(',
        re.I,
    ), [400, 422]),

    # Conflict / duplicate → 409
    (re.compile(
        r'\b(?:already_exists|duplicate|conflict|unique_constraint|'
        r'existsByEmail|existsByName|already\s+exist|already\s+subscribed)\b',
        re.I,
    ), [409]),

    # Async accepted → 202
    (re.compile(
        r'\b(?:queue|enqueue|task|queued|async_job|job_id|celery|rq|'
        r'background_task|trigger_export|publish)\b',
        re.I,
    ), [202, 200]),

    # Rate limit → 429
    (re.compile(
        r'\b(?:rate_limit|rate_limiter|too_many_requests|'
        r'throttle|throttled|RateLimitExceeded|'
        r'limiter\.exceeded|rate.*exceeded)\b',
        re.I,
    ), [429]),

    # Server error → 500
    (re.compile(
        r'\b(?:internal_server_error|unexpected_error|traceback|'
        r'exception_caught|abort\s*\(\s*500)\b',
        re.I,
    ), [500]),

    # Service unavailable → 503
    (re.compile(
        r'\b(?:ServiceUnavailableError|service_unavailable|downstream|'
        r'dependency_down|circuit_breaker|unavailable)\b',
        re.I,
    ), [503, 500]),

    # Redirect → 301/302/307/308
    # Only match when redirect is called as a function (not just a word)
    (re.compile(
        r'redirect\s*\(|url_for\s*\(',
        re.I,
    ), [301, 302, 307, 308, 200]),
]

# Context window size around each signal match (chars)
_WINDOW_BEFORE = 200
_WINDOW_AFTER  = 500


def _check_contextual_correctness(clean_source: str) -> float:
    """
    For each context signal found, verify an appropriate code appears nearby.
    Returns a ratio of correctly-coded contexts [0.0, 1.0].
    """
    correct = 0.0
    total = 0

    for signal_pattern, expected_codes in CONTEXT_SIGNALS:
        for match in signal_pattern.finditer(clean_source):
            total += 1
            start = max(0, match.start() - _WINDOW_BEFORE)
            end   = min(len(clean_source), match.end() + _WINDOW_AFTER)
            window = clean_source[start:end]

            window_codes = _extract_codes(window)
            if any(c in expected_codes for c in window_codes):
                correct += 1.0
            elif not window_codes:
                # No status code near context — framework may handle it: neutral
                correct += 0.25
            else:
                # Wrong code present — clear mismatch
                correct += 0.0

    return (correct / total) if total > 0 else 0.5


def _penalise_200_overuse(codes: List[int]) -> float:
    """
    Returns a penalty [0.0, 0.35] when 200 dominates across multiple branches.
    Only penalises when there are >=3 code occurrences (multiple response paths).
    """
    if not codes or len(codes) < 3:
        return 0.0
    ratio_200 = codes.count(200) / len(codes)
    if ratio_200 == 1.0:
        return 0.35   # Every single response path returns 200
    if ratio_200 >= 0.80:
        return 0.20
    if ratio_200 >= 0.60:
        return 0.10
    return 0.0


class StatusCodeUsage(Tool):
    def __init__(self):
        super().__init__(
            name="status_code_usage",
            description=(
                "Universal HTTP status code usage scorer. Evaluates semantic correctness "
                "across Flask, FastAPI, DRF, aiohttp, Starlette, Express, Gin, Spring Boot. "
                "Checks 2xx/4xx/5xx context alignment and penalises 200-for-everything anti-pattern."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        # Strip strings and comments — prevents false positives from message strings
        clean = _clean(source_code)

        all_codes = _extract_codes(clean)
        suggestions = []

        # No explicit status codes at all → neutral baseline
        if not all_codes:
            return 0.40, ["No explicit HTTP status codes found. Use framework features to return precise status codes (e.g., 201, 404)."]

        contextual_score = _check_contextual_correctness(clean)

        # Check whether any context signals fired in this source
        _has_signals = any(
            pat.search(clean) for pat, _ in CONTEXT_SIGNALS
        )

        # Overuse penalty only applies when the code HAS semantic context
        # but returns 200 anyway. A plain GET /config returning 200 is fine.
        overuse_penalty = _penalise_200_overuse(all_codes) if _has_signals else 0.0
        
        if overuse_penalty > 0.0:
             suggestions.append("Overuse of HTTP 200 OK detected. Return semantic codes (e.g., 201 Created, 404 Not Found, 400 Bad Request) instead of returning 200 for everything.")

        if contextual_score < 0.8:
             suggestions.append("Review status code assignments. Some contexts (e.g., error handlers or DB writes) appear to return incorrect status codes.")

        # Variety bonus: more distinct codes = more intentional usage
        unique = len(set(all_codes))
        variety_bonus = min(0.10 * (unique - 1), 0.20) if unique > 1 else 0.0
        
        if unique <= 1 and _has_signals:
             suggestions.append("API uses very few distinct status codes. Expand your usage to improve client error handling.")

        final = contextual_score - overuse_penalty + variety_bonus
        return round(min(max(final, 0.0), 1.0), 4), suggestions