"""
Retry Utilities — Tenacity-based
==================================
Production-grade retry logic with exponential backoff, jitter, and
configurable exception targeting.

Requirements:
    pip install tenacity

Usage:
    from src.helpers.retry import retry_on_failure, retry_async_on_failure

    # Sync
    @retry_on_failure(max_attempts=3)
    def call_external_api():
        response = requests.get("https://api.example.com/data", timeout=10)
        response.raise_for_status()
        return response.json()

    # Async
    @retry_async_on_failure(max_attempts=5, retryable=(ConnectionError, TimeoutError))
    async def fetch_data():
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.example.com/data", timeout=10)
            resp.raise_for_status()
            return resp.json()

    # Manual (non-decorator)
    from src.helpers.retry import run_with_retry
    result = await run_with_retry(some_async_fn, arg1, arg2, max_attempts=3)
"""

from typing import TypeVar, Callable, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)

T = TypeVar("T")

# ── Default retryable exceptions ──────────────────────────────────────────────
# These cover the most common transient failures across HTTP, DB, and network.
_DEFAULT_RETRYABLE: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def retry_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    logger: Any = None,
):
    """
    Decorator for synchronous functions.

    Retries on specified transient exceptions with exponential backoff + jitter.

    Args:
        max_attempts:  Maximum number of attempts before giving up.
        initial_wait:  Base delay in seconds for the first retry.
        max_wait:      Cap on the delay between retries.
        retryable:     Tuple of exception types that trigger a retry.
        logger:        Optional logger for before-sleep logging.
    """
    kwargs = {
        "stop": stop_after_attempt(max_attempts),
        "wait": wait_exponential_jitter(initial=initial_wait, max=max_wait),
        "retry": retry_if_exception_type(retryable),
        "reraise": True,
    }
    if logger:
        kwargs["before_sleep"] = before_sleep_log(logger, 30)

    return retry(**kwargs)


def retry_async_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    logger: Any = None,
):
    """
    Decorator for async functions.

    Retries on specified transient exceptions with exponential backoff + jitter.

    Args:
        max_attempts:  Maximum number of attempts before giving up.
        initial_wait:  Base delay in seconds for the first retry.
        max_wait:      Cap on the delay between retries.
        retryable:     Tuple of exception types that trigger a retry.
        logger:        Optional logger for before-sleep logging.
    """
    kwargs = {
        "stop": stop_after_attempt(max_attempts),
        "wait": wait_exponential_jitter(initial=initial_wait, max=max_wait),
        "retry": retry_if_exception_type(retryable),
        "reraise": True,
    }
    if logger:
        kwargs["before_sleep"] = before_sleep_log(logger, 30)

    return retry(**kwargs)


async def run_with_retry(
    fn: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    **kwargs: Any,
) -> T:
    """
    Run an async callable with retry logic (non-decorator usage).

    Usage:
        result = await run_with_retry(fetch_user, user_id, max_attempts=5)
    """

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=initial_wait, max=max_wait),
        retry=retry_if_exception_type(retryable),
        reraise=True,
    )
    async def _inner():
        return await fn(*args, **kwargs)

    return await _inner()
