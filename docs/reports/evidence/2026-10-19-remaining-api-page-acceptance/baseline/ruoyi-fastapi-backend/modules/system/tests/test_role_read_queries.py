from __future__ import annotations

import asyncio

import pytest

from module_admin.entity.vo.role_vo import RolePageQueryModel
from module_admin.entity.vo.user_vo import UserRolePageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.role_query_handlers import (
    GetRoleAllocatedUsersQueryHandler,
    GetRoleDeptTreeQueryHandler,
    GetRoleDetailQueryHandler,
    GetRoleListQueryHandler,
    GetRoleUnallocatedUsersQueryHandler,
)
from modules.system.application.queries import (
    GetRoleAllocatedUsersQuery,
    GetRoleDeptTreeQuery,
    GetRoleDetailQuery,
    GetRoleListQuery,
    GetRoleUnallocatedUsersQuery,
)
from modules.system.application.read_models import (
    RoleDeptTreeReadModel,
    RoleDetailReadModel,
    RolePageReadModel,
    RoleUserPageReadModel,
)
from utils.page_util import PageResponseModel


class _DeptServiceStub:
    def __init__(self, *, delay_first_call_seconds: float = 0.0) -> None:
        self.tree_called_with = None
        self.tree_call_count = 0
        self.delay_first_call_seconds = delay_first_call_seconds

    async def get_dept_tree_services(self, query, data_scope_sql):
        self.tree_call_count += 1
        if self.tree_call_count == 1 and self.delay_first_call_seconds > 0:
            await asyncio.sleep(self.delay_first_call_seconds)
        self.tree_called_with = (query, data_scope_sql)
        return [
            {
                'id': 1,
                'label': '总公司',
                'parentId': 0,
            }
        ]


class _RoleServiceStub:
    def __init__(self, *, delay_dept_tree_first_call_seconds: float = 0.0) -> None:
        self.dept_tree_called_with = None
        self.dept_tree_call_count = 0
        self.delay_dept_tree_first_call_seconds = delay_dept_tree_first_call_seconds
        self.list_called_with = None
        self.scope_check_called_with = None
        self.detail_called_with = None
        self.allocated_called_with = None
        self.unallocated_called_with = None

    async def get_role_dept_tree_services(self, role_id):
        self.dept_tree_call_count += 1
        if self.dept_tree_call_count == 1 and self.delay_dept_tree_first_call_seconds > 0:
            await asyncio.sleep(self.delay_dept_tree_first_call_seconds)
        self.dept_tree_called_with = role_id
        return {'checkedKeys': [1]}

    async def get_role_list_services(self, query, data_scope_sql, is_page=False):
        self.list_called_with = (query, data_scope_sql, is_page)
        if is_page:
            return PageResponseModel(
                items=[
                    {
                        'roleId': 1,
                        'roleName': '管理员',
                        'roleKey': 'admin',
                        'status': '0',
                    }
                ],
                page=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'roleId': 1,
                'roleName': '管理员',
                'roleKey': 'admin',
                'status': '0',
            }
        ]

    async def check_role_data_scope_services(self, role_ids, data_scope_sql):
        self.scope_check_called_with = (role_ids, data_scope_sql)

    async def role_detail_services(self, role_id):
        self.detail_called_with = role_id
        return {
            'roleId': role_id,
            'roleName': '管理员',
            'roleKey': 'admin',
            'status': '0',
        }

    async def get_role_user_allocated_list_services(self, query, data_scope_sql, is_page=False):
        self.allocated_called_with = (query, data_scope_sql, is_page)
        return PageResponseModel(
            items=[
                {
                    'userId': 1,
                    'userName': 'admin',
                    'nickName': '管理员',
                    'status': '0',
                }
            ],
            page=1,
            page_size=10,
            total=1,
            has_next=False,
        )

    async def get_role_user_unallocated_list_services(self, query, data_scope_sql, is_page=False):
        self.unallocated_called_with = (query, data_scope_sql, is_page)
        return PageResponseModel(
            items=[
                {
                    'userId': 2,
                    'userName': 'test',
                    'nickName': '测试用户',
                    'status': '0',
                }
            ],
            page=1,
            page_size=10,
            total=1,
            has_next=False,
        )


