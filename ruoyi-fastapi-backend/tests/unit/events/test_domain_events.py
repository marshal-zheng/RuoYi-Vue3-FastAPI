from __future__ import annotations

import pytest

from events.domain_events import DomainEvent
from events.errors import EventPayloadTooLargeError


def test_domain_event_create_generates_required_fields() -> None:
    event = DomainEvent.create(
        event_type='system.user.created',
        aggregate_type='user',
        aggregate_id='u-1',
        payload={'userId': 1},
        metadata={'trace_id': 'trace-1'},
    )

    assert event.event_id
    assert event.event_type == 'system.user.created'
    assert event.aggregate_type == 'user'
    assert event.aggregate_id == 'u-1'
    assert event.version == 1
    assert dict(event.payload) == {'userId': 1}
    assert dict(event.metadata)['trace_id'] == 'trace-1'


def test_domain_event_create_rejects_payload_over_limit() -> None:
    with pytest.raises(EventPayloadTooLargeError):
        DomainEvent.create(
            event_type='system.user.created',
            aggregate_type='user',
            aggregate_id='u-1',
            payload={'blob': 'x' * (65 * 1024)},
        )


def test_domain_event_roundtrip_dict() -> None:
    event = DomainEvent.create(
        event_type='system.user.deleted',
        aggregate_type='user',
        aggregate_id='u-2',
        payload={'user_ids': [2]},
        metadata={'request_id': 'req-2'},
        version=3,
    )

    restored = DomainEvent.from_dict(event.to_dict())

    assert restored.event_id == event.event_id
    assert restored.event_type == event.event_type
    assert restored.aggregate_type == event.aggregate_type
    assert restored.aggregate_id == event.aggregate_id
    assert dict(restored.payload) == dict(event.payload)
    assert dict(restored.metadata) == dict(event.metadata)
    assert restored.version == 3
