"""Thin ASGI guard around the pinned SSE implementation, including its heartbeat send path."""

import logging

import anyio
from sse_starlette.sse import EventSourceResponse, SendTimeoutError


class _NoSSEContentLogs(logging.Filter):
    def filter(self, _record):
        # The pinned library logs raw SSE chunks at DEBUG. Our finite metrics replace these diagnostics.
        return False


logging.getLogger('sse_starlette.sse').addFilter(_NoSSEContentLogs())


class PrivateEventSourceResponse(EventSourceResponse):
    async def __call__(self, scope, receive, send):
        async def bounded_send(message):
            # sse-starlette 3.0.3 applies send_timeout only to data frames, not ping/start/end.
            with anyio.fail_after(self.send_timeout):
                await send(message)

        try:  # noqa: SIM105 -- except* handles AnyIO exception groups, unlike suppress on Python 3.11.
            await super().__call__(scope, receive, bounded_send)
        except* (TimeoutError, SendTimeoutError):
            # A slow/disconnected client cannot consume a candidate. Outer middleware finalizes cancelled.
            pass
