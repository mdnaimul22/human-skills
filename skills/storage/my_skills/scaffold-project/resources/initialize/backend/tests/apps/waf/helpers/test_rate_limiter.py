import time
from src.apps.waf.helpers.rate_limiter import TokenBucketRateLimiter

def test_initial_request_allowed():
    limiter = TokenBucketRateLimiter(default_rpm=60, default_burst=10)
    decision = limiter.check("192.168.1.100")
    assert decision.allowed is True
    assert decision.remaining_tokens >= 68.0

def test_rate_limit_exhaustion():
    limiter = TokenBucketRateLimiter(default_rpm=2, default_burst=0)
    d1 = limiter.check("1.2.3.4")
    assert d1.allowed is True
    d2 = limiter.check("1.2.3.4")
    assert d2.allowed is True
    d3 = limiter.check("1.2.3.4")
    assert d3.allowed is False
    assert d3.reset_seconds > 0.0

def test_high_capacity_endpoint_has_higher_limits():
    limiter = TokenBucketRateLimiter(default_rpm=60, default_burst=10, high_rpm=600, high_burst=100)
    normal = limiter.check("5.6.7.8", "/api/v1/tools")
    assert normal.limit_rpm == 60
    high = limiter.check("9.10.11.12", "/api/v1/tools/status/12345")
    assert high.limit_rpm == 600

def test_cleanup_stale_buckets():
    limiter = TokenBucketRateLimiter(cleanup_threshold_seconds=0.01)
    limiter.check("10.0.0.1")
    assert limiter.active_buckets_count() == 1
    time.sleep(0.02)
    cleaned = limiter.cleanup_stale()
    assert cleaned == 1
    assert limiter.active_buckets_count() == 0
