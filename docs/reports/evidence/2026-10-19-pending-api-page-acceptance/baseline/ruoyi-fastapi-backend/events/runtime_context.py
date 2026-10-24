"""Global accessor for event runtime used by command behaviors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from events.runtime import EventSystemRuntime


_EVENT_RUNTIME: 'EventSystemRuntime | None' = None


def set_event_runtime(runtime: 'EventSystemRuntime | None') -> None:
    global _EVENT_RUNTIME
    _EVENT_RUNTIME = runtime


def get_event_runtime() -> 'EventSystemRuntime | None':
    return _EVENT_RUNTIME
