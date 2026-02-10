"""
Shared pytest fixtures and configuration for all tests.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import httpx
from httpx import ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


_OriginalAsyncClient = httpx.AsyncClient


class _PatchedAsyncClient(_OriginalAsyncClient):
    def __init__(self, *args, app=None, base_url=None, **kwargs):
        if app is not None:
            kwargs.setdefault('transport', ASGITransport(app=app))
        if base_url is not None:
            kwargs.setdefault('base_url', base_url)
        super().__init__(*args, **kwargs)


httpx.AsyncClient = _PatchedAsyncClient

from config.env import AppConfig
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.user_do import UserDO

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def test_engine():
    """Create test database engine."""
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
    TestSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with TestSessionLocal() as session:
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
