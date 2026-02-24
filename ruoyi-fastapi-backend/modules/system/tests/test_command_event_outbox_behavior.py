from __future__ import annotations

from dataclasses import dataclass

import pytest

from events.domain_events import DomainEvent
from events.runtime_context import set_event_runtime
from modules.system.application import CommandResult, HandlerRegistry, Mediator
from modules.system.application.behaviors import build_default_command_behaviors


@dataclass
class _Command:
    query_db: object | None = None


class _Handler:
    async def handle(self, request: _Command) -> CommandResult[dict[str, str]]:
        _ = request
        return CommandResult(
            success=True,
            status='ok',
            data={'message': 'ok'},
            events=(
                DomainEvent.create(
                    event_type='system.user.created',
                    aggregate_type='user',
                    aggregate_id='u-1',
                    payload={'userId': 1},
                ),
            ),
        )


class _RuntimeStub:
    def __init__(self) -> None:
        self.calls: list[tuple[object | None, tuple[object, ...]]] = []

    async def enqueue_events(self, session, events):
        self.calls.append((session, events))
        return len(events)


@pytest.mark.asyncio
async def test_command_event_behavior_enqueues_events_when_runtime_available() -> None:
    runtime = _RuntimeStub()
    set_event_runtime(runtime)

    registry = HandlerRegistry()
    registry.register_command(_Command, _Handler())
    mediator = Mediator(registry, command_behaviors=build_default_command_behaviors())

    try:
        result = await mediator.send(_Command(query_db=object()))
    finally:
        set_event_runtime(None)

    assert result.success is True
    assert result.metadata['event_count'] == 1
    assert result.metadata['outbox_enqueued'] == 1
    assert len(runtime.calls) == 1
