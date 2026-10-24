"""CQRS dispatcher and registry errors."""

from __future__ import annotations


class HandlerRegistrationError(RuntimeError):
    """Base error for handler registration and resolution failures."""


class DuplicateHandlerRegistrationError(HandlerRegistrationError):
    """Raised when a request type is registered multiple times."""

    def __init__(self, request_type: type, kind: str):
        super().__init__(f'Duplicate {kind} handler registration for `{request_type.__name__}`')


class HandlerNotRegisteredError(HandlerRegistrationError):
    """Raised when request handler is missing from registry."""

    def __init__(self, request_type: type, kind: str):
        super().__init__(f'No {kind} handler registered for `{request_type.__name__}`')
