import re
from typing import Any
from helpers.tool import Tool

HTTP_CACHE_HEADERS = re.compile(
    r'\b(Cache-Control|ETag|Last-Modified|Expires|Vary|'
    r'cache_control|etag|last_modified|max.age|s.maxage|'
    r'no-cache|no-store|must-revalidate|public|private)\b',
    re.IGNORECASE,
)

APP_CACHE_BACKENDS = re.compile(
    r'\b(redis|memcache|memcached|pylibmc|aioredis|'
    r'django\.core\.cache|flask_caching|fastapi_cache|'
    r'cachetools|diskcache|dogpile\.cache)\b',
    re.IGNORECASE,
)

CACHE_OPERATIONS = re.compile(
    r'\.(get\(|set\(|delete\(|expire\(|setex\(|mget\(|mset\(|incr\(|decr\()\b'
    r'|cache\.(get|set|delete)\b'
    r'|r\.(get|set|delete|setex)\b',  # common redis variable name
    re.IGNORECASE,
)

CACHE_DECORATORS = re.compile(
    r'@(cache|cached|lru_cache|ttl_cache|cache_page|cache_control|'
    r'cached_property|memoize|memo)\b',
    re.IGNORECASE,
)

CACHE_INVALIDATION = re.compile(
    r'\b(invalidate|evict|bust|flush|delete_pattern|clear_cache|'
    r'cache\.delete|cache\.clear|cache\.invalidate)\b',
    re.IGNORECASE,
)

# Signals that caching might be inappropriate (auth-sensitive endpoints)
AUTH_SENSITIVE = re.compile(
    r'\b(user_id|current_user|request\.user|Authorization|Bearer|'
    r'session\[|is_authenticated|login_required)\b',
    re.IGNORECASE,
)

NO_STORE_USED = re.compile(
    r'no.store|no.cache',
    re.IGNORECASE,
)


class CachingStrategy(Tool):
    def __init__(self):
        super().__init__(
            name="caching_strategy",
            description=(
                "Scores the caching strategy in REST API code: checks for HTTP cache headers, "
                "application-level cache (Redis/Memcached), cache decorators, and "
                "cache invalidation logic."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        score = 0.0

        # 1. HTTP-level cache headers (0.25)
        has_http_cache = bool(HTTP_CACHE_HEADERS.search(source_code))
        if has_http_cache:
            score += 0.25

        # 2. Application cache backend imported/used (0.20)
        has_backend = bool(APP_CACHE_BACKENDS.search(source_code))
        if has_backend:
            score += 0.20

        # 3. Actual cache operations (get/set) (0.25)
        cache_op_count = len(CACHE_OPERATIONS.findall(source_code))
        if cache_op_count >= 2:
            score += 0.25
        elif cache_op_count == 1:
            score += 0.12

        # 4. Cache decorators (0.15)
        has_decorator = bool(CACHE_DECORATORS.search(source_code))
        if has_decorator:
            score += 0.15

        # 5. Cache invalidation logic (0.15)
        has_invalidation = bool(CACHE_INVALIDATION.search(source_code))
        if has_invalidation:
            score += 0.15

        # 6. Auth-sensitive endpoints: reward explicit no-store (or neutral)
        is_auth_sensitive = bool(AUTH_SENSITIVE.search(source_code))
        if is_auth_sensitive:
            if bool(NO_STORE_USED.search(source_code)):
                score += 0.10   # Good: explicitly disabled cache for sensitive data
            else:
                score -= 0.10   # Risky: might be caching user-specific data

        # If no caching at all and code returns collections → mild penalty
        if score == 0.0:
            return 0.2   # No caching detected — not necessarily wrong, but not ideal

        return round(min(max(score, 0.0), 1.0), 4)