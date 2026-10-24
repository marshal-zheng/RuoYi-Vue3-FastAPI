from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlglot import parse

from exceptions.exception import ResourceConflictException, ValidationException
from module_generator.repository.gen_repository import GenTableRepository
from module_generator.service.gen_service import GenTableService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'sql',
    [
        '',
        'SELECT 1',
        'CREATE TABLE own (id INT); SELECT 1',
        'CREATE VIEW own AS SELECT 1',
        'CREATE TABLE own AS SELECT 1',
        'CREATE TABLE other_db.own (id INT)',
        'CREATE TABLE own (',
        'CREATE TABLE own (id INT); CREATE TABLE own (name TEXT)',
    ],
)
async def test_invalid_sql_is_rejected_before_any_ddl(sql):
    repository = SimpleNamespace(execute_sql_statements=AsyncMock(), get_db_tables_by_names=AsyncMock(return_value=[]))
    service = GenTableService(repository, Mock(), Mock())
    with pytest.raises(ValidationException) as error:
        await service.create_table_services.__wrapped__(service, sql, Mock())
    assert error.value.http_status == 422
    repository.execute_sql_statements.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_table_is_a_conflict_without_ddl_or_duplicate_import():
    repository = SimpleNamespace(
        execute_sql_statements=AsyncMock(),
        get_db_tables_by_names=AsyncMock(return_value=[{'table_name': 'own', 'table_comment': 'Owned'}]),
    )
    service = GenTableService(repository, Mock(), Mock())
    with pytest.raises(ResourceConflictException) as error:
        await service.create_table_services.__wrapped__(service, 'CREATE TABLE own (id INT)', Mock())
    assert error.value.http_status == 409
    repository.execute_sql_statements.assert_not_awaited()


@pytest.mark.asyncio
async def test_ddl_uses_an_independent_connection_without_touching_request_savepoint():
    connection = SimpleNamespace(execute=AsyncMock())
    manager = AsyncMock()
    manager.__aenter__.return_value = connection
    session = SimpleNamespace(bind=SimpleNamespace(begin=Mock(return_value=manager)), execute=AsyncMock())
    await GenTableRepository(session).execute_sql_statements(parse('CREATE TABLE own (id INT)', dialect='mysql'))
    session.execute.assert_not_awaited()
    assert connection.execute.await_count == 1
    assert 'CREATE TABLE own' in str(connection.execute.await_args.args[0])
