from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from module_admin.entity.vo.config_vo import ConfigModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application import CommandResult, HandlerRegistry, Mediator
from modules.system.application.behaviors import build_default_command_behaviors
from modules.system.application.commands import AddConfigCommand
from utils.audit_context import get_audit_context, set_audit_context


class _TransactionContext:
    def __init__(self, session: _SessionStub) -> None:
        self._session = session

    async def __aenter__(self):
        self._session.active = True
        self._session.begin_count += 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._session.active = False
        if exc_type is None:
            self._session.commit_count += 1
        else:
            self._session.rollback_count += 1
        return False


class _SessionStub:
    def __init__(self) -> None:
        self.active = False
        self.begin_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def in_transaction(self) -> bool:
        return self.active

    def begin(self) -> _TransactionContext:
        return _TransactionContext(self)

    def begin_nested(self) -> _TransactionContext:
        return _TransactionContext(self)


class _ValidPayload:
    def __init__(self, trace: list[str]) -> None:
        self._trace = trace

    def validate_fields(self) -> None:
        self._trace.append('validate')


class _InvalidPayload:
    def validate_fields(self) -> None:
        raise ValueError('invalid payload')


@dataclass
class _PipelineCommand:
    payload: Any | None = None
    query_db: Any | None = None
    operator: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    authorizer: Any | None = None


class _SuccessHandler:
    def __init__(self, trace: list[str], *, events: tuple[Any, ...] = ()) -> None:
        self._trace = trace
        self._events = events

    async def handle(self, request: _PipelineCommand) -> CommandResult[dict[str, str]]:
        in_txn = bool(getattr(request.query_db, 'active', False))
        self._trace.append(f'handler:txn={in_txn}')
        return CommandResult(
            success=True,
            status='created',
            data={'message': 'ok'},
            events=self._events,
            metadata={'handler': 'ok'},
        )


class _FailHandler:
    def __init__(self, trace: list[str]) -> None:
        self._trace = trace

    async def handle(self, request: _PipelineCommand) -> CommandResult[dict[str, str]]:
        in_txn = bool(getattr(request.query_db, 'active', False))
        self._trace.append(f'handler:txn={in_txn}')
        raise RuntimeError('boom')


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _ConfigServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None

    async def add_config_services(self, redis_client, payload):
        self.add_called_with = (redis_client, payload)
        return _CrudResponse(is_success=True, message='新增成功')


@pytest.mark.asyncio
async def test_default_command_behaviors_validate_auth_txn_and_collect_events() -> None:
    trace: list[str] = []
    session = _SessionStub()

    async def _authorize() -> None:
        trace.append('authorize')

    command = _PipelineCommand(
        payload=_ValidPayload(trace),
        query_db=session,
        operator='tester',
        trace_id='trace-1',
        request_id='req-1',
        authorizer=_authorize,
    )

    registry = HandlerRegistry()
    registry.register_command(_PipelineCommand, _SuccessHandler(trace, events=(object(),)))
    mediator = Mediator(registry, command_behaviors=build_default_command_behaviors())

    set_audit_context({})
    result = await mediator.send(command)

    assert result.success is True
    assert result.status == 'created'
    assert result.metadata['event_count'] == 1
    assert trace == ['validate', 'authorize', 'handler:txn=True']
    assert session.begin_count == 1
    assert session.commit_count == 1
    assert session.rollback_count == 0

    audit_ctx = get_audit_context()
    assert audit_ctx['request_id'] == 'req-1'
    assert audit_ctx['trace_id'] == 'trace-1'
    assert audit_ctx['user_name'] == 'tester'


@pytest.mark.asyncio
async def test_default_command_behaviors_short_circuit_before_handler_on_validation_error() -> None:
    trace: list[str] = []
    session = _SessionStub()

    command = _PipelineCommand(payload=_InvalidPayload(), query_db=session, operator='tester')

    registry = HandlerRegistry()
    registry.register_command(_PipelineCommand, _SuccessHandler(trace))
    mediator = Mediator(registry, command_behaviors=build_default_command_behaviors())

    with pytest.raises(ValueError, match='invalid payload'):
        await mediator.send(command)

    assert trace == []
    assert session.begin_count == 0
    assert session.commit_count == 0
    assert session.rollback_count == 0


@pytest.mark.asyncio
async def test_default_command_behaviors_rollback_transaction_on_handler_exception() -> None:
    trace: list[str] = []
    session = _SessionStub()

    command = _PipelineCommand(payload=_ValidPayload(trace), query_db=session, operator='tester')

    registry = HandlerRegistry()
    registry.register_command(_PipelineCommand, _FailHandler(trace))
    mediator = Mediator(registry, command_behaviors=build_default_command_behaviors())

    with pytest.raises(RuntimeError, match='boom'):
        await mediator.send(command)

    assert trace == ['validate', 'handler:txn=True']
    assert session.begin_count == 1
    assert session.commit_count == 0
    assert session.rollback_count == 1


@pytest.mark.asyncio
async def test_system_mediator_injects_default_command_behaviors() -> None:
    config_service = _ConfigServiceStub()
    mediator = provide_system_mediator(config_service=config_service)

    result = await mediator.send(
        AddConfigCommand(
            redis_client=object(),
            config=ConfigModel(
                configName='系统主题',
                configKey='sys.theme',
                configValue='default',
                configType='Y',
            ),
            operator='tester',
            trace_id='trace-provider',
            request_id='req-provider',
        )
    )

    assert result.success is True
    assert result.status == 'created'
    assert result.metadata['operator'] == 'tester'
    assert result.metadata['event_count'] == 1
    assert config_service.add_called_with is not None
