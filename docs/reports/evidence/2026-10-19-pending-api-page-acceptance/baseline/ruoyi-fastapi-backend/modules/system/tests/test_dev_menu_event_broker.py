from __future__ import annotations

from datetime import UTC, datetime

import pytest

from modules.system.runtime.dev_menu_event_broker import DevMenuEventBroker


@pytest.mark.asyncio
async def test_event_broker_streams_ready_menu_changed_and_heartbeat() -> None:
    broker = DevMenuEventBroker(heartbeat_seconds=1, replay_buffer_size=1)
    stream = broker.subscribe(user_id=1)

    ready_event = await anext(stream)
    assert ready_event.event == 'ready'
    assert 'connectedAt' in ready_event.data
    assert broker.subscriber_count == 1

    event_id = broker.publish_menu_changed(
        trigger='file_change',
        compiled_checksum='checksum-1',
        synced_at=datetime(2026, 4, 6, 12, 0, 1, tzinfo=UTC),
    )
    menu_changed_event = await anext(stream)
    assert menu_changed_event.event == 'menu_changed'
    assert menu_changed_event.event_id == event_id
    assert menu_changed_event.data['compiledChecksum'] == 'checksum-1'

    heartbeat_event = await anext(stream)
    assert heartbeat_event.event == 'heartbeat'
    assert 'ts' in heartbeat_event.data

    await broker.close()
    await stream.aclose()
    assert broker.subscriber_count == 0


@pytest.mark.asyncio
async def test_event_broker_replays_buffered_menu_changed_event() -> None:
    broker = DevMenuEventBroker(heartbeat_seconds=1, replay_buffer_size=1)
    first_event_id = broker.publish_menu_changed(
        trigger='file_change',
        compiled_checksum='checksum-1',
        synced_at=datetime(2026, 4, 6, 12, 0, 1, tzinfo=UTC),
    )
    second_event_id = broker.publish_menu_changed(
        trigger='manual',
        compiled_checksum='checksum-2',
        synced_at=datetime(2026, 4, 6, 12, 0, 2, tzinfo=UTC),
    )

    stream = broker.subscribe(user_id=1, last_event_id=first_event_id)
    ready_event = await anext(stream)
    replay_event = await anext(stream)

    assert ready_event.event == 'ready'
    assert replay_event.event == 'menu_changed'
    assert replay_event.event_id == second_event_id
    assert replay_event.data['trigger'] == 'manual'

    await stream.aclose()
    await broker.close()