@pytest.mark.asyncio
async def test_role_query_handlers_success() -> None:
    dept_service = _DeptServiceStub()
    role_service = _RoleServiceStub()

    dept_tree_handler = GetRoleDeptTreeQueryHandler(role_service, dept_service)
    list_handler = GetRoleListQueryHandler(role_service)
    detail_handler = GetRoleDetailQueryHandler(role_service)
    allocated_handler = GetRoleAllocatedUsersQueryHandler(role_service)
    unallocated_handler = GetRoleUnallocatedUsersQueryHandler(role_service)

    dept_tree_result = await dept_tree_handler.handle(
        GetRoleDeptTreeQuery(role_id=1, data_scope_sql=' AND dept_id in (1)', operator='admin')
    )
    list_result = await list_handler.handle(
        GetRoleListQuery(
            query=RolePageQueryModel(page=1, pageSize=10),
            data_scope_sql=' AND role_id in (1)',
            is_page=True,
            operator='admin',
        )
    )
    detail_result = await detail_handler.handle(
        GetRoleDetailQuery(
            role_id=1,
            data_scope_sql=' AND role_id in (1)',
            require_scope_check=True,
            operator='admin',
        )
    )
    allocated_result = await allocated_handler.handle(
        GetRoleAllocatedUsersQuery(
            query=UserRolePageQueryModel(roleId=1, page=1, pageSize=10),
            data_scope_sql=' AND user_id in (1)',
            is_page=True,
            operator='admin',
        )
    )
    unallocated_result = await unallocated_handler.handle(
        GetRoleUnallocatedUsersQuery(
            query=UserRolePageQueryModel(roleId=1, page=1, pageSize=10),
            data_scope_sql=' AND user_id in (1,2)',
            is_page=True,
            operator='admin',
        )
    )

    assert isinstance(dept_tree_result, RoleDeptTreeReadModel)
    assert isinstance(list_result, RolePageReadModel)
    assert isinstance(detail_result, RoleDetailReadModel)
    assert isinstance(allocated_result, RoleUserPageReadModel)
    assert isinstance(unallocated_result, RoleUserPageReadModel)
    assert detail_result.role_id == 1
    assert role_service.scope_check_called_with == ('1', ' AND role_id in (1)')


@pytest.mark.asyncio
async def test_role_detail_query_handler_skips_scope_check_when_not_required() -> None:
    role_service = _RoleServiceStub()
    detail_handler = GetRoleDetailQueryHandler(role_service)

    detail_result = await detail_handler.handle(
        GetRoleDetailQuery(
            role_id=1,
            data_scope_sql=' AND role_id in (1)',
            require_scope_check=False,
        )
    )

    assert isinstance(detail_result, RoleDetailReadModel)
    assert role_service.scope_check_called_with is None


@pytest.mark.asyncio
async def test_role_dept_tree_query_handler_fallback_when_composed_timeout() -> None:
    dept_service = _DeptServiceStub(delay_first_call_seconds=0.02)
    role_service = _RoleServiceStub(delay_dept_tree_first_call_seconds=0.02)
    handler = GetRoleDeptTreeQueryHandler(role_service, dept_service, timeout_seconds=0.001)

    result = await handler.handle(GetRoleDeptTreeQuery(role_id=1, data_scope_sql=' AND dept_id in (1)'))

    assert isinstance(result, RoleDeptTreeReadModel)
    assert dept_service.tree_call_count == 2
    assert role_service.dept_tree_call_count == 2


@pytest.mark.asyncio
async def test_system_mediator_dispatches_role_read_queries() -> None:
    dept_service = _DeptServiceStub()
    role_service = _RoleServiceStub()
    mediator = provide_system_mediator(dept_service=dept_service, role_service=role_service)

    list_result = await mediator.query(
        GetRoleListQuery(
            query=RolePageQueryModel(page=1, pageSize=10),
            data_scope_sql=' AND role_id in (1)',
            is_page=True,
        )
    )
    detail_result = await mediator.query(
        GetRoleDetailQuery(
            role_id=1,
            data_scope_sql=' AND role_id in (1)',
            require_scope_check=True,
        )
    )

    assert isinstance(list_result, RolePageReadModel)
    assert isinstance(detail_result, RoleDetailReadModel)
    assert detail_result.role_id == 1
