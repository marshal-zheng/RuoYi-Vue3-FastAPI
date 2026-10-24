from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.database import Base
from container import AppContainer
from module_admin.entity.do.config_do import ConfigDO
from modules.system.infrastructure.config_repository import ConfigRepository
from tests.fakes.external_fakes import InMemoryRedisClient


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Use application cache wiring and an isolated real database, without external services."""
    container = AppContainer()
    await container.initialize_runtime(redis_client=InMemoryRedisClient(), initialize_scheduler=False)
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync: Base.metadata.create_all(sync, tables=[ConfigDO.__table__]))
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await container.shutdown_runtime()
        await engine.dispose()


def config(key: str, *, kind: str = 'N') -> ConfigDO:
    return ConfigDO(config_name=key, config_key=key, config_value='value', config_type=kind)


@pytest.mark.asyncio
async def test_total_tracks_committed_create_delete_and_pages(sessions):
    async with sessions() as db:
        repository = ConfigRepository(db)
        assert (await repository.paginate_with_filters(1, 1)).total == 0
        await repository.add_all([config('first'), config('second')])
        await db.commit()
        first = await repository.paginate_with_filters(1, 1)
        second = await repository.paginate_with_filters(2, 1)
        assert first.total == second.total == 2
        assert len(first.items) == len(second.items) == 1
        assert first.items[0]['configId'] != second.items[0]['configId']
        await repository.delete_by_id(first.items[0]['configId'])
        await db.commit()
        remaining = await repository.paginate_with_filters(1, 1)
        past_end = await repository.paginate_with_filters(2, 1)
        assert remaining.total == past_end.total == 1
        assert len(remaining.items) == 1
        assert past_end.items == []
        await repository.delete_by_ids([remaining.items[0]['configId']])
        await db.commit()
        empty = await repository.paginate_with_filters(1, 1)
        assert empty.total == 0
        assert empty.items == []


@pytest.mark.asyncio
async def test_uncommitted_count_does_not_escape_after_rollback(sessions):
    async with sessions() as writer:
        repository = ConfigRepository(writer)
        await repository.add(config('rolled-back'))
        local = await repository.paginate_with_filters(1, 10)
        assert local.total == len(local.items) == 1
        await writer.rollback()
    async with sessions() as reader:
        committed = await ConfigRepository(reader).paginate_with_filters(1, 10)
        assert committed.total == 0
        assert committed.items == []


@pytest.mark.asyncio
async def test_total_uses_current_filter_after_update(sessions):
    async with sessions() as db:
        repository = ConfigRepository(db)
        item = await repository.add(config('filtered'))
        await db.commit()
        assert (await repository.paginate_with_filters(1, 10, config_type='N')).total == 1
        assert (await repository.paginate_with_filters(1, 10, config_type='Y')).total == 0
        item.config_type = 'Y'
        await repository.update(item)
        await db.commit()
        old_filter = await repository.paginate_with_filters(1, 10, config_type='N')
        new_filter = await repository.paginate_with_filters(1, 10, config_type='Y')
        assert old_filter.total == len(old_filter.items) == 0
        assert new_filter.total == len(new_filter.items) == 1
