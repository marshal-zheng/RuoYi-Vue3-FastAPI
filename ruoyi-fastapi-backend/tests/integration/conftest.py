"""
Integration test fixtures and configuration
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from container import build_container
from server import DummyRedis, app


@pytest.fixture(scope="function")
def test_client(test_db: AsyncSession):
    """Create a test client with test database override"""

    async def override_get_db():
        yield test_db

    previous_container = getattr(app.state, 'container', None)
    previous_redis = getattr(app.state, 'redis', None)
    app.state.container = build_container()
    app.state.redis = DummyRedis()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    if previous_container is None and hasattr(app.state, 'container'):
        delattr(app.state, 'container')
    else:
        app.state.container = previous_container
    if previous_redis is None and hasattr(app.state, 'redis'):
        delattr(app.state, 'redis')
    else:
        app.state.redis = previous_redis
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession):
    """Create an async test client for integration tests with test database"""

    async def override_get_db():
        yield test_db

    previous_container = getattr(app.state, 'container', None)
    previous_redis = getattr(app.state, 'redis', None)
    app.state.container = build_container()
    app.state.redis = DummyRedis()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    if previous_container is None and hasattr(app.state, 'container'):
        delattr(app.state, 'container')
    else:
        app.state.container = previous_container
    if previous_redis is None and hasattr(app.state, 'redis'):
        delattr(app.state, 'redis')
    else:
        app.state.redis = previous_redis
    app.dependency_overrides.clear()
