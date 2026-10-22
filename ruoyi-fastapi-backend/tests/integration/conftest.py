"""HTTP tests run the real lifespan with resources owned by its event loop."""
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import server
from config import get_db as db_module
from config.enums import RedisInitKeyConfig
from container import build_container
from modules.system.application.services.capability_gate_service import CapabilityGateService
from tests.conftest import _import_orm_models


@pytest.fixture
def integration_app(tmp_path):
    app = server.app
    previous_state = dict(app.state._state)
    previous_overrides = dict(app.dependency_overrides)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def isolated_lifespan(application):
        # Created inside TestClient's portal (or the async test loop), never in
        # a different pytest loop. Separate request/background sessions use the
        # same per-test database, with normal commit/rollback semantics.
        _import_orm_models()
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'http.sqlite'}")
        sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        container = build_container()
        container._session_factory = sessions
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(db_module, '_TEST_ENGINE', engine)
            patch.setattr(db_module, '_TEST_SESSIONMAKER', sessions)
            patch.setattr(server, 'async_engine', engine)
            patch.setattr(server, 'build_container', lambda: container)
            patch.setattr(server, 'is_dev_managed_data_hot_reconcile_enabled', lambda: False)
            try:
                async with original_lifespan(application):
                    # Exercise ordinary HTTP contracts with declared modules enabled.
                    # Gate-disabled/missing behavior has its own integration tests.
                    gates = CapabilityGateService.from_declarations()
                    application.state.capability_gate_service = gates
                    for gate in gates.runtime_gates.values():
                        await application.state.redis.set(
                            f'{RedisInitKeyConfig.SYS_CONFIG.key}:{gate.config_key}', 'true'
                        )
                    yield
            finally:
                await engine.dispose()

    app.router.lifespan_context = isolated_lifespan
    try:
        yield app
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        app.state._state.clear()
        app.state._state.update(previous_state)


@pytest.fixture
def test_client(integration_app):
    with TestClient(integration_app, raise_server_exceptions=False) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(integration_app):
    async with integration_app.router.lifespan_context(integration_app), AsyncClient(
        transport=ASGITransport(app=integration_app, raise_app_exceptions=False),
        base_url='http://testserver',
    ) as client:
        yield client
