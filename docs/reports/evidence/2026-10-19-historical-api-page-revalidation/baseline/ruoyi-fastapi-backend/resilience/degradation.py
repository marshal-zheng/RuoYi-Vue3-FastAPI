"""Degradation context and response-header middleware."""

from __future__ import annotations

import contextvars
from typing import Dict

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Scope, Send


_DEGRADED_SERVICES: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar('degraded_services', default={})


def reset_degradation_context() -> contextvars.Token:
    """Reset degradation context for a request."""
    return _DEGRADED_SERVICES.set({})


def restore_degradation_context(token: contextvars.Token) -> None:
    _DEGRADED_SERVICES.reset(token)


def mark_degraded(service: str, reason: str) -> None:
    """Mark one dependency as degraded in current request scope."""
    current = dict(_DEGRADED_SERVICES.get() or {})
    current[service] = reason
    _DEGRADED_SERVICES.set(current)


def get_degraded_services() -> Dict[str, str]:
    """Return degraded services map."""
    return dict(_DEGRADED_SERVICES.get() or {})


def build_degraded_header_value() -> str:
    services = get_degraded_services()
    if not services:
        return ''
    return ','.join(sorted(services.keys()))


class DegradationHeaderASGIMiddleware:
    """Attach X-Degraded-Services header for degraded requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive, send: Send) -> None:
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        token = reset_degradation_context()

        async def send_wrapper(message: Message) -> None:
            if message.get('type') == 'http.response.start':
                header_value = build_degraded_header_value()
                if header_value:
                    headers = list(message.get('headers', []))
                    headers.append((b'x-degraded-services', header_value.encode('utf-8')))
                    message['headers'] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            restore_degradation_context(token)


def add_degradation_header_middleware(app: FastAPI) -> None:
    app.add_middleware(DegradationHeaderASGIMiddleware)
