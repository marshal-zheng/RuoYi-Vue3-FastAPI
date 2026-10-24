"""Integration test for request log and OpenTelemetry trace correlation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from middlewares.request_logging_middleware import RequestLoggingASGIMiddleware
from utils import otel_tracing


@dataclass
class _CapturedEvent:
    level: str
    message: str
    payload: dict


class _CapturedBoundLogger:
    def __init__(self, sink: list[_CapturedEvent], payload: dict):
        self._sink = sink
        self._payload = payload

    def log(self, level: str, message: str) -> None:
        self._sink.append(_CapturedEvent(level=str(level), message=str(message), payload=dict(self._payload)))


class _CapturedLogger:
    def __init__(self):
        self.events: list[_CapturedEvent] = []

    def bind(self, **kwargs):
        return _CapturedBoundLogger(self.events, kwargs)


@pytest.mark.asyncio
async def test_traceparent_correlates_request_log_and_spans(monkeypatch):
    otel_tracing.reset_otel_state_for_tests()
    symbols = otel_tracing._load_otel_symbols()
    assert symbols is not None

    class _NoopOTLPSpanExporter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def shutdown(self):
            return None

        def force_flush(self, timeout_millis=30000):
            return True

    patched_symbols = dict(symbols)
    patched_symbols['OTLPSpanExporter'] = _NoopOTLPSpanExporter
    monkeypatch.setattr(otel_tracing, '_load_otel_symbols', lambda: patched_symbols)

    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_enabled', True)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_traces_sample_ratio', 1.0)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_otlp_endpoint', 'http://127.0.0.1:4318/v1/traces')
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_console_exporter', False)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_excluded_urls', '')

    captured_logger = _CapturedLogger()
    monkeypatch.setattr('middlewares.request_logging_middleware.logger', captured_logger)

    app = FastAPI()
    app.add_middleware(RequestLoggingASGIMiddleware)

    @app.get('/trace-correlation')
    async def trace_correlation_endpoint():
        tracer = otel_trace.get_tracer('tests.integration.trace-correlation')
        with tracer.start_as_current_span('db.mock.query'):
            pass
        with tracer.start_as_current_span('redis.mock.command'):
            pass
        return {'ok': True}

    assert otel_tracing.init_otel_tracing(app=app, db_engine=None) is True

    exporter = InMemorySpanExporter()
    provider = otel_trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    upstream_trace_id = '1234567890abcdef1234567890abcdef'
    upstream_parent_id = '1111222233334444'
    headers = {'traceparent': f'00-{upstream_trace_id}-{upstream_parent_id}-01'}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/trace-correlation', headers=headers)

    assert response.status_code == 200
    assert len(captured_logger.events) == 1
    log_event = captured_logger.events[0]
    assert log_event.payload['trace_id'] == upstream_trace_id

    spans = exporter.get_finished_spans()
    assert spans

    trace_ids = {format(span.context.trace_id, '032x') for span in spans}
    assert trace_ids == {upstream_trace_id}

    span_by_name = {span.name: span for span in spans}
    assert 'GET /trace-correlation' in span_by_name
    assert 'db.mock.query' in span_by_name
    assert 'redis.mock.command' in span_by_name

    server_span = span_by_name['GET /trace-correlation']
    db_span = span_by_name['db.mock.query']
    redis_span = span_by_name['redis.mock.command']
    assert db_span.parent is not None and db_span.parent.span_id == server_span.context.span_id
    assert redis_span.parent is not None and redis_span.parent.span_id == server_span.context.span_id
