"""Domain event contract and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

from events.errors import EventPayloadTooLargeError

MAX_EVENT_PAYLOAD_BYTES = 64 * 1024


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _payload_size(payload: Mapping[str, Any]) -> int:
    dumped = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return len(dumped.encode('utf-8'))


@dataclass(frozen=True)
class DomainEvent:
    """Immutable domain event with versioned payload contract."""

    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    occurred_at: datetime
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any]
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        version: int = 1,
    ) -> 'DomainEvent':
        if not event_type:
            raise ValueError('event_type must not be empty')
        if not aggregate_type:
            raise ValueError('aggregate_type must not be empty')
        if not aggregate_id:
            raise ValueError('aggregate_id must not be empty')

        normalized_payload = dict(payload or {})
        payload_size = _payload_size(normalized_payload)
        if payload_size > MAX_EVENT_PAYLOAD_BYTES:
            raise EventPayloadTooLargeError(payload_size=payload_size, max_bytes=MAX_EVENT_PAYLOAD_BYTES)

        normalized_metadata = dict(metadata or {})
        normalized_metadata.setdefault('schema_version', int(version))

        return cls(
            event_id=uuid4().hex,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            occurred_at=_utc_now(),
            payload=_freeze_mapping(normalized_payload),
            metadata=_freeze_mapping(normalized_metadata),
            version=int(version),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'aggregate_type': self.aggregate_type,
            'aggregate_id': self.aggregate_id,
            'occurred_at': self.occurred_at.isoformat(),
            'payload': dict(self.payload),
            'metadata': dict(self.metadata),
            'version': self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'DomainEvent':
        occurred_at_raw = data.get('occurred_at')
        if isinstance(occurred_at_raw, datetime):
            occurred_at = occurred_at_raw
        elif isinstance(occurred_at_raw, str):
            occurred_at = datetime.fromisoformat(occurred_at_raw)
        else:
            occurred_at = _utc_now()

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        return cls(
            event_id=str(data['event_id']),
            event_type=str(data['event_type']),
            aggregate_type=str(data['aggregate_type']),
            aggregate_id=str(data['aggregate_id']),
            occurred_at=occurred_at,
            payload=_freeze_mapping(data.get('payload') or {}),
            metadata=_freeze_mapping(data.get('metadata') or {}),
            version=int(data.get('version', 1)),
        )
