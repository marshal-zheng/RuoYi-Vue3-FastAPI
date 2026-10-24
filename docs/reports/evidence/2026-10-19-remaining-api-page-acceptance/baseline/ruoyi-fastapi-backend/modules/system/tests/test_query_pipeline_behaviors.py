from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from modules.system.application.behaviors.query_behaviors import QueryPerformanceBehavior
from modules.system.application.handler_registry import HandlerRegistry
from modules.system.application.mediator import Mediator
from modules.system.application.query_services import ComposedQueryExecutor, ComposedQueryTimeoutError


@dataclass
class _SlowQuery:
    trace_id: str = 'trace-1'
    request_id: str = 'request-1'


class _SlowQueryHandler:
    async def handle(self, request: _SlowQuery) -> str:
        _ = request
        await asyncio.sleep(0.005)
        return 'ok'


@dataclass
class _FailQuery:
    trace_id: str = 'trace-2'
    request_id: str = 'request-2'


class _FailQueryHandler:
    async def handle(self, request: _FailQuery) -> str:
        _ = request
        raise RuntimeError('query_failed')


@pytest.mark.asyncio
async def test_query_performance_behavior_records_slow_query_observation() -> None:
    observed: list[dict[str, object]] = []
    registry = HandlerRegistry()
    registry.register_query(_SlowQuery, _SlowQueryHandler())
    mediator = Mediator(
        registry,
        query_behaviors=(
            QueryPerformanceBehavior(
                slow_threshold_ms=1.0,
                observation_handler=observed.append,
            ),
        ),
    )

    result = await mediator.query(_SlowQuery())

    assert result == 'ok'
    assert observed
    assert observed[0]['query_type'] == '_SlowQuery'
    assert observed[0]['success'] is True
    assert observed[0]['is_slow'] is True


@pytest.mark.asyncio
async def test_query_performance_behavior_records_failure_observation() -> None:
    observed: list[dict[str, object]] = []
    registry = HandlerRegistry()
    registry.register_query(_FailQuery, _FailQueryHandler())
    mediator = Mediator(
        registry,
        query_behaviors=(
            QueryPerformanceBehavior(
                slow_threshold_ms=1000.0,
                observation_handler=observed.append,
            ),
        ),
    )

    with pytest.raises(RuntimeError, match='query_failed'):
        await mediator.query(_FailQuery())

    assert observed
    assert observed[0]['query_type'] == '_FailQuery'
    assert observed[0]['success'] is False
    assert observed[0]['status'] == 'failed'


@pytest.mark.asyncio
async def test_composed_query_executor_parallel_success() -> None:
    executor = ComposedQueryExecutor(query_name='UserDetailOptions', timeout_seconds=0.1)
    result = await executor.run(
        {
            'roles': lambda: _sleep_return(0.01, ['admin']),
            'posts': lambda: _sleep_return(0.01, ['dev']),
        },
        trace_id='trace-3',
        request_id='request-3',
    )

    assert result == {'roles': ['admin'], 'posts': ['dev']}


@pytest.mark.asyncio
async def test_composed_query_executor_timeout() -> None:
    executor = ComposedQueryExecutor(query_name='RoleDeptTree', timeout_seconds=0.005)

    with pytest.raises(ComposedQueryTimeoutError) as exc_info:
        await executor.run(
            {
                'dept_tree': lambda: _sleep_return(0.02, ['dept']),
                'checked_keys': lambda: _sleep_return(0.02, [1]),
            }
        )

    assert exc_info.value.query_name == 'RoleDeptTree'
    assert exc_info.value.branch_names == ('dept_tree', 'checked_keys')


async def _sleep_return(delay_seconds: float, value):
    await asyncio.sleep(delay_seconds)
    return value
