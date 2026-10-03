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

from typing import TypeVar, Callable, Protocol, ParamSpec

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)

T = TypeVar("T")
P = ParamSpec("P")

class LoggerProtocol(Protocol):
    def warning(self, msg: str) -> None:
        ...

_DEFAULT_RETRYABLE: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def _build_retry(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    logger: LoggerProtocol | None = None,
):
    kwargs = {
        "stop": stop_after_attempt(max_attempts),
        "wait": wait_exponential_jitter(initial=initial_wait, max=max_wait),
        "retry": retry_if_exception_type(retryable),
        "reraise": True,
    }
    if logger is not None:
        kwargs["before_sleep"] = before_sleep_log(logger, 30)
    return retry(**kwargs)


def retry_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    logger: LoggerProtocol | None = None,
):
    return _build_retry(max_attempts, initial_wait, max_wait, retryable, logger)


def retry_async_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    logger: LoggerProtocol | None = None,
):
    return _build_retry(max_attempts, initial_wait, max_wait, retryable, logger)


async def run_with_retry(
    fn: Callable[P, T],
    *args: P.args,
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
    **kwargs: P.kwargs,
) -> T:
    decorator = _build_retry(max_attempts, initial_wait, max_wait, retryable)

    @decorator
    async def _inner():
        return await fn(*args, **kwargs)

    return await _inner()
