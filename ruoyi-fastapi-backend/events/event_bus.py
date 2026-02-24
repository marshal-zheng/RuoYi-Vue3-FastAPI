"""In-process event bus implementation with idempotent consumption."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from events.domain_events import DomainEvent
from events.errors import EventPublishError, HandlerFailure
from events.handler_registry import EventHandler, EventHandlerRegistry
from events.metrics import EventMetrics
from events.repositories import EventConsumptionRepository
from utils.log_util import logger


@dataclass(frozen=True)
class PublishResult:
    event_id: str
    event_type: str
    handlers_total: int
    handlers_succeeded: int
    handlers_failed: int
    handlers_skipped: int


class InProcessEventBus:
    """In-process publish/subscribe bus with handler-failure isolation."""

    def __init__(
        self,
        *,
        registry: EventHandlerRegistry,
        session_factory: Callable[[], Any],
        metrics: EventMetrics,
    ) -> None:
        self._registry = registry
        self._session_factory = session_factory
        self._metrics = metrics

    def subscribe(self, event_type: str, handler: EventHandler, *, handler_name: str | None = None) -> None:
        self._registry.register(event_type, handler, handler_name=handler_name)

    async def publish(self, event: DomainEvent) -> PublishResult:
        registrations = self._registry.handlers_for(event.event_type)
        if not registrations:
            return PublishResult(
                event_id=event.event_id,
                event_type=event.event_type,
                handlers_total=0,
                handlers_succeeded=0,
                handlers_failed=0,
                handlers_skipped=0,
            )

        failures: list[HandlerFailure] = []
        succeeded = 0
        skipped = 0

        async with self._session_factory() as session:
            consumption_repo = EventConsumptionRepository(session)
            for registration in registrations:
                record = await consumption_repo.get(event.event_id, registration.handler_name)
                if record is not None and record.status == 'success':
                    skipped += 1
                    continue

                try:
                    await registration.handler(event)
                except Exception as exc:  # pragma: no cover - behavior verified via integration path
                    error_message = str(exc)
                    failures.append(HandlerFailure(handler_name=registration.handler_name, error=error_message))
                    await consumption_repo.mark_result(
                        event_id=event.event_id,
                        handler_name=registration.handler_name,
                        success=False,
                        error=error_message,
                    )
                    self._metrics.record_handler_failure(event.event_type, registration.handler_name)
                    logger.bind(
                        event='event_handler_failed',
                        event_id=event.event_id,
                        event_type=event.event_type,
                        handler=registration.handler_name,
                        trace_id=event.metadata.get('trace_id'),
                    ).error('event_handler_failed')
                    continue

                await consumption_repo.mark_result(
                    event_id=event.event_id,
                    handler_name=registration.handler_name,
                    success=True,
                )
                self._metrics.record_handler_success(event.event_type, registration.handler_name)
                succeeded += 1

            await session.commit()

        if failures:
            raise EventPublishError(event_id=event.event_id, event_type=event.event_type, failures=failures)

        return PublishResult(
            event_id=event.event_id,
            event_type=event.event_type,
            handlers_total=len(registrations),
            handlers_succeeded=succeeded,
            handlers_failed=0,
            handlers_skipped=skipped,
        )
