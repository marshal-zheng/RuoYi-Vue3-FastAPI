"""CQRS core contracts for command/query handlers and pipeline behaviors."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')
TResult = TypeVar('TResult')

NextHandler = Callable[[], Awaitable[TResponse]]


@dataclass
class CommandResult(Generic[TResult]):
    """Standard command execution result."""

    success: bool
    data: TResult | None = None
    status: str = 'ok'
    events: tuple[Any, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ICommandHandler(Protocol[TRequest, TResult]):
    """Command handler abstraction."""

    async def handle(self, request: TRequest) -> CommandResult[TResult]:
        """Handle a command request and return standardized command result."""


@runtime_checkable
class IQueryHandler(Protocol[TRequest, TResponse]):
    """Query handler abstraction."""

    async def handle(self, request: TRequest) -> TResponse:
        """Handle a query request and return read model."""


@runtime_checkable
class IPipelineBehavior(Protocol[TRequest, TResponse]):
    """Pipeline behavior abstraction."""

    async def handle(self, request: TRequest, next_handler: NextHandler[TResponse]) -> TResponse:
        """Run pre/post logic and delegate to next handler."""
