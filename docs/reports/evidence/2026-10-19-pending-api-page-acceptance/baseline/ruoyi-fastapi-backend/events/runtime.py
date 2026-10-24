"""Event system runtime orchestration and API helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from events.dispatcher import OutboxDispatcher
from events.domain_events import DomainEvent
from events.event_bus import InProcessEventBus
from events.handler_registry import EventHandlerRegistry
from events.handlers import ProjectReadSideProjectionHandler
from events.metrics import EventMetrics
from events.repositories import (
    EventHistoryFilters,
    EventHistoryRepository,
    OutboxRepository,
    history_row_to_event,
)
from utils.log_util import logger

if TYPE_CHECKING:
    from container import AppContainer


@dataclass
class ReplayResult:
    replay_id: str
    total: int
    succeeded: int
    failed: int
    failure_samples: list[dict[str, str]]


class EventSystemRuntime:
    """Owns event bus, dispatcher, history APIs, and metrics."""

    def __init__(
        self,
        *,
        container: 'AppContainer',
        poll_interval_seconds: float = 1.0,
        max_batch_size: int = 100,
        max_retry_count: int = 6,
        backlog_alert_threshold: int = 500,
        idle_max_interval_seconds: float = 30.0,
    ) -> None:
        self._container = container
        self.metrics = EventMetrics()
        self.registry = EventHandlerRegistry()
        self.event_bus = InProcessEventBus(
            registry=self.registry,
            session_factory=self._container.create_task_session,
            metrics=self.metrics,
        )
        self.dispatcher = OutboxDispatcher(
            session_factory=self._container.create_task_session,
            event_bus=self.event_bus,
            metrics=self.metrics,
            poll_interval_seconds=poll_interval_seconds,
            max_batch_size=max_batch_size,
            max_retry_count=max_retry_count,
            backlog_alert_threshold=backlog_alert_threshold,
            idle_max_interval_seconds=idle_max_interval_seconds,
        )
        self._register_builtin_handlers()

    async def start(self) -> None:
        await self.dispatcher.start()
        await self.dispatcher.refresh_backlog_snapshot()
        logger.info('Event runtime started')

    async def stop(self) -> None:
        await self.dispatcher.stop()
        logger.info('Event runtime stopped')

    async def enqueue_events(self, session: Any, events: tuple[Any, ...]) -> int:
        if not events:
            return 0
        if not isinstance(session, AsyncSession):
            logger.warning('Skip enqueue events because query_db is not AsyncSession')
            return 0

        normalized_events = [event for event in events if isinstance(event, DomainEvent)]
        if not normalized_events:
            return 0

        repo = OutboxRepository(session)
        await repo.add_events(normalized_events)
        return len(normalized_events)

    async def list_history(self, filters: EventHistoryFilters) -> tuple[list[dict[str, Any]], int]:
        async with self._container.create_task_session() as session:
            repo = EventHistoryRepository(session)
            rows, total = await repo.list(filters)
            payload = [
                {
                    'eventId': row.event_id,
                    'eventType': row.event_type,
                    'aggregateType': row.aggregate_type,
                    'aggregateId': row.aggregate_id,
                    'occurredAt': row.occurred_at,
                    'publishedAt': row.published_at,
                    'version': row.event_version,
                    'traceId': row.trace_id,
                    'sourceStatus': row.source_status,
                }
                for row in rows
            ]
            return payload, total

    async def replay(self, *, filters: EventHistoryFilters, replay_id: str, limit: int = 500) -> ReplayResult:
        failures: list[dict[str, str]] = []
        succeeded = 0

        async with self._container.create_task_session() as session:
            repo = EventHistoryRepository(session)
            rows = await repo.list_for_replay(filters, limit=limit)

        for row in rows:
            event = history_row_to_event(row)
            replayed_metadata = dict(event.metadata)
            replayed_metadata['replay_id'] = replay_id
            replayed_metadata['replayed_at'] = datetime.utcnow().isoformat()
            replayed_event = DomainEvent.from_dict(
                {
                    **event.to_dict(),
                    'metadata': replayed_metadata,
                }
            )

            try:
                await self.event_bus.publish(replayed_event)
            except Exception as exc:  # pragma: no cover - replay failures exposed via API
                failures.append({'eventId': event.event_id, 'error': str(exc)})
                logger.bind(
                    event='event_replay_failed',
                    replay_id=replay_id,
                    event_id=event.event_id,
                    event_type=event.event_type,
                ).error('event_replay_failed')
                continue
            succeeded += 1

        failed = len(failures)
        total = len(rows)
        logger.bind(
            event='event_replay_completed',
            replay_id=replay_id,
            total=total,
            succeeded=succeeded,
            failed=failed,
        ).info('event_replay_completed')

        return ReplayResult(
            replay_id=replay_id,
            total=total,
            succeeded=succeeded,
            failed=failed,
            failure_samples=failures[:20],
        )

    async def health(self) -> dict[str, Any]:
        await self.dispatcher.refresh_backlog_snapshot()
        snapshot = self.dispatcher.health_snapshot()
        return {
            'running': snapshot.running,
            'backlog': snapshot.backlog,
            'lagSeconds': round(snapshot.lag_seconds, 3),
            'lastDispatchAt': snapshot.last_dispatch_at.isoformat() if snapshot.last_dispatch_at else None,
            'lastError': snapshot.last_error,
            'handlers': self.registry.snapshot(),
        }

    async def render_metrics(self) -> str:
        await self.dispatcher.refresh_backlog_snapshot()
        snapshot = self.dispatcher.health_snapshot()
        return self.metrics.render_prometheus(backlog=snapshot.backlog, lag_seconds=snapshot.lag_seconds)

    def _register_builtin_handlers(self) -> None:
        # Cross-module read-side orchestration via project ports.
        self.event_bus.subscribe(
            'system.user.deleted',
            ProjectReadSideProjectionHandler(self._container),
            handler_name='project_read_side_projection',
        )
