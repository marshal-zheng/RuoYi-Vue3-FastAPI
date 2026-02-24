"""Handler registry for typed domain events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from events.domain_events import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None]]


@dataclass(frozen=True)
class RegisteredHandler:
    event_type: str
    handler_name: str
    handler: EventHandler


class EventHandlerRegistry:
    """In-memory event-handler mapping."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[RegisteredHandler]] = defaultdict(list)

    def register(self, event_type: str, handler: EventHandler, *, handler_name: str | None = None) -> None:
        if not event_type:
            raise ValueError('event_type must not be empty')
        name = handler_name or getattr(handler, '__name__', handler.__class__.__name__)
        registrations = self._handlers[event_type]
        if any(item.handler_name == name for item in registrations):
            return
        registrations.append(RegisteredHandler(event_type=event_type, handler_name=name, handler=handler))

    def handlers_for(self, event_type: str) -> tuple[RegisteredHandler, ...]:
        return tuple(self._handlers.get(event_type, ()))

    def snapshot(self) -> dict[str, tuple[str, ...]]:
        return {
            event_type: tuple(item.handler_name for item in registrations)
            for event_type, registrations in self._handlers.items()
        }
