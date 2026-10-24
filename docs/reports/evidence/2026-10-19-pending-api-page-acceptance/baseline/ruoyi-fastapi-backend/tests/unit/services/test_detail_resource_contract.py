"""Single-resource reads require an existing entity; collections keep their own semantics."""

from importlib import import_module
from inspect import signature
from unittest.mock import AsyncMock, MagicMock

import pytest

from exceptions.exception import ResourceNotFoundException

CASES = [
    (
        'modules.system.application.services.config_service',
        'ConfigService',
        'config_repo',
        'config_detail_services',
        'config_id',
    ),
    (
        'modules.system.application.services.dict_type_service',
        'DictTypeService',
        'dict_type_repo',
        'dict_type_detail_services',
        'dict_id',
    ),
    (
        'modules.system.application.services.dict_data_service',
        'DictDataService',
        'dict_data_repo',
        'dict_data_detail_services',
        'dict_code',
    ),
    ('modules.system.application.services.dept_service', 'DeptService', 'dept_repo', 'dept_detail_services', 'dept_id'),
    ('modules.system.application.services.role_service', 'RoleService', 'role_repo', 'role_detail_services', 'role_id'),
    ('modules.system.application.services.menu_service', 'MenuService', 'menu_repo', 'menu_detail_services', 'menu_id'),
    ('modules.system.application.services.post_service', 'PostService', 'post_repo', 'post_detail_services', 'post_id'),
    (
        'modules.system.application.services.notice_service',
        'NoticeService',
        'notice_repo',
        'notice_detail_services',
        'notice_id',
    ),
    (
        'modules.project.application.services.project_service',
        'ProjectService',
        'project_repo',
        'project_detail_services',
        'project_id',
    ),
    (
        'modules.project.application.services.project_version_service',
        'ProjectVersionService',
        'version_repo',
        'project_version_detail_services',
        'version_id',
    ),
    (
        'module_generator.service.gen_service',
        'GenTableService',
        'table_repo',
        'get_gen_table_by_id_services',
        'table_id',
    ),
    ('modules.scheduler.application.job_service', 'JobService', 'job_repo', 'job_detail_services', 'job_id'),
    (
        'module_admin.service.protocol_service',
        'ProtocolService',
        'protocol_repo',
        'protocol_detail_services',
        'protocol_id',
    ),
]


def make_service(case, monkeypatch, *, row=None, cached=None):
    module_name, class_name, repo_name, _, _ = case
    module = import_module(module_name)
    cls = getattr(module, class_name)
    repo = MagicMock()
    repo.find_by_id = AsyncMock(return_value=row)
    repo.find_by_code = AsyncMock(return_value=row)
    repo.find_active_by_id = AsyncMock(return_value=row)
    service = cls(**{name: repo if name == repo_name else MagicMock() for name in signature(cls).parameters})
    cache = MagicMock(key_prefix='query_cache')
    cache.build_key.return_value = 'query_cache:detail:42'
    cache.get = AsyncMock(return_value=cached)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    if hasattr(module, 'get_query_cache'):
        monkeypatch.setattr(module, 'get_query_cache', lambda: cache)
    return service, repo, cache


@pytest.mark.parametrize('case', CASES, ids=lambda case: case[1])
async def test_missing_detail_raises_existing_404(case, monkeypatch):
    service, _, cache = make_service(case, monkeypatch)
    with pytest.raises(ResourceNotFoundException) as failure:
        await getattr(service, case[3])(42)
    assert failure.value.http_status == 404
    assert failure.value.error_code != 50000
    cache.set.assert_not_awaited()


@pytest.mark.parametrize('case', CASES, ids=lambda case: case[1])
async def test_existing_detail_retains_its_identity(case, monkeypatch):
    service, _, _ = make_service(case, monkeypatch, row={case[4]: 42})
    result = await getattr(service, case[3])(42)
    if hasattr(result, 'model_dump'):
        result = result.model_dump(by_alias=False)
    camel = case[4].split('_')[0] + ''.join(part.title() for part in case[4].split('_')[1:])
    assert result.get(case[4], result.get(camel)) == 42


# Only menu details retain a result cache; role/dept reads live in test_uncached_detail_contract.py.
@pytest.mark.parametrize('case', [CASES[5]], ids=lambda case: case[1])
@pytest.mark.parametrize('cached_id', [None, 999])
async def test_old_invalid_detail_cache_is_removed_and_missing_entity_still_404(case, cached_id, monkeypatch):
    camel = case[4].split('_')[0] + ''.join(part.title() for part in case[4].split('_')[1:])
    service, repo, cache = make_service(case, monkeypatch, cached={camel: cached_id})
    with pytest.raises(ResourceNotFoundException):
        await getattr(service, case[3])(42)
    cache.delete.assert_awaited_once_with(cache.build_key.return_value)
    assert repo.find_by_id.await_count + repo.find_active_by_id.await_count == 1
    cache.set.assert_not_awaited()
