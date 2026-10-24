"""Development-only SSE event broker for dev menu hot reload."""

from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from config.env import DevManagedDataHotReconcileConfig


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class DevMenuSseEvent:
    event: str
    data: dict[str, Any]
    event_id: int | None = None

    def encode(self) -> bytes:
        lines = [f'event: {self.event}']
        if self.event_id is not None:
            lines.append(f'id: {self.event_id}')
        lines.append(f'data: {json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))}')
        return ('\n'.join(lines) + '\n\n').encode('utf-8')


@dataclass
class SseSubscriber:
    subscriber_id: int
    user_id: int | None
    queue: asyncio.Queue[DevMenuSseEvent | None]
    connected_at: datetime


class DevMenuEventBroker:
    """In-process SSE broker for development-only menu refresh events."""

    def __init__(
        self,
        *,
        heartbeat_seconds: int | None = None,
        replay_buffer_size: int | None = None,
    ) -> None:
        self._heartbeat_seconds = max(
            int(
                heartbeat_seconds
                if heartbeat_seconds is not None
                else DevManagedDataHotReconcileConfig.dev_managed_data_sse_heartbeat_seconds
            ),
            1,
        )
        self._replay_buffer_size = max(
            int(
                replay_buffer_size
                if replay_buffer_size is not None
                else DevManagedDataHotReconcileConfig.dev_managed_data_sse_replay_buffer_size
            ),
            0,
        )
        self._subscribers: dict[int, SseSubscriber] = {}
        self._subscriber_sequence = 0
        self._event_sequence = 0
        self._replay_buffer: deque[DevMenuSseEvent] = deque(maxlen=self._replay_buffer_size or None)
        self._closed = False

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    @property
    def last_event_id(self) -> int:
        return self._event_sequence

    @property
    def replay_events(self) -> tuple[DevMenuSseEvent, ...]:
        return tuple(self._replay_buffer)

    async def stream(
        self,
        *,
        user_id: int | None,
        last_event_id: int | None = None,
    ):
        async for event in self.subscribe(user_id=user_id, last_event_id=last_event_id):
            yield event.encode()

    async def subscribe(
        self,
        *,
        user_id: int | None,
        last_event_id: int | None = None,
    ):
        if self._closed:
            return

        subscriber = self._register_subscriber(user_id=user_id)
        try:
            yield DevMenuSseEvent(
                event='ready',
                data={'connectedAt': subscriber.connected_at.isoformat()},
            )
            for replay_event in self._replay_events_after(last_event_id):
                yield replay_event

            while True:
                try:
                    queued_event = await asyncio.wait_for(
                        subscriber.queue.get(),
                        timeout=float(self._heartbeat_seconds),
                    )
                except TimeoutError:
                    yield DevMenuSseEvent(event='heartbeat', data={'ts': _utcnow().isoformat()})
                    continue

                if queued_event is None:
                    break
                yield queued_event
        finally:
            self._subscribers.pop(subscriber.subscriber_id, None)

    def publish_menu_changed(
        self,
        *,
        trigger: str,
        compiled_checksum: str | None,
        synced_at: datetime | None,
    ) -> int:
        self._event_sequence += 1
        event = DevMenuSseEvent(
            event='menu_changed',
            event_id=self._event_sequence,
            data={
                'trigger': trigger,
                'compiledChecksum': compiled_checksum,
                'syncedAt': synced_at.isoformat() if synced_at else None,
            },
        )
        if self._replay_buffer_size > 0:
            self._replay_buffer.append(event)

        for subscriber in tuple(self._subscribers.values()):
            subscriber.queue.put_nowait(event)
        return event.event_id or 0

    async def close(self) -> None:
        self._closed = True
        subscribers = tuple(self._subscribers.values())
        self._subscribers.clear()
        for subscriber in subscribers:
            subscriber.queue.put_nowait(None)

    def _register_subscriber(self, *, user_id: int | None) -> SseSubscriber:
        self._subscriber_sequence += 1
        subscriber = SseSubscriber(
            subscriber_id=self._subscriber_sequence,
            user_id=user_id,
            queue=asyncio.Queue(),
            connected_at=_utcnow(),
        )
        self._subscribers[subscriber.subscriber_id] = subscriber
        return subscriber

    def _replay_events_after(self, last_event_id: int | None) -> tuple[DevMenuSseEvent, ...]:
        if last_event_id is None:
            return ()
        return tuple(
            event
            for event in self._replay_buffer
            if event.event_id is not None and event.event_id > last_event_id
        )
