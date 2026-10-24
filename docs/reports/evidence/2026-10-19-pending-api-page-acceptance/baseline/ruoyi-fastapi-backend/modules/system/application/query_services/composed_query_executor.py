"""Composable query executor with bounded timeout and rollback-friendly fallback."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from utils.log_util import logger

QueryBranchFactory = Callable[[], Awaitable[Any]]


class ComposedQueryTimeoutError(TimeoutError):
    """Raised when composed query branches exceed configured timeout."""

    def __init__(self, query_name: str, timeout_seconds: float, branch_names: tuple[str, ...]):
        self.query_name = query_name
        self.timeout_seconds = timeout_seconds
        self.branch_names = branch_names
        super().__init__(
            f'Composed query {query_name!r} timed out after {timeout_seconds:.3f}s: {", ".join(branch_names)}'
        )


class ComposedQueryExecutor:
    """Execute independent query branches in parallel with deterministic timeout control."""

    def __init__(self, query_name: str, *, timeout_seconds: float = 0.35):
        if timeout_seconds <= 0:
            raise ValueError('timeout_seconds must be greater than 0')
        self._query_name = query_name
        self._timeout_seconds = float(timeout_seconds)

    async def run(
        self,
        branches: dict[str, QueryBranchFactory],
        *,
        trace_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Run named branches concurrently and return name->result mapping."""
        if not branches:
            return {}

        started_at = time.perf_counter()
        branch_names = tuple(branches.keys())
        tasks = {
            name: asyncio.create_task(factory(), name=f'{self._query_name}:{name}')
            for name, factory in branches.items()
        }

        try:
            async with asyncio.timeout(self._timeout_seconds):
                values = await asyncio.gather(*(tasks[name] for name in branch_names))
        except TimeoutError as exc:
            await self._cancel_tasks(tasks.values())
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            logger.bind(
                event='cqrs_composed_query',
                query_name=self._query_name,
                branch_names=branch_names,
                timeout_seconds=self._timeout_seconds,
                duration_ms=duration_ms,
                trace_id=trace_id or '',
                request_id=request_id or '',
                degraded=True,
            ).warning('cqrs_composed_query_timeout')
            raise ComposedQueryTimeoutError(self._query_name, self._timeout_seconds, branch_names) from exc
        except Exception:
            await self._cancel_tasks(tasks.values())
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            logger.bind(
                event='cqrs_composed_query',
                query_name=self._query_name,
                branch_names=branch_names,
                timeout_seconds=self._timeout_seconds,
                duration_ms=duration_ms,
                trace_id=trace_id or '',
                request_id=request_id or '',
                degraded=False,
            ).exception('cqrs_composed_query_failed')
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        logger.bind(
            event='cqrs_composed_query',
            query_name=self._query_name,
            branch_names=branch_names,
            timeout_seconds=self._timeout_seconds,
            duration_ms=duration_ms,
            trace_id=trace_id or '',
            request_id=request_id or '',
            degraded=False,
        ).info('cqrs_composed_query_executed')
        return dict(zip(branch_names, values, strict=True))

    @staticmethod
    async def _cancel_tasks(tasks: Any) -> None:
        task_list = tuple(tasks)
        for task in task_list:
            if not task.done():
                task.cancel()
        if task_list:
            await asyncio.gather(*task_list, return_exceptions=True)
