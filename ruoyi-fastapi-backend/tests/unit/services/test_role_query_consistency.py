"""Role editor reads must not reuse cross-transaction or cross-scope result snapshots."""

import asyncio
import fnmatch
from unittest.mock import AsyncMock

import pytest

from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.vo.menu_vo import MenuQueryModel
from module_admin.entity.vo.role_vo import RolePageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.application.services import menu_service as menu_module
from modules.system.application.services import role_service as role_module
from modules.system.application.services.menu_service import MenuService
from modules.system.application.services.role_service import RoleService
from utils.page_util import PageResponseModel
from utils.query_cache import QueryCache


class MemoryRedis:
    """Exercise the production cache implementation without a Redis or database connection."""

    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, _ttl, value):
        self.values[key] = value

    async def keys(self, pattern):
        return [key for key in self.values if fnmatch.fnmatch(key, pattern)]

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)


@pytest.fixture
def query_cache(monkeypatch):
    cache = QueryCache(MemoryRedis(), key_prefix='owned_role_regression', is_async=True)
    monkeypatch.setattr(role_module, 'get_query_cache', lambda: cache, raising=False)
    monkeypatch.setattr(menu_module, 'get_query_cache', lambda: cache, raising=False)
    return cache


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'resource', ['role_list', 'role_select', 'role_detail', 'menu_tree', 'role_menu_tree', 'menu_list']
)
async def test_completed_old_read_cannot_poison_next_independent_read(resource, query_cache):
    """A real service read pauses after its repository snapshot, across a write's invalidation."""
    state = {'version': 1, 'calls': 0}
    loaded = asyncio.Event()
    release = asyncio.Event()

    async def snapshot(*_args, **_kwargs):
        state['calls'] += 1
        version = state['version']
        if state['calls'] == 1:
            loaded.set()
            await release.wait()
        return version

    async def role_page(**kwargs):
        version = await snapshot()
        return PageResponseModel(
            items=[{'roleId': version}], total=1, page=kwargs['page'], pageSize=kwargs['page_size']
        )

    async def roles():
        return [{'roleId': await snapshot()}]

    async def role(*_):
        return RoleDO(role_id=7, role_name=f'v{await snapshot()}', role_key='owned', role_sort=0)

    async def menus(*_args, **_kwargs):
        return [MenuDO(menu_id=await snapshot(), menu_name='owned', parent_id=0)]

    async def relations(*_):
        return [RoleMenuDO(role_id=7, menu_id=await snapshot())]

    role_repo = AsyncMock()
    role_repo.paginate_with_filters.side_effect = role_page
    role_repo.find_all_active.side_effect = roles
    role_repo.find_active_by_id.side_effect = role
    role_repo.find_by_id.side_effect = role if resource == 'role_detail' else None
    role_repo.find_by_id.return_value = RoleDO(role_id=7, role_name='owned', role_key='owned', role_sort=0)
    role_menu_repo = AsyncMock()
    role_menu_repo.find_by_role_id.side_effect = relations
    menu_repo = AsyncMock()
    menu_repo.find_all_active.side_effect = menus if resource != 'role_menu_tree' else None
    menu_repo.find_all_active.return_value = []
    menu_repo.find_with_filters.side_effect = menus
    roles_service = RoleService(role_repo, role_menu_repo, AsyncMock(), AsyncMock(), AsyncMock())
    menus_service = MenuService(menu_repo, role_repo, role_menu_repo, AsyncMock())
    operator = CurrentUserModel(user=UserInfoModel(userId=1), roles=['admin'], permissions=['*:*:*'])
    reads = {
        'role_list': lambda: roles_service.get_role_list_services(RolePageQueryModel(), True, is_page=True),
        'role_select': roles_service.get_role_select_option_services,
        'role_detail': lambda: roles_service.role_detail_services(7),
        'menu_tree': lambda: menus_service.get_menu_tree_services(operator),
        'role_menu_tree': lambda: menus_service.get_role_menu_tree_services(7, operator),
        'menu_list': lambda: menus_service.get_menu_list_services(MenuQueryModel(), operator),
    }
    read = reads[resource]
    old = asyncio.create_task(read())
    try:
        await asyncio.wait_for(loaded.wait(), 2)
        state['version'] = 2
        # This is precisely the cache delete done by the existing write path; HTTP exercises the full transaction.
        await query_cache.delete_pattern(f'{query_cache.key_prefix}:*')
        release.set()
        await old
        fresh = await read()
    finally:
        release.set()
        await old
    version_of = {
        'role_list': lambda item: item.items[0]['roleId'],
        'role_select': lambda item: item[0]['roleId'],
        'role_detail': lambda item: int(item.role_name.removeprefix('v')),
        'menu_tree': lambda item: item[0]['id'],
        'role_menu_tree': lambda item: item.checked_keys[0],
        'menu_list': lambda item: item[0]['menuId'],
    }
    assert version_of[resource](fresh) == 2
    assert state['calls'] == 2


@pytest.mark.asyncio
async def test_role_list_keeps_bound_data_scope_values_isolated(query_cache):
    repo = AsyncMock()

    async def page(**kwargs):
        scope_id = next(iter(kwargs['data_scope_sql'].compile().params.values()))
        return PageResponseModel(items=[{'roleId': scope_id}], total=1, page=1, pageSize=10)

    repo.paginate_with_filters.side_effect = page
    service = RoleService(repo, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())
    first = await service.get_role_list_services(RolePageQueryModel(), DeptDO.dept_id == 7, is_page=True)
    second = await service.get_role_list_services(RolePageQueryModel(), DeptDO.dept_id == 8, is_page=True)
    assert first.items == [{'roleId': 7}]
    assert second.items == [{'roleId': 8}]
