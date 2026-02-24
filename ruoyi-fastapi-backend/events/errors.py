"""Event subsystem errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class EventError(RuntimeError):
    """Base event runtime error."""


class EventPayloadTooLargeError(EventError):
    """Raised when event payload exceeds hard size limit."""

    def __init__(self, *, payload_size: int, max_bytes: int):
        super().__init__(f'event payload too large: {payload_size} bytes > {max_bytes} bytes')
        self.payload_size = payload_size
        self.max_bytes = max_bytes


@dataclass(frozen=True)
class HandlerFailure:
    handler_name: str
    error: str


class EventPublishError(EventError):
    """Raised when one or more handlers failed while publishing an event."""

    def __init__(self, *, event_id: str, event_type: str, failures: Sequence[HandlerFailure]):
        summary = ', '.join(f'{item.handler_name}: {item.error}' for item in failures)
        super().__init__(f'event publish failed for {event_type}({event_id}): {summary}')
        self.event_id = event_id
        self.event_type = event_type
        self.failures = tuple(failures)
