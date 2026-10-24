"""Explicit handler registry for CQRS mediator dispatch."""

from __future__ import annotations

from typing import Any

from modules.system.application.errors import DuplicateHandlerRegistrationError, HandlerNotRegisteredError


class HandlerRegistry:
    """Runtime registry for command and query handlers."""

    def __init__(self) -> None:
        self._command_handlers: dict[type, Any] = {}
        self._query_handlers: dict[type, Any] = {}

    def register_command(self, request_type: type, handler: Any) -> None:
        """Register command handler with explicit request type key."""
        if request_type in self._command_handlers:
            raise DuplicateHandlerRegistrationError(request_type, kind='command')
        self._command_handlers[request_type] = handler

    def register_query(self, request_type: type, handler: Any) -> None:
        """Register query handler with explicit request type key."""
        if request_type in self._query_handlers:
            raise DuplicateHandlerRegistrationError(request_type, kind='query')
        self._query_handlers[request_type] = handler

    def resolve_command(self, request_type: type) -> Any:
        """Resolve command handler by request type."""
        handler = self._command_handlers.get(request_type)
        if handler is None:
            raise HandlerNotRegisteredError(request_type, kind='command')
        return handler

    def resolve_query(self, request_type: type) -> Any:
        """Resolve query handler by request type."""
        handler = self._query_handlers.get(request_type)
        if handler is None:
            raise HandlerNotRegisteredError(request_type, kind='query')
        return handler

    @property
    def command_handlers(self) -> dict[type, Any]:
        """Read-only command handler mapping."""
        return self._command_handlers

    @property
    def query_handlers(self) -> dict[type, Any]:
        """Read-only query handler mapping."""
        return self._query_handlers
