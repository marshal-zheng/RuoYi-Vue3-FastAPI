from __future__ import annotations

from collections import defaultdict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from events.dispatcher import OutboxDispatcher
from events.domain_events import DomainEvent
from events.errors import EventPublishError
from events.event_bus import InProcessEventBus
from events.handler_registry import EventHandlerRegistry
from events.metrics import EventMetrics
from events.models import EventHistoryDO, OutboxEventDO
from events.repositories import OutboxRepository


@pytest.fixture
def session_factory(test_engine):
    session_maker = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False,
    )

    def _factory():
        return session_maker()

    return _factory


@pytest.mark.asyncio
async def test_event_bus_isolates_handler_failures_and_keeps_idempotency(session_factory) -> None:
    registry = EventHandlerRegistry()
    metrics = EventMetrics()
    bus = InProcessEventBus(
        registry=registry,
        session_factory=session_factory,
        metrics=metrics,
    )

    calls = defaultdict(int)

    async def success_handler(event: DomainEvent) -> None:
        _ = event
        calls['success'] += 1

    async def fail_handler(event: DomainEvent) -> None:
        _ = event
        calls['fail'] += 1
        raise RuntimeError('boom')

    bus.subscribe('system.user.deleted', success_handler, handler_name='success_handler')
    bus.subscribe('system.user.deleted', fail_handler, handler_name='fail_handler')

    event = DomainEvent.create(
        event_type='system.user.deleted',
        aggregate_type='user',
        aggregate_id='u-1',
        payload={'user_ids': [1]},
    )

    with pytest.raises(EventPublishError):
        await bus.publish(event)

    assert calls['success'] == 1
    assert calls['fail'] == 1

    with pytest.raises(EventPublishError):
        await bus.publish(event)

    assert calls['success'] == 1  # success handler should be skipped via idempotency log
    assert calls['fail'] == 2


@pytest.mark.asyncio
async def test_outbox_dispatcher_publishes_and_persists_history(session_factory) -> None:
    registry = EventHandlerRegistry()
    metrics = EventMetrics()
    bus = InProcessEventBus(registry=registry, session_factory=session_factory, metrics=metrics)
    dispatcher = OutboxDispatcher(
        session_factory=session_factory,
        event_bus=bus,
        metrics=metrics,
        poll_interval_seconds=1.0,
        max_batch_size=10,
        max_retry_count=3,
    )

    event = DomainEvent.create(
        event_type='system.menu.created',
        aggregate_type='menu',
        aggregate_id='m-1',
        payload={'menuId': 1},
    )

    async with session_factory() as session:
        outbox_repo = OutboxRepository(session)
        await outbox_repo.add_events((event,))
        await session.commit()

    processed = await dispatcher.dispatch_batch()
    assert processed == 1

    async with session_factory() as session:
        outbox_row = (await session.execute(select(OutboxEventDO).where(OutboxEventDO.event_id == event.event_id))).scalar_one()
        history_row = (await session.execute(select(EventHistoryDO).where(EventHistoryDO.event_id == event.event_id))).scalar_one()

    assert outbox_row.status == 'published'
    assert outbox_row.published_at is not None
    assert history_row.event_type == 'system.menu.created'


@pytest.mark.asyncio
async def test_outbox_dispatcher_marks_manual_intervention_after_retry_exhausted(session_factory) -> None:
    registry = EventHandlerRegistry()
    metrics = EventMetrics()
    bus = InProcessEventBus(registry=registry, session_factory=session_factory, metrics=metrics)

    async def always_fail_handler(event: DomainEvent) -> None:
        _ = event
        raise RuntimeError('handler failed')

    bus.subscribe('system.user.deleted', always_fail_handler, handler_name='always_fail_handler')

    dispatcher = OutboxDispatcher(
        session_factory=session_factory,
        event_bus=bus,
        metrics=metrics,
        poll_interval_seconds=1.0,
        max_batch_size=10,
        max_retry_count=1,
    )

    event = DomainEvent.create(
        event_type='system.user.deleted',
        aggregate_type='user',
        aggregate_id='u-2',
        payload={'user_ids': [2]},
    )

    async with session_factory() as session:
        outbox_repo = OutboxRepository(session)
        await outbox_repo.add_events((event,))
        await session.commit()

    processed = await dispatcher.dispatch_batch()
    assert processed == 1

    async with session_factory() as session:
        outbox_row = (await session.execute(select(OutboxEventDO).where(OutboxEventDO.event_id == event.event_id))).scalar_one()

    assert outbox_row.status == 'manual_intervention'
    assert outbox_row.retry_count == 1
