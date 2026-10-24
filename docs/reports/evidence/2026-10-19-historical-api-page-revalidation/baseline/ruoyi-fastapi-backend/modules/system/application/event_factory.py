"""Helpers for building standardized system-domain events."""

from __future__ import annotations

from typing import Any

from events.domain_events import DomainEvent


def build_system_event(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    version: int = 1,
) -> DomainEvent:
    normalized_metadata = {
        key: value
        for key, value in (metadata or {}).items()
        if value is not None and value != ''
    }
    return DomainEvent.create(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id or 'unknown',
        payload=payload or {},
        metadata=normalized_metadata,
        version=version,
    )
