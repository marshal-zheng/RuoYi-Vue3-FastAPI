from __future__ import annotations

from dataclasses import dataclass

import pytest

from modules.system.application import (
    CommandResult,
    DuplicateHandlerRegistrationError,
    HandlerNotRegisteredError,
    HandlerRegistry,
    Mediator,
)


@dataclass(frozen=True)
class CreateUserCommand:
    user_name: str


@dataclass(frozen=True)
class ListUsersQuery:
    keyword: str


class CreateUserCommandHandler:
    def __init__(self, trace: list[str] | None = None) -> None:
        self._trace = trace

    async def handle(self, request: CreateUserCommand) -> CommandResult[dict[str, str]]:
        if self._trace is not None:
            self._trace.append('handler')
        return CommandResult(success=True, data={'user_name': request.user_name}, status='created')


class ListUsersQueryHandler:
    async def handle(self, request: ListUsersQuery) -> list[dict[str, str]]:
        return [{'user_name': request.keyword}]


class TraceBehavior:
    def __init__(self, trace: list[str], name: str) -> None:
        self._trace = trace
        self._name = name

    async def handle(self, request, next_handler):
        self._trace.append(f'{self._name}:before:{type(request).__name__}')
        result = await next_handler()
        self._trace.append(f'{self._name}:after:{type(request).__name__}')
        return result


class ShortCircuitBehavior:
    async def handle(self, request, next_handler):
        _ = request
        _ = next_handler
        return CommandResult(success=False, status='blocked')


@pytest.mark.asyncio
async def test_mediator_dispatch_command_and_query() -> None:
    registry = HandlerRegistry()
    registry.register_command(CreateUserCommand, CreateUserCommandHandler())
    registry.register_query(ListUsersQuery, ListUsersQueryHandler())

    mediator = Mediator(registry)

    command_result = await mediator.send(CreateUserCommand(user_name='alice'))
    query_result = await mediator.query(ListUsersQuery(keyword='alice'))

    assert command_result.success is True
    assert command_result.status == 'created'
    assert command_result.data == {'user_name': 'alice'}
    assert query_result == [{'user_name': 'alice'}]


@pytest.mark.asyncio
async def test_mediator_raises_when_handler_missing() -> None:
    registry = HandlerRegistry()
    mediator = Mediator(registry)

    with pytest.raises(HandlerNotRegisteredError, match='CreateUserCommand'):
        await mediator.send(CreateUserCommand(user_name='alice'))

    with pytest.raises(HandlerNotRegisteredError, match='ListUsersQuery'):
        await mediator.query(ListUsersQuery(keyword='alice'))


@pytest.mark.asyncio
async def test_registry_rejects_duplicate_registration() -> None:
    registry = HandlerRegistry()

    registry.register_command(CreateUserCommand, CreateUserCommandHandler())
    with pytest.raises(DuplicateHandlerRegistrationError):
        registry.register_command(CreateUserCommand, CreateUserCommandHandler())

    registry.register_query(ListUsersQuery, ListUsersQueryHandler())
    with pytest.raises(DuplicateHandlerRegistrationError):
        registry.register_query(ListUsersQuery, ListUsersQueryHandler())


@pytest.mark.asyncio
async def test_command_pipeline_runs_in_configured_order() -> None:
    trace: list[str] = []
    registry = HandlerRegistry()
    registry.register_command(CreateUserCommand, CreateUserCommandHandler(trace=trace))

    mediator = Mediator(
        registry,
        command_behaviors=(
            TraceBehavior(trace, 'validate'),
            TraceBehavior(trace, 'audit'),
        ),
    )

    _ = await mediator.send(CreateUserCommand(user_name='alice'))

    assert trace == [
        'validate:before:CreateUserCommand',
        'audit:before:CreateUserCommand',
        'handler',
        'audit:after:CreateUserCommand',
        'validate:after:CreateUserCommand',
    ]


@pytest.mark.asyncio
async def test_command_pipeline_supports_short_circuit() -> None:
    trace: list[str] = []
    registry = HandlerRegistry()
    registry.register_command(CreateUserCommand, CreateUserCommandHandler(trace=trace))

    mediator = Mediator(
        registry,
        command_behaviors=(
            ShortCircuitBehavior(),
            TraceBehavior(trace, 'audit'),
        ),
    )

    result = await mediator.send(CreateUserCommand(user_name='alice'))

    assert result.success is False
    assert result.status == 'blocked'
    assert trace == []
