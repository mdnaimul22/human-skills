import re
from typing import Any
from helpers.tool import Tool


# ── Rate limiting signal patterns ─────────────────────────────────────────────

RATE_LIMIT_LIBRARIES = re.compile(
    r'\b(flask_limiter|slowapi|fastapi_limiter|django_ratelimit|'
    r'limits|ratelimit|throttle|Throttle|APIThrottle|'
    r'django_throttle|express-rate-limit|rate.limit)\b',
    re.IGNORECASE,
)

RATE_LIMIT_DECORATORS = re.compile(
    r'@(limiter\.(limit|shared_limit)|ratelimit|throttle|'
    r'limit\(|Throttle\(|RateLimit\(|rate_limit)',
    re.IGNORECASE,
)

RATE_LIMIT_MIDDLEWARE = re.compile(
    r'\b(RateLimitMiddleware|ThrottleMiddleware|SlowAPIMiddleware|'
    r'limiter\.init_app|app\.state\.limiter|'
    r'DEFAULT_THROTTLE_CLASSES|DEFAULT_THROTTLE_RATES|'
    r'AnonRateThrottle|UserRateThrottle|ScopedRateThrottle)\b',
    re.IGNORECASE,
)

BACKEND_RATE_LOGIC = re.compile(
    r'\b(token_bucket|sliding_window|fixed_window|leaky_bucket|'
    r'rate_counter|request_count|redis.*incr|INCR.*rate|'
    r'rate_key|rate_limit_key|requests_per_\w+|calls_per_\w+)\b',
    re.IGNORECASE,
)

RESPONSE_429 = re.compile(
    r'\b(429|TOO_MANY_REQUESTS|Too Many Requests|rate.?limit.?exceeded|'
    r'HTTPStatus\.TOO_MANY_REQUESTS)\b',
    re.IGNORECASE,
)

RATE_LIMIT_HEADERS = re.compile(
    r'\b(X-RateLimit-Limit|X-RateLimit-Remaining|X-RateLimit-Reset|'
    r'Retry-After|RateLimit-Limit|RateLimit-Remaining|RateLimit-Reset)\b',
    re.IGNORECASE,
)

PER_USER_RATE = re.compile(
    r'\b(per_user|user_rate|user.?key|user.?limit|'
    r'get_ident|get_user_id|current_user.*limit|'
    r'authenticated.*rate|user.?throttle)\b',
    re.IGNORECASE,
)

# Signals that rate limiting is intentionally disabled
RATE_LIMIT_EXEMPT = re.compile(
    r'@(limiter\.exempt|no_limit|rate_limit_exempt|exempt)',
    re.IGNORECASE,
)


class RateLimiting(Tool):
    def __init__(self):
        super().__init__(
            name="rate_limiting",
            description=(
                "Scores rate limiting implementation in REST API code: checks for rate limiting "
                "libraries, decorators, middleware, 429 response handling, rate limit headers, "
                "and per-user limiting strategies."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        score = 0.0

        # 1. Rate limiting library imported (0.25)
        if RATE_LIMIT_LIBRARIES.search(source_code):
            score += 0.25

        # 2. Rate limiting decorators on endpoints (0.25)
        decorator_count = len(RATE_LIMIT_DECORATORS.findall(source_code))
        if decorator_count >= 2:
            score += 0.25
        elif decorator_count == 1:
            score += 0.15

        # 3. Middleware-level rate limiting (0.20)
        if RATE_LIMIT_MIDDLEWARE.search(source_code):
            score += 0.20

        # 4. Custom backend rate limiting logic (0.15)
        if BACKEND_RATE_LOGIC.search(source_code):
            score += 0.15

        # 5. Proper 429 response (0.10)
        if RESPONSE_429.search(source_code):
            score += 0.10

        # 6. Rate limit headers in response (0.10)
        if RATE_LIMIT_HEADERS.search(source_code):
            score += 0.10

        # 7. Per-user rate limiting bonus (0.05)
        if PER_USER_RATE.search(source_code):
            score += 0.05

        # 8. If endpoints exist but no rate limiting at all
        has_routes = re.search(
            r'@(app|router)\.(get|post|put|delete|patch)|@route\(',
            source_code, re.IGNORECASE
        )
        all_exempt = bool(RATE_LIMIT_EXEMPT.search(source_code))

        if has_routes and score == 0.0 and not all_exempt:
            return 0.05   # Routes with zero rate limiting — very low score

        return round(min(max(score, 0.0), 1.0), 4)