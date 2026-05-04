import re
from typing import Any
from helpers.tool_manager import Tool

RETRY_LIBRARIES = re.compile(
    r'\b(tenacity|backoff|retry|Retry|retrying|stamina|'
    r'urllib3\.util\.retry|requests\.adapters\.HTTPAdapter|'
    r'HTTPAdapter.*Retry|aiohttp.*retry|httpx.*retry)\b',
    re.IGNORECASE,
)

RETRY_DECORATORS = re.compile(
    r'@(retry|tenacity\.retry|backoff\.on_exception|backoff\.on_predicate|'
    r'on_exception|on_predicate|retry_with_backoff|'
    r'retry_on_exception|retry_on_result)\b',
    re.IGNORECASE,
)

EXPONENTIAL_BACKOFF = re.compile(
    r'\b(expo|exponential|backoff\.expo|wait_exponential|'
    r'wait_random_exponential|2\s*\*\*\s*\w+|'
    r'sleep.*\*.*attempt|sleep.*\*\*|jitter)\b',
    re.IGNORECASE,
)

MAX_RETRIES = re.compile(
    r'\b(max_tries|max_attempts|max_retries|retries\s*=\s*\d|'
    r'stop_after_attempt|stop_after_delay|MAX_RETRY|'
    r'num_retries|retry_limit)\b',
    re.IGNORECASE,
)

SPECIFIC_RETRY_ERRORS = re.compile(
    r'\b(ConnectionError|TimeoutError|HTTPError|RequestException|'
    r'OperationalError|ServiceUnavailable|TooManyRequests|'
    r'503|429|5\d\d.*retry|retry.*5\d\d)\b',
    re.IGNORECASE,
)

IDEMPOTENCY_SIGNALS = re.compile(
    r'\b(idempotent|Idempotency-Key|idempotency_key|'
    r'is_idempotent|safe_methods|GET.*retry|retry.*GET)\b',
    re.IGNORECASE,
)

# Anti-patterns
INFINITE_RETRY = re.compile(
    r'while\s+True.*retry|retry.*while\s+True',
    re.IGNORECASE | re.DOTALL,
)

BARE_SLEEP_RETRY = re.compile(
    r'time\.sleep\s*\(\s*\d+\s*\).*retry|'
    r'retry.*time\.sleep\s*\(\s*\d+\s*\)',
    re.IGNORECASE | re.DOTALL,
)

MANUAL_RETRY_LOOP = re.compile(
    r'for\s+\w+\s+in\s+range.*:\s*\n.*try\s*:',
    re.IGNORECASE | re.DOTALL,
)


class RetryLogic(Tool):
    def __init__(self):
        super().__init__(
            name="retry_logic",
            description=(
                "Scores retry logic implementation in REST API code: checks for retry libraries, "
                "exponential backoff, max retry limits, specific error targeting, and "
                "idempotency awareness."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        score = 0.0

        # 1. Retry library imported (0.25)
        has_library = bool(RETRY_LIBRARIES.search(source_code))
        if has_library:
            score += 0.25

        # 2. Retry decorator applied (0.25)
        decorator_count = len(RETRY_DECORATORS.findall(source_code))
        if decorator_count >= 1:
            score += 0.25

        # 3. Exponential backoff (0.20)
        has_exp_backoff = bool(EXPONENTIAL_BACKOFF.search(source_code))
        if has_exp_backoff:
            score += 0.20

        # 4. Max retry limit defined (0.15)
        has_max = bool(MAX_RETRIES.search(source_code))
        if has_max:
            score += 0.15

        # 5. Retry on specific errors only (0.10)
        has_specific = bool(SPECIFIC_RETRY_ERRORS.search(source_code))
        if has_specific:
            score += 0.10

        # 6. Idempotency awareness (0.05 bonus)
        if IDEMPOTENCY_SIGNALS.search(source_code):
            score += 0.05

        # Penalties
        if INFINITE_RETRY.search(source_code):
            score -= 0.20

        # Fixed-sleep retry (not backoff) — mild penalty
        has_bare_sleep = bool(BARE_SLEEP_RETRY.search(source_code))
        has_manual_loop = bool(MANUAL_RETRY_LOOP.search(source_code))

        if has_manual_loop and not has_library:
            # Manual retry loop without proper library — okay but not ideal
            if has_bare_sleep:
                score -= 0.10
            else:
                score += 0.05  # At least they're trying

        # No retry signals at all — check if external calls exist
        makes_external_calls = re.search(
            r'\b(requests\.|httpx\.|aiohttp\.|urllib|http\.client)\b',
            source_code, re.IGNORECASE
        )
        if makes_external_calls and score <= 0.0:
            return 0.10   # External calls with zero retry = reliability risk

        return round(min(max(score, 0.0), 1.0), 4)