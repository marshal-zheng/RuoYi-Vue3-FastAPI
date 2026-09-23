"""
Unit tests for RoleService instance-method paths.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config.constant import CommonConstant
from exceptions.exception import PermissionException
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.user_vo import UserRolePageQueryModel
from modules.system.application.services.role_service import RoleService
from utils.page_util import PageResponseModel


class FakeCache:
    def __init__(self):
        self.key_prefix = 'cache'
        self._store = {}
        self.deleted_patterns = []
        self.get = AsyncMock(side_effect=self._get_impl)
        self.set = AsyncMock(side_effect=self._set_impl)
        self.delete_pattern = AsyncMock(side_effect=self._delete_pattern_impl)

    def build_key(self, prefix: str, payload: dict) -> str:
        return f'{prefix}:{payload}'

    async def _get_impl(self, key):
        return self._store.get(key)

    async def _set_impl(self, key, value, ttl):
        self._store[key] = value

    async def _delete_pattern_impl(self, pattern):
        self.deleted_patterns.append(pattern)


def build_service(role_repo=None):
    return RoleService(
        role_repo=role_repo or AsyncMock(),
        role_menu_repo=AsyncMock(),
        role_dept_repo=AsyncMock(),
        user_repo=AsyncMock(),
        query_db=AsyncMock(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('allocation', ['allocated', 'unallocated'])
async def test_role_user_list_preserves_joined_department_and_page_contract(allocation):
    service = build_service()
    repository = getattr(service.user_repo, f'paginate_{allocation}_by_role')
    repository.return_value = PageResponseModel(
        items=[
            [{'userId': 2, 'userName': 'joined'}, {'deptId': 7, 'deptName': '研发'}],
            [{'userId': 3, 'userName': 'without-department'}, None],
        ],
        page=2,
        page_size=10,
        total=12,
    )

    result = await getattr(service, f'get_role_user_{allocation}_list_services')(
        UserRolePageQueryModel(role_id=5, page=2, page_size=10), 'True', is_page=True
    )

    assert result.page == 2
    assert result.page_size == 10
    assert result.total == 12
    assert result.items[0].user_id == 2
    assert result.items[0].dept.dept_name == '研发'
    assert result.items[1].user_id == 3
    assert result.items[1].dept is None
    repository.assert_awaited_once_with(
        role_id=5, page=2, page_size=10, user_name=None, phonenumber=None, data_scope_sql='True'
    )


class TestRoleServiceAccessControl:
    @pytest.mark.asyncio
    async def test_check_role_allowed_rejects_admin(self):
        admin_role = RoleModel(role_id=1, role_name='admin', role_key='admin')
        service = build_service()

        with pytest.raises(PermissionException):
            await service.check_role_allowed_services(admin_role)

    @pytest.mark.asyncio
    async def test_check_role_allowed_passes_non_admin(self):
        role = RoleModel(role_id=2, role_name='common', role_key='common')
        service = build_service()

        result = await service.check_role_allowed_services(role)

        assert result.is_success is True
        assert result.message == '校验通过'


class TestRoleServiceUniquenessChecks:
    @pytest.mark.asyncio
    async def test_check_role_name_unique_returns_not_unique(self):
        role_repo = AsyncMock()
        role_repo.find_by_name.return_value = SimpleNamespace(role_id=2)
        service = build_service(role_repo=role_repo)
        role = RoleModel(role_id=1, role_name='ops')

        result = await service.check_role_name_unique_services(role)

        assert result is CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_role_key_unique_returns_unique_when_same_id(self):
        role_repo = AsyncMock()
        role_repo.find_by_key.return_value = SimpleNamespace(role_id=3)
        service = build_service(role_repo=role_repo)
        role = RoleModel(role_id=3, role_key='ops')

        result = await service.check_role_key_unique_services(role)

        assert result is CommonConstant.UNIQUE


class TestRoleServiceDataScope:
    @pytest.mark.asyncio
    async def test_check_role_data_scope_raises_when_role_out_of_scope(self):
        role_repo = AsyncMock()

        async def _paginate_with_filters(**kwargs):
            if kwargs.get('role_id') == 1:
                return SimpleNamespace(items=[{'role_id': 1}])
            return SimpleNamespace(items=[])

        role_repo.paginate_with_filters.side_effect = _paginate_with_filters
        service = build_service(role_repo=role_repo)

        with pytest.raises(PermissionException):
            await service.check_role_data_scope_services('1,2', '1=1')


class TestRoleServiceCacheAndExport:
    @pytest.mark.asyncio
    async def test_role_detail_uses_cache_when_hit(self, monkeypatch):
        cache = FakeCache()
        key = cache.build_key('role:detail', {'role_id': 7})
        cache._store[key] = {'roleId': 7, 'roleName': 'cached', 'roleKey': 'cached'}

        monkeypatch.setattr('modules.system.application.services.role_service.get_query_cache', lambda: cache)
        service = build_service(role_repo=AsyncMock())

        result = await service.role_detail_services(7)

        assert result.role_id == 7
        assert result.role_name == 'cached'

    @pytest.mark.asyncio
    async def test_invalidate_role_cache_deletes_expected_patterns(self, monkeypatch):
        cache = FakeCache()
        monkeypatch.setattr('modules.system.application.services.role_service.get_query_cache', lambda: cache)

        await RoleService._invalidate_role_cache()

        assert f'{cache.key_prefix}:role:*' in cache.deleted_patterns
        assert f'{cache.key_prefix}:menu:role_tree:*' in cache.deleted_patterns
        assert f'{cache.key_prefix}:menu:tree:*' in cache.deleted_patterns
        assert f'{cache.key_prefix}:menu:list:*' in cache.deleted_patterns

    @pytest.mark.asyncio
    async def test_export_role_list_maps_status_before_export(self, monkeypatch):
        captured = {}

        def fake_export(rows, mapping):
            captured['rows'] = rows
            captured['mapping'] = mapping
            return b'role-bytes'

        monkeypatch.setattr('modules.system.application.services.role_service.ExcelUtil.export_list2excel', fake_export)
        rows = [
            {'roleId': 1, 'status': '0'},
            {'roleId': 2, 'status': '1'},
        ]

        data = await RoleService.export_role_list_services(rows)

        assert data == b'role-bytes'
        assert captured['rows'][0]['status'] == '正常'
        assert captured['rows'][1]['status'] == '停用'
