"""
@author: peng
@file: span.py
@time: 2025/1/17  16:57
"""

from contextlib import asynccontextmanager

from starlette.types import Message, Scope

from .ctx import TraceCtx


class Span:
    """
    整个http生命周期：
        request(before) --> request(after) --> response(before) --> response(after)
    """

    def __init__(self, scope: Scope):
        self.scope = scope

    @staticmethod
    def _extract_headers(scope: Scope) -> dict[str, str]:
        headers = {}
        for raw_key, raw_value in scope.get('headers', []):
            key = raw_key.decode('latin-1').lower()
            if key not in headers:
                headers[key] = raw_value.decode('latin-1')
        return headers

    @staticmethod
    def _parse_traceparent_trace_id(traceparent: str | None) -> str:
        if not traceparent:
            return ''
        parts = str(traceparent).strip().split('-')
        if len(parts) != 4:
            return ''
        trace_id = parts[1].strip().lower()
        if len(trace_id) != 32 or trace_id == '0' * 32:
            return ''
        try:
            int(trace_id, 16)
        except ValueError:
            return ''
        return trace_id

    async def request_before(self):
        """
        request_before: 处理header信息等, 如记录请求体信息
        """
        headers = self._extract_headers(self.scope)
        request_id = headers.get('x-request-id') or headers.get('request-id')
        trace_id = (
            self._parse_traceparent_trace_id(headers.get('traceparent'))
            or headers.get('x-trace-id', '').strip()
        )
        TraceCtx.set_request_id(request_id)
        TraceCtx.set_trace_id(trace_id)

    async def request_after(self, message: Message):
        """
        request_after: 处理请求bytes， 如记录请求参数

        example:
            message: {'type': 'http.request', 'body': b'{\r\n    "name": "\xe8\x8b\x8f\xe8\x8b\x8f\xe8\x8b\x8f"\r\n}', 'more_body': False}
        """
        return message

    async def response(self, message: Message):
        """
        if message['type'] == "http.response.start":   -----> request-before
            pass
        if message['type'] == "http.response.body":    -----> request-after
            message.get('body', b'')
            pass
        """
        if message['type'] == 'http.response.start':
            headers = [
                (key, value) for key, value in message.get('headers', [])
                if key.lower() not in {b'x-request-id', b'x-trace-id'}
            ]
            request_id = TraceCtx.get_request_id()
            trace_id = TraceCtx.get_trace_id()
            if request_id:
                headers.append((b'x-request-id', request_id.encode()))
            if trace_id:
                headers.append((b'x-trace-id', trace_id.encode()))
            message['headers'] = headers
        return message


@asynccontextmanager
async def get_current_span(scope: Scope):
    yield Span(scope)
