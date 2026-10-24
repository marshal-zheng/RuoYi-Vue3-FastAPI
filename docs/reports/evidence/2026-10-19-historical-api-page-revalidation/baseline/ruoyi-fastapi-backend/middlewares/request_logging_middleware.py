"""
HTTP request structured logging middleware.

Logs one event per request with normalized fields:
- request_id
- trace_id
- user_id
- method
- path
- status_code
- duration_ms
"""
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Scope, Send

from middlewares.trace_middleware import TraceCtx, get_request_id, get_trace_id
from utils.log_util import logger


class RequestLoggingASGIMiddleware:
    def __init__(self, app: ASGIApp, exclude_paths: tuple[str, ...] = ()) -> None:
        self.app = app
        self._exclude_paths = frozenset(path for path in exclude_paths if path)

    async def __call__(self, scope: Scope, receive, send: Send) -> None:
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        path = str(scope.get('path', ''))
        if path in self._exclude_paths:
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        method = str(scope.get('method', ''))
        headers = self._extract_headers(scope.get('headers', []))
        user_id = await self._resolve_user_id(scope, headers)
        client_ip = self._resolve_client_ip(scope, headers)
        traceparent = headers.get('traceparent')
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message.get('type') == 'http.response.start':
                status_code = int(message.get('status', status_code))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._emit_request_log(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=self._duration_ms(started_at),
                user_id=user_id,
                client_ip=client_ip,
                traceparent=traceparent,
            )
            raise

        self._emit_request_log(
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=self._duration_ms(started_at),
            user_id=user_id,
            client_ip=client_ip,
            traceparent=traceparent,
        )

    @staticmethod
    def _duration_ms(started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000.0, 3)

    @staticmethod
    def _extract_headers(raw_headers) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for raw_name, raw_value in raw_headers:
            name = raw_name.decode('latin-1').lower()
            if name not in result:
                result[name] = raw_value.decode('latin-1')
        return result

    @staticmethod
    def _resolve_client_ip(scope: Scope, headers: Dict[str, str]) -> str:
        forwarded = headers.get('x-forwarded-for', '')
        if forwarded:
            first_ip = forwarded.split(',')[0].strip()
            if first_ip:
                return first_ip

        client = scope.get('client')
        if isinstance(client, (list, tuple)) and client:
            return str(client[0])
        return 'unknown'

    async def _resolve_user_id(self, scope: Scope, headers: Dict[str, str]) -> Optional[str]:
        authorization = headers.get('authorization', '')
        if not authorization.lower().startswith('bearer '):
            return None

        token = authorization[7:].strip()
        if not token:
            return None

        service = self._resolve_security_service(scope)
        if service is None:
            return None
        try:
            payload = await service.extract_user_context_from_token(token)
            if not payload:
                return None
            user_id = payload.get('userId')
            return str(user_id) if user_id else None
        except Exception:
            return None

    @staticmethod
    def _resolve_security_service(scope: Scope) -> Optional[Any]:
        app = scope.get('app')
        state = getattr(app, 'state', None) if app else None
        service = getattr(state, 'security_token_service', None) if state else None
        if service and hasattr(service, 'extract_user_context_from_token'):
            return service
        return None

    @staticmethod
    def _emit_request_log(
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str],
        client_ip: str,
        traceparent: Optional[str],
    ) -> None:
        request_id = get_request_id() or TraceCtx.get_request_id() or TraceCtx.set_request_id()
        trace_id = get_trace_id() or RequestLoggingASGIMiddleware._resolve_trace_id(request_id, traceparent)
        level = 'INFO'
        if status_code >= 500:
            level = 'ERROR'
        elif status_code >= 400:
            level = 'WARNING'

        logger.bind(
            event='http_request',
            request_id=request_id,
            trace_id=trace_id,
            user_id=user_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        ).log(level, 'http_request')

    @staticmethod
    def _resolve_trace_id(fallback: str, traceparent: Optional[str] = None) -> str:
        try:
            from opentelemetry import trace as otel_trace

            span = otel_trace.get_current_span()
            context = span.get_span_context() if span is not None else None
            if context is not None and getattr(context, 'is_valid', False):
                trace_id = format(int(context.trace_id), '032x')
                if trace_id and trace_id != '0' * 32:
                    return trace_id
        except Exception:
            pass

        parsed_trace_id = RequestLoggingASGIMiddleware._parse_traceparent_trace_id(traceparent)
        if parsed_trace_id:
            return parsed_trace_id
        return fallback

    @staticmethod
    def _parse_traceparent_trace_id(traceparent: Optional[str]) -> Optional[str]:
        if not traceparent:
            return None

        parts = str(traceparent).strip().split('-')
        if len(parts) != 4:
            return None

        trace_id = parts[1].strip().lower()
        if len(trace_id) != 32 or trace_id == '0' * 32:
            return None

        try:
            int(trace_id, 16)
        except ValueError:
            return None
        return trace_id


def add_request_logging_middleware(app: FastAPI, *, exclude_paths: tuple[str, ...] = ()) -> None:
    app.add_middleware(RequestLoggingASGIMiddleware, exclude_paths=exclude_paths)
