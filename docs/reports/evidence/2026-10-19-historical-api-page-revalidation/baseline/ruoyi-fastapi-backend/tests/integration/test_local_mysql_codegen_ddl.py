"""Opt-in regression for MySQL implicit DDL commits and schema snapshots."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.database import ASYNC_SQLALCHEMY_DATABASE_URL
from config.env import DataBaseConfig
from container import build_container
from exceptions.exception import ResourceConflictException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_generator.entity.do.gen_do import GenTableColumnDO, GenTableDO
from module_generator.repository.gen_repository import GenTableRepository


@pytest.mark.asyncio
async def test_create_after_auth_transaction_imports_columns_without_losing_savepoint():
    if os.environ.get('RUOYI_ACCEPTANCE_LOCAL_MYSQL') != '1':
        pytest.skip('Explicit opt-in for owned temporary tables on local MySQL')
    assert DataBaseConfig.db_type == 'mysql' and DataBaseConfig.db_host in ('127.0.0.1', 'localhost')
    name = f'qa_codegen_{uuid4().hex[:12]}'
    engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    user = CurrentUserModel(user={'userId': 132, 'userName': 'qa-codegen'}, permissions=[], roles=[])
    sql = (
        f"CREATE TABLE {name} (item_id bigint NOT NULL PRIMARY KEY COMMENT '编号', "
        "item_name varchar(80) COMMENT '名称') COMMENT='Owned regression fixture'"
    )
    try:
        async with sessions() as session:
            # Authentication has already opened a transaction before the service.
            await session.execute(text('SELECT 1'))
            service = build_container().resolve_service('gen_table_service', session)
            result = await service.create_table_services(sql, user)
            assert result.result['createdCount'] == 1
            await session.commit()
        async with sessions() as session:
            record = await GenTableRepository(session).find_by_name(name)
            assert record is not None
            assert {column.column_name for column in record.columns} == {'item_id', 'item_name'}
            service = build_container().resolve_service('gen_table_service', session)
            with pytest.raises(ResourceConflictException) as conflict:
                await service.create_table_services(sql, user)
            assert conflict.value.http_status == 409
    finally:
        async with sessions.begin() as session:
            ids = select(GenTableDO.table_id).where(GenTableDO.table_name == name)
            await session.execute(delete(GenTableColumnDO).where(GenTableColumnDO.table_id.in_(ids)))
            await session.execute(delete(GenTableDO).where(GenTableDO.table_name == name))
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP TABLE IF EXISTS {name}'))
        await engine.dispose()
