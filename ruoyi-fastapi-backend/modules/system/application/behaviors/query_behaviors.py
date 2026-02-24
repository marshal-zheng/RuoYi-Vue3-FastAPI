"""Default query pipeline behaviors for system CQRS mediator."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from middlewares.trace_middleware import TraceCtx
from modules.system.application.contracts import IPipelineBehavior
from utils.log_util import logger

QueryNextHandler = Callable[[], Awaitable[Any]]
QueryObservationHandler = Callable[[dict[str, Any]], None]


class QueryPerformanceBehavior(IPipelineBehavior[Any, Any]):
    """Emit structured query execution telemetry and slow-query evidence."""

    def __init__(
        self,
        *,
        slow_threshold_ms: float = 300.0,
        observation_handler: QueryObservationHandler | None = None,
    ) -> None:
        self._slow_threshold_ms = max(float(slow_threshold_ms), 1.0)
        self._observation_handler = observation_handler

    async def handle(self, request: Any, next_handler: QueryNextHandler) -> Any:
        query_type = type(request).__name__
        trace_id = getattr(request, 'trace_id', None) or TraceCtx.get_id() or ''
        request_id = getattr(request, 'request_id', None) or TraceCtx.get_id() or ''

        started_at = time.perf_counter()
        try:
            result = await next_handler()
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            observation = {
                'query_type': query_type,
                'duration_ms': duration_ms,
                'trace_id': trace_id,
                'request_id': request_id,
                'is_slow': duration_ms >= self._slow_threshold_ms,
                'success': False,
                'status': 'failed',
            }
            self._record_observation(observation)
            logger.bind(
                event='cqrs_query',
                **observation,
                slow_threshold_ms=self._slow_threshold_ms,
            ).exception('cqrs_query_failed')
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        observation = {
            'query_type': query_type,
            'duration_ms': duration_ms,
            'trace_id': trace_id,
            'request_id': request_id,
            'is_slow': duration_ms >= self._slow_threshold_ms,
            'success': True,
            'status': 'ok',
        }
        self._record_observation(observation)
        query_logger = logger.bind(
            event='cqrs_query',
            **observation,
            slow_threshold_ms=self._slow_threshold_ms,
        )
        if observation['is_slow']:
            query_logger.warning('cqrs_query_slow')
        else:
            query_logger.info('cqrs_query_executed')
        return result

    def _record_observation(self, observation: dict[str, Any]) -> None:
        if self._observation_handler is None:
            return
        try:
            self._observation_handler(observation)
        except Exception:
            logger.bind(
                event='cqrs_query',
                observation=observation,
            ).exception('cqrs_query_observation_handler_failed')


def build_default_query_behaviors() -> tuple[IPipelineBehavior[Any, Any], ...]:
    """Build default query pipeline behaviors."""

    return (QueryPerformanceBehavior(),)
