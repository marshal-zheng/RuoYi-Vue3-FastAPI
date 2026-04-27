"""Repositories for outbox dispatch, history queries, and idempotency logs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from events.domain_events import DomainEvent
from events.models import EventConsumptionLogDO, EventHistoryDO, OutboxEventDO

PENDING_STATUSES = ('pending', 'retrying')


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _serialize_mapping(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def _deserialize_mapping(data: str | None) -> dict[str, Any]:
    if not data:
        return {}
    loaded = json.loads(data)
    return loaded if isinstance(loaded, dict) else {}


def outbox_row_to_event(row: OutboxEventDO) -> DomainEvent:
    return DomainEvent.from_dict(
        {
            'event_id': row.event_id,
            'event_type': row.event_type,
            'aggregate_type': row.aggregate_type,
            'aggregate_id': row.aggregate_id,
            'occurred_at': row.occurred_at,
            'payload': _deserialize_mapping(row.payload),
            'metadata': _deserialize_mapping(row.event_metadata),
            'version': row.event_version,
        }
    )


@dataclass
class EventHistoryFilters:
    aggregate_id: str | None = None
    aggregate_type: str | None = None
    event_type: str | None = None
    begin_time: datetime | None = None
    end_time: datetime | None = None
    page: int = 1
    page_size: int = 20


class OutboxRepository:
    """Persistence access for transactional outbox records."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_events(self, events: Sequence[DomainEvent]) -> list[OutboxEventDO]:
        rows: list[OutboxEventDO] = []
        for event in events:
            row = OutboxEventDO(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.occurred_at,
                payload=_serialize_mapping(dict(event.payload)),
                event_metadata=_serialize_mapping(dict(event.metadata)),
                event_version=event.version,
                status='pending',
                next_retry_at=event.occurred_at,
                trace_id=str(event.metadata.get('trace_id', '')) or None,
            )
            self._session.add(row)
            rows.append(row)
        if rows:
            await self._session.flush()
        return rows

    async def fetch_dispatch_batch(self, *, limit: int, now: datetime | None = None) -> list[OutboxEventDO]:
        dispatch_time = now or _utc_now()
        stmt = (
            select(OutboxEventDO)
            .where(
                and_(
                    OutboxEventDO.status.in_(PENDING_STATUSES),
                    or_(OutboxEventDO.next_retry_at.is_(None), OutboxEventDO.next_retry_at <= dispatch_time),
                )
            )
            .order_by(OutboxEventDO.occurred_at.asc())
            .limit(max(int(limit), 1))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_published(self, row: OutboxEventDO, *, published_at: datetime) -> None:
        row.status = 'published'
        row.published_at = published_at
        row.last_error = None
        row.next_retry_at = None
        await self._session.flush()

    async def mark_failed(
        self,
        row: OutboxEventDO,
        *,
        error: str,
        retry_count: int,
        next_retry_at: datetime | None,
        manual_intervention: bool,
    ) -> None:
        row.retry_count = int(retry_count)
        row.last_error = error[:5000]
        row.next_retry_at = next_retry_at
        row.status = 'manual_intervention' if manual_intervention else 'retrying'
        await self._session.flush()

    async def count_backlog(self) -> int:
        stmt = select(func.count(OutboxEventDO.id)).where(OutboxEventDO.status.in_(('pending', 'retrying', 'manual_intervention')))
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def oldest_backlog_time(self) -> datetime | None:
        stmt = select(func.min(OutboxEventDO.occurred_at)).where(
            OutboxEventDO.status.in_(('pending', 'retrying', 'manual_intervention'))
        )
        result = await self._session.execute(stmt)
        value = result.scalar()
        return value if isinstance(value, datetime) else None


class EventHistoryRepository:
    """Persistence access for published event history."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, event: DomainEvent, *, published_at: datetime, source_status: str = 'published') -> EventHistoryDO:
        row = EventHistoryDO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            occurred_at=event.occurred_at,
            published_at=published_at,
            payload=_serialize_mapping(dict(event.payload)),
            event_metadata=_serialize_mapping(dict(event.metadata)),
            event_version=event.version,
            trace_id=str(event.metadata.get('trace_id', '')) or None,
            source_status=source_status,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list(self, filters: EventHistoryFilters) -> tuple[list[EventHistoryDO], int]:
        conditions = []
        if filters.aggregate_id:
            conditions.append(EventHistoryDO.aggregate_id == filters.aggregate_id)
        if filters.aggregate_type:
            conditions.append(EventHistoryDO.aggregate_type == filters.aggregate_type)
        if filters.event_type:
            conditions.append(EventHistoryDO.event_type == filters.event_type)
        if filters.begin_time is not None:
            conditions.append(EventHistoryDO.occurred_at >= filters.begin_time)
        if filters.end_time is not None:
            conditions.append(EventHistoryDO.occurred_at <= filters.end_time)

        base_stmt = select(EventHistoryDO)
        count_stmt = select(func.count(EventHistoryDO.id))
        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        page = max(int(filters.page), 1)
        page_size = max(min(int(filters.page_size), 200), 1)
        offset = (page - 1) * page_size

        stmt = (
            base_stmt.order_by(EventHistoryDO.occurred_at.desc(), EventHistoryDO.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        total = int((await self._session.execute(count_stmt)).scalar() or 0)
        return rows, total

    async def list_for_replay(self, filters: EventHistoryFilters, *, limit: int = 500) -> list[EventHistoryDO]:
        conditions = []
        if filters.aggregate_id:
            conditions.append(EventHistoryDO.aggregate_id == filters.aggregate_id)
        if filters.aggregate_type:
            conditions.append(EventHistoryDO.aggregate_type == filters.aggregate_type)
        if filters.event_type:
            conditions.append(EventHistoryDO.event_type == filters.event_type)
        if filters.begin_time is not None:
            conditions.append(EventHistoryDO.occurred_at >= filters.begin_time)
        if filters.end_time is not None:
            conditions.append(EventHistoryDO.occurred_at <= filters.end_time)

        stmt = select(EventHistoryDO)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(EventHistoryDO.occurred_at.asc(), EventHistoryDO.id.asc()).limit(max(int(limit), 1))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


def history_row_to_event(row: EventHistoryDO) -> DomainEvent:
    return DomainEvent.from_dict(
        {
            'event_id': row.event_id,
            'event_type': row.event_type,
            'aggregate_type': row.aggregate_type,
            'aggregate_id': row.aggregate_id,
            'occurred_at': row.occurred_at,
            'payload': _deserialize_mapping(row.payload),
            'metadata': _deserialize_mapping(row.event_metadata),
            'version': row.event_version,
        }
    )


class EventConsumptionRepository:
    """Persistence access for idempotent handler-consumption logs."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, event_id: str, handler_name: str) -> EventConsumptionLogDO | None:
        stmt = select(EventConsumptionLogDO).where(
            EventConsumptionLogDO.event_id == event_id,
            EventConsumptionLogDO.handler_name == handler_name,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def mark_result(
        self,
        *,
        event_id: str,
        handler_name: str,
        success: bool,
        error: str | None = None,
    ) -> EventConsumptionLogDO:
        record = await self.get(event_id, handler_name)
        now = _utc_now()
        if record is None:
            record = EventConsumptionLogDO(
                event_id=event_id,
                handler_name=handler_name,
                status='success' if success else 'failed',
                attempts=1,
                last_error=error,
                processed_at=now,
            )
            self._session.add(record)
        else:
            record.attempts = int(record.attempts or 0) + 1
            record.status = 'success' if success else 'failed'
            record.last_error = None if success else (error or '')[:5000]
            record.processed_at = now
        await self._session.flush()
        return record
