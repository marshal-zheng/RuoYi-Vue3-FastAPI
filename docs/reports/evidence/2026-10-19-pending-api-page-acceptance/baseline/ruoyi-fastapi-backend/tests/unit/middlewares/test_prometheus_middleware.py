import pytest
from fastapi import FastAPI, HTTPException, Response
from httpx import ASGITransport, AsyncClient

from middlewares.prometheus_middleware import PrometheusMetricsASGIMiddleware
from utils.prometheus_metrics import PrometheusMetricsRegistry, format_metric_line


def _build_app() -> FastAPI:
    app = FastAPI()
    app.state.metrics_registry = PrometheusMetricsRegistry(buckets=(0.01, 0.1, 1.0))
    app.add_middleware(PrometheusMetricsASGIMiddleware, exclude_paths=('/metrics',))

    @app.get('/ok')
    async def ok_endpoint():
        return {'ok': True}

    @app.get('/boom')
    async def boom_endpoint():
        raise HTTPException(status_code=500, detail='boom')

    @app.get('/metrics')
    async def metrics_endpoint():
        content = app.state.metrics_registry.render_http_metrics()
        return Response(content=content, media_type='text/plain; version=0.0.4; charset=utf-8')

    return app


@pytest.mark.asyncio
async def test_prometheus_middleware_collects_http_metrics():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        await client.get('/ok')
        await client.get('/ok')
        await client.get('/boom')
        metrics_resp = await client.get('/metrics')

    assert metrics_resp.status_code == 200
    text = metrics_resp.text

    assert 'http_requests_total{method="GET",path="/ok",status_code="200"} 2' in text
    assert 'http_requests_total{method="GET",path="/boom",status_code="500"} 1' in text
    assert 'http_request_errors_total{method="GET",path="/boom",status_code="500"} 1' in text
    assert 'http_request_duration_seconds_count{method="GET",path="/ok"} 2' in text
    assert 'path="/metrics"' not in text


def test_format_metric_line_escapes_label_values():
    line = format_metric_line(
        'sample_metric',
        1,
        labels={'path': '/a"b\\c'},
    )
    assert line == 'sample_metric{path="/a\\"b\\\\c"} 1'

