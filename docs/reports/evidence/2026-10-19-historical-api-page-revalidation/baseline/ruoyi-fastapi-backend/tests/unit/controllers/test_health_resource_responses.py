from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

import server


@pytest.fixture
def health_app(monkeypatch):
    app = FastAPI()
    paths = {'/health', '/ready', '/health/db', '/health/deep', '/health/events', '/health/query-stats'}
    for route in server.app.routes:
        if getattr(route, 'path', None) in paths:
            app.router.routes.append(route)
    monkeypatch.setattr(server, 'app', SimpleNamespace(state=SimpleNamespace()))
    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'path,status',
    [
        ('/health', 200),
        ('/ready', 503),
        ('/health/db', 503),
        ('/health/deep', 503),
        ('/health/events', 503),
        ('/health/query-stats', 503),
    ],
)
async def test_missing_runtime_has_resource_status_instead_of_500(health_app, path, status):
    async with AsyncClient(app=health_app, base_url='http://test') as client:
        response = await client.get(path)
    assert response.status_code == status
    assert 'status' in response.json()
    assert 'code' not in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize('pool_status,http_status', [('healthy', 200), ('warning', 200), ('critical', 503)])
async def test_pool_health_preserves_critical_http_status(health_app, pool_status, http_status):
    server.app.state.pool_health_checker = SimpleNamespace(
        check_health=lambda _: {'status': pool_status, 'pool_size': 5, 'message': 'pool result'}
    )
    async with AsyncClient(app=health_app, base_url='http://test') as client:
        response = await client.get('/health/db')
    assert response.status_code == http_status
    assert response.json() == {'status': pool_status, 'poolSize': 5, 'message': 'pool result'}


@pytest.mark.asyncio
async def test_healthy_deep_events_and_query_stats(health_app):
    server.app.state.resilience_runtime = SimpleNamespace(
        deep_health_checker=SimpleNamespace(run=AsyncMock(return_value=(200, {'status': 'healthy'})))
    )
    server.app.state.event_runtime = SimpleNamespace(health=AsyncMock(return_value={'running': True}))
    server.app.state.query_monitor = SimpleNamespace(
        get_stats=lambda: {'total_queries': 2, 'slow_queries': 0, 'slow_query_rate': 0, 'avg_time': 1.5, 'max_time': 2}
    )
    async with AsyncClient(app=health_app, base_url='http://test') as client:
        for path in ['/health/deep', '/health/events', '/health/query-stats']:
            response = await client.get(path)
            assert response.status_code == 200
            assert 'code' not in response.json()
        assert response.json()['totalQueries'] == 2
