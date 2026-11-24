from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from src.config import Settings, setup_logger

retry_logger = setup_logger(Settings.LOG_DIR / "helpers.log", name="helpers.retry")

P = ParamSpec("P")
T = TypeVar("T")

_DEFAULT_RETRYABLE: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def _log_before_sleep(retry_state: RetryCallState) -> None:
    outcome = retry_state.outcome
    err = outcome.exception() if outcome is not None else None
    retry_logger.warning(f"Retry attempt {retry_state.attempt_number} after error: {err}")


def retry_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=initial_wait, max=max_wait),
        retry=retry_if_exception_type(retryable),
        reraise=True,
        before_sleep=_log_before_sleep,
    )


def retry_async_on_failure(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable: tuple[type[Exception], ...] = _DEFAULT_RETRYABLE,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    return retry_on_failure(
        max_attempts=max_attempts,
        initial_wait=initial_wait,
        max_wait=max_wait,
        retryable=retryable,
    )
