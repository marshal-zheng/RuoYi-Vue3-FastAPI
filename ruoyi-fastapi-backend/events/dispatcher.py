"""Background outbox dispatcher with retry/backoff semantics."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from events.errors import EventPublishError
from events.event_bus import InProcessEventBus
from events.metrics import EventMetrics
from events.repositories import EventHistoryRepository, OutboxRepository, outbox_row_to_event
from utils.log_util import logger


@dataclass
class DispatcherHealth:
    running: bool
    last_dispatch_at: datetime | None
    last_error: str | None
    backlog: int
    lag_seconds: float


class OutboxDispatcher:
    """Poll outbox rows, publish through event bus, and update statuses."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Any],
        event_bus: InProcessEventBus,
        metrics: EventMetrics,
        poll_interval_seconds: float = 1.0,
        max_batch_size: int = 100,
        max_retry_count: int = 6,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 60.0,
        backlog_alert_threshold: int = 500,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._metrics = metrics
        self._poll_interval = max(float(poll_interval_seconds), 0.1)
        self._max_batch_size = max(int(max_batch_size), 1)
        self._max_retry_count = max(int(max_retry_count), 1)
        self._base_backoff_seconds = max(float(base_backoff_seconds), 0.1)
        self._max_backoff_seconds = max(float(max_backoff_seconds), self._base_backoff_seconds)
        self._backlog_alert_threshold = max(int(backlog_alert_threshold), 1)

        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._last_dispatch_at: datetime | None = None
        self._last_error: str | None = None
        self._backlog: int = 0
        self._lag_seconds: float = 0.0

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name='outbox-dispatcher')

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def dispatch_batch(self) -> int:
        now = datetime.now(tz=timezone.utc)
        processed = 0

        async with self._session_factory() as session:
            outbox_repo = OutboxRepository(session)
            history_repo = EventHistoryRepository(session)
            rows = await outbox_repo.fetch_dispatch_batch(limit=self._max_batch_size, now=now)

            for row in rows:
                processed += 1
                domain_event = outbox_row_to_event(row)
                trace_id = domain_event.metadata.get('trace_id')

                try:
                    await self._event_bus.publish(domain_event)
                except EventPublishError as exc:
                    retry_count = int(row.retry_count or 0) + 1
                    manual_intervention = retry_count >= self._max_retry_count
                    next_retry_at = None
                    if not manual_intervention:
                        backoff_seconds = min(
                            self._base_backoff_seconds * (2 ** (retry_count - 1)),
                            self._max_backoff_seconds,
                        )
                        next_retry_at = now + timedelta(seconds=backoff_seconds)
                        self._metrics.record_retry(domain_event.event_type)

                    await outbox_repo.mark_failed(
                        row,
                        error=str(exc),
                        retry_count=retry_count,
                        next_retry_at=next_retry_at,
                        manual_intervention=manual_intervention,
                    )
                    self._metrics.record_dispatch_failure(domain_event.event_type)
                    logger.bind(
                        event='outbox_dispatch_failed',
                        event_id=domain_event.event_id,
                        event_type=domain_event.event_type,
                        retry_count=retry_count,
                        manual_intervention=manual_intervention,
                        trace_id=trace_id,
                    ).error('outbox_dispatch_failed')
                    continue
                except Exception as exc:  # pragma: no cover - defensive branch
                    retry_count = int(row.retry_count or 0) + 1
                    manual_intervention = retry_count >= self._max_retry_count
                    next_retry_at = None
                    if not manual_intervention:
                        backoff_seconds = min(
                            self._base_backoff_seconds * (2 ** (retry_count - 1)),
                            self._max_backoff_seconds,
                        )
                        next_retry_at = now + timedelta(seconds=backoff_seconds)
                        self._metrics.record_retry(domain_event.event_type)
                    await outbox_repo.mark_failed(
                        row,
                        error=str(exc),
                        retry_count=retry_count,
                        next_retry_at=next_retry_at,
                        manual_intervention=manual_intervention,
                    )
                    self._metrics.record_dispatch_failure(domain_event.event_type)
                    logger.bind(
                        event='outbox_dispatch_error',
                        event_id=domain_event.event_id,
                        event_type=domain_event.event_type,
                        retry_count=retry_count,
                        trace_id=trace_id,
                    ).exception('outbox_dispatch_error')
                    continue

                await outbox_repo.mark_published(row, published_at=now)
                await history_repo.append(domain_event, published_at=now)
                self._metrics.record_dispatch_success(domain_event.event_type)
                logger.bind(
                    event='outbox_dispatch_published',
                    event_id=domain_event.event_id,
                    event_type=domain_event.event_type,
                    trace_id=trace_id,
                ).info('outbox_dispatch_published')

            await session.commit()

        await self.refresh_backlog_snapshot()
        if self._backlog >= self._backlog_alert_threshold:
            logger.bind(
                event='outbox_backlog_alert',
                backlog=self._backlog,
                threshold=self._backlog_alert_threshold,
            ).warning('outbox_backlog_above_threshold')

        if processed > 0:
            self._last_dispatch_at = now
        return processed

    async def refresh_backlog_snapshot(self) -> None:
        async with self._session_factory() as session:
            outbox_repo = OutboxRepository(session)
            backlog = await outbox_repo.count_backlog()
            oldest = await outbox_repo.oldest_backlog_time()

        lag_seconds = 0.0
        if oldest is not None:
            now = datetime.now(tz=timezone.utc)
            reference = oldest
            if reference.tzinfo is None:
                reference = reference.replace(tzinfo=timezone.utc)
            lag_seconds = max((now - reference).total_seconds(), 0.0)

        self._backlog = backlog
        self._lag_seconds = lag_seconds

    def health_snapshot(self) -> DispatcherHealth:
        task_running = self._task is not None and not self._task.done()
        return DispatcherHealth(
            running=task_running,
            last_dispatch_at=self._last_dispatch_at,
            last_error=self._last_error,
            backlog=self._backlog,
            lag_seconds=self._lag_seconds,
        )

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                processed = await self.dispatch_batch()
                self._last_error = None
                sleep_for = self._poll_interval if processed == 0 else 0.05
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive branch
                self._last_error = str(exc)
                logger.bind(event='outbox_dispatch_loop_error').exception('outbox_dispatch_loop_error')
                sleep_for = self._poll_interval

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_for)
            except TimeoutError:
                continue
