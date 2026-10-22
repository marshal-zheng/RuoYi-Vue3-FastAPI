import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.database import Base
from module_generator.entity.do.gen_do import GenTableColumnDO, GenTableDO
from module_generator.repository.gen_repository import GenTableRepository


@pytest.mark.asyncio
async def test_imported_generator_metadata_uses_current_database_count():
    """Imported metadata must be reflected immediately in the next page total."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                lambda sync: Base.metadata.create_all(sync, tables=[GenTableDO.__table__, GenTableColumnDO.__table__])
            )
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            repository = GenTableRepository(db)
            db.add(GenTableDO(table_name='sys_post', table_comment='岗位'))
            await db.commit()
            first = await repository.paginate_with_filters(page=1, page_size=10)
            assert first.total == 1
            assert [item['tableName'] for item in first.items] == ['sys_post']

            db.add(GenTableDO(table_name='sys_role', table_comment='角色'))
            await db.commit()
            second = await repository.paginate_with_filters(page=1, page_size=10)
            assert second.total == 2
            assert len(second.items) == 2
    finally:
        await engine.dispose()
