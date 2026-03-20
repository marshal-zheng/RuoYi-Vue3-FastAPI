import sys
import types

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middlewares.request_logging_middleware import RequestLoggingASGIMiddleware


class _CaptureBoundLogger:
    def __init__(self, events, payload):
        self._events = events
        self._payload = dict(payload)

    def log(self, level, message):
        self._events.append(
            {
                'level': str(level),
                'message': str(message),
                'payload': dict(self._payload),
            }
        )


class _CaptureLogger:
    def __init__(self):
        self.events = []

    def bind(self, **kwargs):
        return _CaptureBoundLogger(self.events, kwargs)


def _build_app() -> FastAPI:
    app = FastAPI()
    class _FakeSecurityTokenService:
        @staticmethod
        async def extract_user_context_from_token(token: str):
            if token == 'token-user-9527':
                return {'userId': '9527', 'userName': 'admin'}
            return None

    app.state.security_token_service = _FakeSecurityTokenService()
    app.add_middleware(RequestLoggingASGIMiddleware)

    @app.get('/ok')
    async def ok_endpoint():
        return {'ok': True}

    @app.get('/boom')
    async def boom_endpoint():
        raise RuntimeError('boom')

    return app


@pytest.mark.asyncio
async def test_request_log_contains_required_fields(monkeypatch):
    app = _build_app()
    capture_logger = _CaptureLogger()
    monkeypatch.setattr('middlewares.request_logging_middleware.logger', capture_logger)

    token = 'token-user-9527'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Forwarded-For': '10.0.0.1',
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/ok', headers=headers)

    assert response.status_code == 200
    assert len(capture_logger.events) == 1
    event = capture_logger.events[0]
    payload = event['payload']

    assert event['level'] == 'INFO'
    assert event['message'] == 'http_request'
    assert payload['event'] == 'http_request'
    assert payload['user_id'] == '9527'
    assert payload['method'] == 'GET'
    assert payload['path'] == '/ok'
    assert payload['status_code'] == 200
    assert isinstance(payload['duration_ms'], float)
    assert payload['client_ip'] == '10.0.0.1'
    assert isinstance(payload['request_id'], str) and payload['request_id']
    assert isinstance(payload['trace_id'], str) and payload['trace_id']


@pytest.mark.asyncio
async def test_request_log_500_uses_error_level(monkeypatch):
    app = _build_app()
    capture_logger = _CaptureLogger()
    monkeypatch.setattr('middlewares.request_logging_middleware.logger', capture_logger)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/boom')

    assert response.status_code == 500
    assert len(capture_logger.events) == 1
    event = capture_logger.events[0]
    payload = event['payload']

    assert event['level'] == 'ERROR'
    assert payload['status_code'] == 500
    assert payload['path'] == '/boom'


@pytest.mark.asyncio
async def test_request_log_prefers_otel_trace_id(monkeypatch):
    app = _build_app()
    capture_logger = _CaptureLogger()
    monkeypatch.setattr('middlewares.request_logging_middleware.logger', capture_logger)

    trace_id_int = int('1234567890abcdef1234567890abcdef', 16)

    class _DummySpanContext:
        is_valid = True
        trace_id = trace_id_int

    class _DummySpan:
        @staticmethod
        def get_span_context():
            return _DummySpanContext()

    fake_trace_module = types.SimpleNamespace(get_current_span=lambda: _DummySpan())
    fake_otel_module = types.ModuleType('opentelemetry')
    fake_otel_module.trace = fake_trace_module
    monkeypatch.setitem(sys.modules, 'opentelemetry', fake_otel_module)
    monkeypatch.setitem(sys.modules, 'opentelemetry.trace', fake_trace_module)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/ok')

    assert response.status_code == 200
    assert len(capture_logger.events) == 1
    payload = capture_logger.events[0]['payload']
    assert payload['trace_id'] == format(trace_id_int, '032x')


@pytest.mark.asyncio
async def test_request_log_uses_traceparent_when_otel_span_unavailable(monkeypatch):
    app = _build_app()
    capture_logger = _CaptureLogger()
    monkeypatch.setattr('middlewares.request_logging_middleware.logger', capture_logger)

    trace_id = '1234567890abcdef1234567890abcdef'
    span_id = '1111222233334444'
    headers = {'traceparent': f'00-{trace_id}-{span_id}-01'}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/ok', headers=headers)

    assert response.status_code == 200
    assert len(capture_logger.events) == 1
    payload = capture_logger.events[0]['payload']
    assert payload['trace_id'] == trace_id
