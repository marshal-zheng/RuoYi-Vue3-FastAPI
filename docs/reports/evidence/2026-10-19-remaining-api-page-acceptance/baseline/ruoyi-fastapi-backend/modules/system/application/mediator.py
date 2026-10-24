"""CQRS mediator with explicit handler registry and pipeline dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from modules.system.application.contracts import CommandResult, IPipelineBehavior
    from modules.system.application.handler_registry import HandlerRegistry


class Mediator:
    """Dispatch command/query requests to registered handlers via ordered pipelines."""

    def __init__(
        self,
        registry: HandlerRegistry,
        *,
        command_behaviors: tuple[IPipelineBehavior[Any, CommandResult[Any]], ...]
        | list[IPipelineBehavior[Any, CommandResult[Any]]] = (),
        query_behaviors: tuple[IPipelineBehavior[Any, Any], ...] | list[IPipelineBehavior[Any, Any]] = (),
    ) -> None:
        self._registry = registry
        self._command_behaviors = tuple(command_behaviors)
        self._query_behaviors = tuple(query_behaviors)

    async def send(self, command: Any) -> CommandResult[Any]:
        """Dispatch command request through command pipeline."""
        handler = self._registry.resolve_command(type(command))

        async def terminal() -> CommandResult[Any]:
            return cast('CommandResult[Any]', await handler.handle(command))

        return await self._execute_pipeline(command, self._command_behaviors, terminal)

    async def query(self, query_request: Any) -> Any:
        """Dispatch query request through query pipeline."""
        handler = self._registry.resolve_query(type(query_request))

        async def terminal() -> Any:
            return await handler.handle(query_request)

        return await self._execute_pipeline(query_request, self._query_behaviors, terminal)

    async def _execute_pipeline(
        self,
        request: Any,
        behaviors: tuple[IPipelineBehavior[Any, Any], ...],
        terminal,
    ) -> Any:
        async def invoke(index: int) -> Any:
            if index >= len(behaviors):
                return await terminal()
            behavior = behaviors[index]
            return await behavior.handle(request, lambda: invoke(index + 1))

        return await invoke(0)
