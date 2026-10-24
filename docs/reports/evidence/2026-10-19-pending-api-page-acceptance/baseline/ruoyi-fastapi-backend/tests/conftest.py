"""
Shared pytest fixtures and configuration for all tests.
"""

import sys
from collections.abc import AsyncGenerator, Generator
from importlib import import_module
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:  # pragma: no cover - environment-dependent branch
    import aiosqlite as _aiosqlite  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - exercised in offline/local python env
    from tests.fakes import aiosqlite_fallback as _aiosqlite_fallback

    sys.modules['aiosqlite'] = _aiosqlite_fallback


_OriginalAsyncClient = httpx.AsyncClient


class _PatchedAsyncClient(_OriginalAsyncClient):
    def __init__(self, *args, app=None, base_url=None, **kwargs):
        if app is not None:
            kwargs.setdefault('transport', ASGITransport(app=app, raise_app_exceptions=False))
        if base_url is not None:
            kwargs.setdefault('base_url', base_url)
        super().__init__(*args, **kwargs)


httpx.AsyncClient = _PatchedAsyncClient

from config.env import AppConfig  # noqa: E402
from container import AppContainer, build_container  # noqa: E402
from module_admin.entity.do.base import LegacyBaseModel  # noqa: E402
from module_admin.entity.do.user_do import UserDO  # noqa: E402

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


def _import_orm_models() -> None:
    """Import all ORM model modules so SQLAlchemy metadata is fully registered."""
    backend_root = Path(__file__).parent.parent
    model_dirs = (
        backend_root / 'module_admin' / 'entity' / 'do',
        backend_root / 'module_generator' / 'entity' / 'do',
    )
    for model_dir in model_dirs:
        if not model_dir.exists():
            continue
        package_prefix = '.'.join(model_dir.relative_to(backend_root).parts)
        for model_file in sorted(model_dir.glob('*_do.py')):
            import_module(f'{package_prefix}.{model_file.stem}')
    import_module('events.models')


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    _import_orm_models()
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(LegacyBaseModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic rollback."""
    test_session_factory = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with test_session_factory() as session:
        # Begin nested transaction
        await session.begin()

        yield session

        # Rollback transaction
        await session.rollback()


@pytest.fixture
async def db_session(test_db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Alias fixture for tests expecting db_session."""
    yield test_db


@pytest.fixture
async def test_user(db_session: AsyncSession) -> UserDO:
    """Create a test user in the database."""
    user = UserDO(
        user_name="test_user",
        nick_name="Test User",
        password="test123",
        status="0",
        del_flag="0",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def app_config() -> AppConfig:
    """Create test application configuration."""
    return AppConfig(
        app_env='test',
        app_debug=True,
        app_host='127.0.0.1',
        app_port=8000,
        database_url=TEST_DATABASE_URL,
        redis_host='localhost',
        redis_port=6379,
        redis_db=0,
        redis_password='',
        jwt_secret_key='test-secret-key',
        jwt_algorithm='HS256',
        jwt_expire_minutes=30,
    )


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client."""
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = True
    mock_client.exists.return_value = False
    return mock_client


@pytest.fixture
def app_container() -> Generator[AppContainer, None, None]:
    """Create app container for dependency override in tests."""
    container = build_container()
    yield container
    container.reset_override()


@pytest.fixture
def app_container_in_server(app_container: AppContainer) -> Generator[AppContainer, None, None]:
    """Attach test container to FastAPI app and restore after test."""
    from server import app  # noqa: PLC0415

    previous_container = getattr(app.state, 'container', None)
    app.state.container = app_container
    try:
        yield app_container
    finally:
        app_container.reset_override()
        if previous_container is None:
            delattr(app.state, 'container')
        else:
            app.state.container = previous_container
