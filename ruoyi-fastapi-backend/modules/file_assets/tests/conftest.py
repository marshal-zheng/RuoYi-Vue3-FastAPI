"""Fixtures for file asset tests: in-memory SQLite + fake storage (no real DB/S3 semantics claimed)."""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

import pytest
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import container.file_asset_policies  # noqa: F401 - registers the business owner policies
from config.database import Base
from config.env import FileAssetSettings
from module_admin.entity.do.notice_do import NoticeDO
from module_admin.entity.do.user_do import UserDO
from modules.file_assets.application.asset_service import AssetService, IncomingFile
from modules.file_assets.application.binding_service import BindingService
from modules.file_assets.application.cleanup_service import CleanupService
from modules.file_assets.application.composition import get_policy_registry
from modules.file_assets.application.runtime import FileAssetRuntime, OwnershipState
from modules.file_assets.domain.models import Actor, UploadEntry
from modules.file_assets.infrastructure import models as _asset_models  # noqa: F401 - registers the asset tables
from modules.file_assets.infrastructure.models import FileAssetDO
from modules.file_assets.tests.fakes import FakeStorage


def make_settings(**overrides) -> FileAssetSettings:
    values = {
        'file_asset_s3_endpoint': 'http://s3.test',
        'file_asset_s3_bucket': 'test-bucket',
        'file_asset_s3_access_key': SecretStr('app'),
        'file_asset_s3_secret_key': SecretStr('secret'),
        'file_asset_installation_id': 'test-installation',
        'file_asset_slot_wait_seconds': 0.2,
    }
    values.update(overrides)
    return FileAssetSettings(**values)


@pytest.fixture
async def engine():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:', poolclass=StaticPool, connect_args={'check_same_thread': False}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def settings():
    return make_settings()


@pytest.fixture
async def runtime(settings, storage):
    runtime = FileAssetRuntime(settings, storage)
    runtime.ownership.state = OwnershipState.CONFIRMED
    yield runtime
    await runtime.stop()


@pytest.fixture
def registry():
    return get_policy_registry()


@pytest.fixture
def assets(runtime, registry, session_factory):
    return AssetService(runtime, registry, session_factory)


@pytest.fixture
def bindings(registry):
    return BindingService(registry, delete_grace_hours=24)


@pytest.fixture
def cleanup(runtime, session_factory):
    return CleanupService(runtime, session_factory)


@pytest.fixture
async def seeded(session_factory):
    async with session_factory() as session:
        session.add_all(
            [
                UserDO(user_id=1, user_name='admin', nick_name='admin', del_flag='0'),
                UserDO(user_id=2, user_name='editor', nick_name='editor', del_flag='0'),
                UserDO(user_id=3, user_name='reader', nick_name='reader', del_flag='0'),
                UserDO(user_id=4, user_name='gone', nick_name='gone', del_flag='2'),
                NoticeDO(notice_id=10, notice_title='n10', notice_type='1', notice_content='<p></p>'),
                NoticeDO(notice_id=11, notice_title='n11', notice_type='1', notice_content='<p></p>'),
            ]
        )
        await session.commit()


ADMIN = Actor(user_id=1, permissions=frozenset({'*:*:*'}))
EDITOR = Actor(user_id=2, permissions=frozenset({'system:notice:add', 'system:notice:edit', 'system:notice:list'}))
READER = Actor(user_id=3, permissions=frozenset({'system:notice:query'}))
NOBODY = Actor(user_id=3, permissions=frozenset())


def png_bytes(size=(32, 24), color='red') -> bytes:
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, 'PNG')
    return buffer.getvalue()


def incoming(data: bytes, filename: str = 'image.png', content_type: str | None = 'image/png') -> IncomingFile:
    stream = io.BytesIO(data)
    return IncomingFile(stream=stream, filename=filename, content_type=content_type, close=stream.close)


async def upload(
    assets, actor, purpose='notice.image', owner_id=None, data=None, filename='image.png', content_type='image/png'
):
    spec = assets.registry.purpose(purpose)
    entry = spec.upload_entry if spec.upload_entry is UploadEntry.DEDICATED else UploadEntry.GENERIC
    slot = await assets.runtime.upload_slots.acquire()
    return await assets.upload(
        actor=actor,
        spec=assets.resolve_purpose(purpose, entry=entry),
        owner_id=owner_id,
        incoming=incoming(data if data is not None else png_bytes(), filename, content_type),
        slot=slot,
    )


async def asset_row(session_factory, asset_id) -> FileAssetDO:
    async with session_factory() as session:
        return await session.get(FileAssetDO, asset_id)


async def shift_asset(session_factory, asset_id, **delta_fields):
    """Move lifecycle timestamps into the past (fake clock for SQLite tests)."""
    async with session_factory() as session:
        row = await session.get(FileAssetDO, asset_id)
        values = {}
        for name, delta in delta_fields.items():
            current = getattr(row, name)
            values[name] = (current or datetime.now(UTC).replace(tzinfo=None)) - delta
        await session.execute(update(FileAssetDO).where(FileAssetDO.asset_id == asset_id).values(**values))
        await session.commit()


HOUR = timedelta(hours=1)
