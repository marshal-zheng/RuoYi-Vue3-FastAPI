"""Management detail reads use current rows, including disabled rows, and preserve 404."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from exceptions.exception import ResourceNotFoundException
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.role_do import RoleDO
from modules.system.application.services.dept_service import DeptService
from modules.system.application.services.role_service import RoleService
from modules.system.infrastructure.dept_repository import DeptRepository
from modules.system.infrastructure.role_repository import RoleRepository


@pytest.fixture(params=['department', 'role'])
def detail_reader(request, db_session):
    if request.param == 'department':
        service = DeptService(DeptRepository(db_session), db_session)
        entity = DeptDO(dept_id=42, dept_name='Before', parent_id=0, ancestors='0', status='1', del_flag='0')
        return service.dept_detail_services, entity, 'dept_id', 'dept_name'
    service = RoleService(RoleRepository(db_session), AsyncMock(), AsyncMock(), AsyncMock(), db_session)
    entity = RoleDO(role_id=42, role_name='Before', role_key='owned', role_sort=1, status='1', del_flag='0')
    return service.role_detail_services, entity, 'role_id', 'role_name'


@pytest.fixture
def obsolete_result_cache(monkeypatch):
    cache = MagicMock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    # The real cache provider still serves other resources. Do not recreate removed service symbols.
    monkeypatch.setattr('utils.query_cache._query_cache', cache)
    return cache


@pytest.mark.parametrize('cached_id', [None, 999])
@pytest.mark.parametrize('missing_kind', ['absent', 'soft-deleted'])
async def test_missing_uncached_detail_is_404_even_with_obsolete_cache(
    detail_reader, obsolete_result_cache, db_session, cached_id, missing_kind
):
    read, entity, id_field, _ = detail_reader
    obsolete_result_cache.get.return_value = {id_field: cached_id}
    if missing_kind == 'soft-deleted':
        entity.del_flag = '2'
        db_session.add(entity)
        await db_session.flush()

    with pytest.raises(ResourceNotFoundException) as failure:
        await read(42)

    assert failure.value.http_status == 404
    obsolete_result_cache.get.assert_not_awaited()
    obsolete_result_cache.set.assert_not_awaited()
    obsolete_result_cache.delete.assert_not_awaited()


async def test_disabled_detail_reads_latest_repository_row(detail_reader, obsolete_result_cache, db_session):
    read, entity, id_field, name_field = detail_reader
    obsolete_result_cache.get.return_value = {id_field: 999, name_field: 'Obsolete'}
    db_session.add(entity)
    await db_session.flush()

    first = await read(42)
    assert getattr(first, id_field) == 42
    assert getattr(first, name_field) == 'Before'
    assert first.status == '1'

    setattr(entity, name_field, 'After')
    await db_session.flush()
    second = await read(42)
    assert getattr(second, id_field) == 42
    assert getattr(second, name_field) == 'After'
    assert getattr(first, name_field) == 'Before'
    obsolete_result_cache.get.assert_not_awaited()
    obsolete_result_cache.set.assert_not_awaited()
    obsolete_result_cache.delete.assert_not_awaited()
