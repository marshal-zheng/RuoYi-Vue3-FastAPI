"""Async circuit breaker implementation."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

from utils.log_util import logger
from resilience.models import CircuitBreakerConfig


STATE_CLOSED = 'CLOSED'
STATE_OPEN = 'OPEN'
STATE_HALF_OPEN = 'HALF_OPEN'


class CircuitBreakerOpenError(RuntimeError):
    """Raised when circuit is open and call is rejected."""


@dataclass
class CircuitBreakerSnapshot:
    name: str
    state: str
    failures: int
    successes: int
    opened_at: Optional[float]
    rejected_total: int


class CircuitBreaker:
    """Circuit breaker state machine."""

    def __init__(self, name: str, config: CircuitBreakerConfig) -> None:
        self.name = name
        self.config = config
        self._lock = asyncio.Lock()

        self._state = STATE_CLOSED
        self._failures = 0
        self._successes = 0
        self._opened_at: Optional[float] = None
        self._half_open_calls = 0
        self._rejected_total = 0

    async def allow_request(self) -> bool:
        """Return True when request can pass through."""
        if not self.config.enabled:
            return True

        now = time.monotonic()
        async with self._lock:
            if self._state == STATE_OPEN:
                if self._opened_at is not None and (now - self._opened_at) >= self.config.recovery_timeout_seconds:
                    self._transition(STATE_HALF_OPEN)
                    self._half_open_calls = 0
                    self._successes = 0
                else:
                    self._rejected_total += 1
                    return False

            if self._state == STATE_HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._rejected_total += 1
                    return False
                self._half_open_calls += 1

            return True

    async def on_success(self) -> None:
        if not self.config.enabled:
            return
        async with self._lock:
            if self._state == STATE_HALF_OPEN:
                self._successes += 1
                if self._successes >= self.config.half_open_success_threshold:
                    self._reset_to_closed()
                return

            if self._state == STATE_CLOSED:
                self._failures = 0

    async def on_failure(self, exc: Exception) -> None:
        if not self.config.enabled:
            return
        async with self._lock:
            if self._state == STATE_HALF_OPEN:
                self._open()
                logger.warning(f'circuit transition HALF_OPEN->OPEN name={self.name} reason={type(exc).__name__}')
                return

            if self._state == STATE_CLOSED:
                self._failures += 1
                if self._failures >= self.config.failure_threshold:
                    self._open()
                    logger.warning(
                        f'circuit transition CLOSED->OPEN name={self.name} failures={self._failures} '
                        f'reason={type(exc).__name__}'
                    )

    async def snapshot(self) -> CircuitBreakerSnapshot:
        async with self._lock:
            return CircuitBreakerSnapshot(
                name=self.name,
                state=self._state,
                failures=self._failures,
                successes=self._successes,
                opened_at=self._opened_at,
                rejected_total=self._rejected_total,
            )

    def _open(self) -> None:
        self._transition(STATE_OPEN)
        self._opened_at = time.monotonic()
        self._failures = 0
        self._successes = 0
        self._half_open_calls = 0

    def _reset_to_closed(self) -> None:
        self._transition(STATE_CLOSED)
        self._opened_at = None
        self._failures = 0
        self._successes = 0
        self._half_open_calls = 0

    def _transition(self, state: str) -> None:
        if self._state != state:
            logger.info(f'circuit transition name={self.name} from={self._state} to={state}')
            self._state = state


class CircuitBreakerRegistry:
    """Registry for named circuit breakers."""

    def __init__(self) -> None:
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        async with self._lock:
            breaker = self._breakers.get(name)
            if breaker is None:
                breaker = CircuitBreaker(name=name, config=config)
                self._breakers[name] = breaker
            return breaker

    async def list_snapshots(self) -> list[dict]:
        snapshots: list[dict] = []
        async with self._lock:
            breakers = list(self._breakers.values())
        for breaker in breakers:
            snap = await breaker.snapshot()
            snapshots.append(
                {
                    'name': snap.name,
                    'state': snap.state,
                    'failures': snap.failures,
                    'successes': snap.successes,
                    'openedAtMonotonic': snap.opened_at,
                    'rejectedTotal': snap.rejected_total,
                }
            )
        snapshots.sort(key=lambda item: item['name'])
        return snapshots
