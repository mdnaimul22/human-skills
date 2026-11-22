import time
from dataclasses import dataclass
from src.apps.waf.schema import RateLimitDecision

@dataclass
class TokenBucket:
    tokens: float
    last_refill: float
    capacity: float
    refill_rate: float

_HIGH_CAPACITY_PREFIXES: tuple[str, ...] = (
    "/api/v1/tools/status/",
    "/_next/",
    "/static/",
    "/favicon.ico",
)

class TokenBucketRateLimiter:
    def __init__(
        self,
        default_rpm: int = 120,
        default_burst: int = 30,
        high_rpm: int = 600,
        high_burst: int = 100,
        cleanup_threshold_seconds: float = 300.0,
        high_capacity_prefixes: tuple[str, ...] | None = None,
    ) -> None:
        self._default_rpm = default_rpm
        self._default_burst = default_burst
        self._high_rpm = high_rpm
        self._high_burst = high_burst
        self._cleanup_threshold = cleanup_threshold_seconds
        self._high_capacity_prefixes = high_capacity_prefixes if high_capacity_prefixes is not None else _HIGH_CAPACITY_PREFIXES
        self._buckets: dict[str, TokenBucket] = {}

    def _resolve_limits(self, path: str) -> tuple[int, int]:
        if path.startswith(self._high_capacity_prefixes):
            return self._high_rpm, self._high_burst
        return self._default_rpm, self._default_burst

    def _get_or_create_bucket(self, ip: str, rpm: int, burst: int, now: float) -> TokenBucket:
        bucket = self._buckets.get(ip)
        capacity = float(rpm + burst)
        refill_rate = float(rpm) / 60.0
        if bucket is None:
            bucket = TokenBucket(
                tokens=capacity,
                last_refill=now,
                capacity=capacity,
                refill_rate=refill_rate,
            )
            self._buckets[ip] = bucket
            return bucket

        elapsed = max(0.0, now - bucket.last_refill)
        bucket.tokens = min(bucket.capacity, bucket.tokens + (elapsed * bucket.refill_rate))
        bucket.last_refill = now
        return bucket

    def check(self, ip: str, path: str = "") -> RateLimitDecision:
        now = time.time()
        rpm, burst = self._resolve_limits(path)
        bucket = self._get_or_create_bucket(ip, rpm, burst, now)

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            allowed = True
        else:
            allowed = False

        reset_seconds = 0.0
        if bucket.tokens < 1.0:
            reset_seconds = (1.0 - bucket.tokens) / bucket.refill_rate

        return RateLimitDecision(
            allowed=allowed,
            remaining_tokens=max(0.0, bucket.tokens),
            reset_seconds=reset_seconds,
            limit_rpm=rpm,
        )

    def cleanup_stale(self) -> int:
        now = time.time()
        stale_ips = [
            ip for ip, b in self._buckets.items()
            if now - b.last_refill > self._cleanup_threshold
        ]
        for ip in stale_ips:
            del self._buckets[ip]
        return len(stale_ips)

    def active_buckets_count(self) -> int:
        return len(self._buckets)
