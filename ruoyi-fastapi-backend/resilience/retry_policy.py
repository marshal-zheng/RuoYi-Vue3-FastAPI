"""Retry helpers backed by tenacity with safe fallback."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Sequence, Tuple, Type

from utils.log_util import logger
from resilience.models import RetryPolicyConfig

try:
    from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_random_exponential
except Exception:  # pragma: no cover - optional dependency fallback
    AsyncRetrying = None
    retry_if_exception_type = None
    stop_after_attempt = None
    wait_random_exponential = None


@dataclass
class RetryContext:
    """Retry context attached to terminal failures."""

    operation: str
    attempts: int
    wait_seconds: float
    exception_type: str


class RetryExhaustedError(RuntimeError):
    """Raised when retries are exhausted."""

    def __init__(self, context: RetryContext, original: Exception) -> None:
        super().__init__(f'retry exhausted for {context.operation} after {context.attempts} attempts')
        self.context = context
        self.original = original


def _resolve_exception_types(names: Sequence[str]) -> Tuple[Type[BaseException], ...]:
    builtins_map = {
        'Exception': Exception,
        'TimeoutError': TimeoutError,
        'ConnectionError': ConnectionError,
        'OSError': OSError,
        'ValueError': ValueError,
        'RuntimeError': RuntimeError,
    }
    resolved = []
    for item in names:
        exc = builtins_map.get(item)
        if exc is not None:
            resolved.append(exc)
    return tuple(resolved) if resolved else (Exception,)


def _is_retryable(exc: Exception, exc_types: Tuple[Type[BaseException], ...]) -> bool:
    return isinstance(exc, exc_types)


async def execute_with_retry(
    operation: str,
    policy: RetryPolicyConfig,
    action: Callable[[], Awaitable[Any]],
) -> Any:
    """Execute action with retry policy."""
    if not policy.enabled:
        return await action()

    retry_types = _resolve_exception_types(policy.retry_exceptions)

    if AsyncRetrying is not None:
        attempt_no = 0
        last_sleep = 0.0

        async def _before_sleep(retry_state) -> None:
            nonlocal last_sleep
            attempt = int(retry_state.attempt_number)
            exc = retry_state.outcome.exception() if retry_state.outcome is not None else None
            wait_seconds = float(getattr(retry_state.next_action, 'sleep', 0.0) or 0.0)
            last_sleep = wait_seconds
            logger.warning(
                f'retry attempt={attempt} operation={operation} wait_seconds={wait_seconds:.3f} '
                f'exception_type={type(exc).__name__ if exc else "Unknown"}'
            )

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(retry_types),
                stop=stop_after_attempt(policy.max_retries + 1),
                wait=wait_random_exponential(multiplier=policy.base_delay, max=policy.max_delay),
                before_sleep=_before_sleep,
                reraise=True,
            ):
                with attempt:
                    attempt_no = int(attempt.retry_state.attempt_number)
                    return await action()
        except Exception as exc:
            context = RetryContext(
                operation=operation,
                attempts=max(attempt_no, policy.max_retries + 1),
                wait_seconds=last_sleep,
                exception_type=type(exc).__name__,
            )
            raise RetryExhaustedError(context, exc) from exc

    # Fallback path when tenacity is unavailable.
    logger.warning('tenacity is unavailable, using built-in retry fallback')
    last_wait = 0.0
    max_attempts = policy.max_retries + 1
    for attempt in range(1, max_attempts + 1):
        try:
            return await action()
        except Exception as exc:
            if attempt >= max_attempts or not _is_retryable(exc, retry_types):
                context = RetryContext(
                    operation=operation,
                    attempts=attempt,
                    wait_seconds=last_wait,
                    exception_type=type(exc).__name__,
                )
                raise RetryExhaustedError(context, exc) from exc

            backoff = min(policy.max_delay, policy.base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0.0, policy.jitter)
            last_wait = backoff + jitter
            logger.warning(
                f'retry attempt={attempt} operation={operation} wait_seconds={last_wait:.3f} '
                f'exception_type={type(exc).__name__}'
            )
            await asyncio.sleep(last_wait)

    raise RuntimeError('unreachable')
