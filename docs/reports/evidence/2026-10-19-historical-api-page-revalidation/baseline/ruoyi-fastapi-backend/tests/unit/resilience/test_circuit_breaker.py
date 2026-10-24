import asyncio

import pytest

from resilience.circuit_breaker import CircuitBreaker
from resilience.models import CircuitBreakerConfig


@pytest.mark.asyncio
async def test_circuit_breaker_open_and_recover():
    breaker = CircuitBreaker(
        name='redis.get',
        config=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=2,
            recovery_timeout_seconds=0.01,
            half_open_max_calls=1,
            half_open_success_threshold=1,
        ),
    )

    assert await breaker.allow_request() is True
    await breaker.on_failure(RuntimeError('boom-1'))
    assert await breaker.allow_request() is True
    await breaker.on_failure(RuntimeError('boom-2'))

    assert await breaker.allow_request() is False

    await asyncio.sleep(0.02)
    assert await breaker.allow_request() is True
    await breaker.on_success()

    snapshot = await breaker.snapshot()
    assert snapshot.state == 'CLOSED'
