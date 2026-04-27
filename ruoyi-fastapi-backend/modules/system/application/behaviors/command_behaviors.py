"""Default command pipeline behaviors for system CQRS mediator."""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any

from events.runtime_context import get_event_runtime
from middlewares.trace_middleware import TraceCtx
from modules.system.application.contracts import CommandResult, IPipelineBehavior
from utils.audit_context import get_audit_context, set_audit_context
from utils.log_util import logger
from utils.transaction_manager import TransactionManager

CommandNextHandler = Callable[[], Awaitable[CommandResult[Any]]]

_AUTH_HOOK_NAMES = (
    'authorize',
    'authorizer',
    'permission_checker',
    'auth_checker',
)


class CommandValidationBehavior(IPipelineBehavior[Any, CommandResult[Any]]):
    """Execute command payload validation before entering business handlers."""

    async def handle(self, request: Any, next_handler: CommandNextHandler) -> CommandResult[Any]:
        self._validate_request(request)
        return await next_handler()

    @staticmethod
    def _validate_request(request: Any) -> None:
        payload_items = []
        if hasattr(request, '__dict__'):
            payload_items = list(request.__dict__.items())
        elif hasattr(type(request), '__slots__'):
            payload_items = [
                (slot_name, getattr(request, slot_name, None))
                for slot_name in getattr(type(request), '__slots__', ())
            ]

        if not payload_items and hasattr(request, 'model_dump'):
            payload_items = list(request.model_dump(exclude_none=False).items())

        for field_name, payload in payload_items:
            if payload is None or field_name.startswith('_'):
                continue

            if field_name == 'user' and getattr(payload, 'type', None) in {'status', 'avatar', 'pwd'}:
                continue

            validator = getattr(payload, 'validate_fields', None)
            if callable(validator):
                validator()


class CommandAuthAuditBehavior(IPipelineBehavior[Any, CommandResult[Any]]):
    """Run optional authorization hook and bind audit context metadata."""

    async def handle(self, request: Any, next_handler: CommandNextHandler) -> CommandResult[Any]:
        await self._run_authorization_hook(request)
        self._bind_audit_context(request)
        return await next_handler()

    @staticmethod
    async def _run_authorization_hook(request: Any) -> None:
        for hook_name in _AUTH_HOOK_NAMES:
            hook = getattr(request, hook_name, None)
            if not callable(hook):
                continue

            result = hook()
            if inspect.isawaitable(result):
                await result
            return

    @staticmethod
    def _bind_audit_context(request: Any) -> None:
        operator = getattr(request, 'operator', None)
        request_id = getattr(request, 'request_id', None) or TraceCtx.get_request_id() or TraceCtx.set_request_id()
        trace_id = getattr(request, 'trace_id', None) or TraceCtx.get_trace_id() or request_id

        context = dict(get_audit_context())
        context['request_id'] = request_id
        context['trace_id'] = trace_id
        if operator:
            context['user_name'] = str(operator)

        set_audit_context(context)


class CommandTransactionBehavior(IPipelineBehavior[Any, CommandResult[Any]]):
    """Wrap command execution in a managed transaction when session is available."""

    def __init__(self, *, isolation_level: str | None = None, timeout: float | None = None):
        self._isolation_level = isolation_level
        self._timeout = timeout

    async def handle(self, request: Any, next_handler: CommandNextHandler) -> CommandResult[Any]:
        query_db = getattr(request, 'query_db', None)
        if not self._supports_transaction(query_db):
            return await next_handler()

        async with TransactionManager(query_db).transaction(
            isolation_level=self._isolation_level,
            timeout=self._timeout,
        ):
            return await next_handler()

    @staticmethod
    def _supports_transaction(query_db: Any) -> bool:
        return query_db is not None and hasattr(query_db, 'begin') and hasattr(query_db, 'in_transaction')


class CommandEventCollectionBehavior(IPipelineBehavior[Any, CommandResult[Any]]):
    """Normalize command events and enrich result metadata."""

    async def handle(self, request: Any, next_handler: CommandNextHandler) -> CommandResult[Any]:
        result = await next_handler()

        events = tuple(result.events or ())
        metadata = dict(result.metadata or {})
        metadata.setdefault('event_count', len(events))
        if events and 'event_types' not in metadata:
            metadata['event_types'] = [
                getattr(event, 'event_type', type(event).__name__)
                for event in events
            ]

        enqueued_count = 0
        event_runtime = get_event_runtime()
        if event_runtime is not None and events:
            query_db = getattr(request, 'query_db', None)
            enqueued_count = await event_runtime.enqueue_events(query_db, events)
        metadata.setdefault('outbox_enqueued', enqueued_count)

        result.events = events
        result.metadata = metadata
        return result


class CommandLoggingBehavior(IPipelineBehavior[Any, CommandResult[Any]]):
    """Emit structured command execution logs with correlation metadata."""

    async def handle(self, request: Any, next_handler: CommandNextHandler) -> CommandResult[Any]:
        command_type = type(request).__name__
        operator = getattr(request, 'operator', None)
        trace_id = getattr(request, 'trace_id', None) or TraceCtx.get_trace_id() or ''
        request_id = getattr(request, 'request_id', None) or TraceCtx.get_request_id() or ''

        started_at = time.perf_counter()
        try:
            result = await next_handler()
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            logger.bind(
                event='cqrs_command',
                command_type=command_type,
                operator=operator,
                trace_id=trace_id,
                request_id=request_id,
                duration_ms=duration_ms,
                success=False,
                status='failed',
            ).exception('cqrs_command_failed')
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        logger.bind(
            event='cqrs_command',
            command_type=command_type,
            operator=operator,
            trace_id=trace_id,
            request_id=request_id,
            duration_ms=duration_ms,
            success=result.success,
            status=result.status,
        ).info('cqrs_command_executed')
        return result


def build_default_command_behaviors() -> tuple[IPipelineBehavior[Any, CommandResult[Any]], ...]:
    """Build default command pipeline behaviors in deterministic order."""

    return (
        CommandLoggingBehavior(),
        CommandValidationBehavior(),
        CommandAuthAuditBehavior(),
        CommandTransactionBehavior(),
        CommandEventCollectionBehavior(),
    )
