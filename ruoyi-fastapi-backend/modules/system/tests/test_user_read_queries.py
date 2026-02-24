from __future__ import annotations

import asyncio

import pytest

from module_admin.entity.vo.user_vo import UserPageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.user_query_handlers import (
    GetUserAuthRoleQueryHandler,
    GetUserDeptTreeQueryHandler,
    GetUserDetailQueryHandler,
    GetUserListQueryHandler,
    GetUserProfileQueryHandler,
)
from modules.system.application.queries import (
    GetUserAuthRoleQuery,
    GetUserDeptTreeQuery,
    GetUserDetailQuery,
    GetUserListQuery,
    GetUserProfileQuery,
)
from modules.system.application.read_models import (
    DeptTreeNodeReadModel,
    UserDetailReadModel,
    UserPageReadModel,
    UserProfileReadModel,
    UserRoleResponseReadModel,
)
from utils.page_util import PageResponseModel


class _DeptServiceStub:
    def __init__(self) -> None:
        self.tree_called_with = None

    async def get_dept_tree_services(self, query, data_scope_sql):
        self.tree_called_with = (query, data_scope_sql)
        return [
            {
                'id': 1,
                'label': '总公司',
                'parentId': 0,
            }
        ]


class _PostServiceStub:
    def __init__(self, *, delay_first_call_seconds: float = 0.0) -> None:
        self.list_called_with = None
        self.list_call_count = 0
        self.delay_first_call_seconds = delay_first_call_seconds

    async def get_post_list_services(self, query, is_page=False):
        self.list_call_count += 1
        if self.list_call_count == 1 and self.delay_first_call_seconds > 0:
            await asyncio.sleep(self.delay_first_call_seconds)
        self.list_called_with = (query, is_page)
        return [
            {
                'postId': 1,
                'postName': '研发工程师',
            }
        ]


class _RoleServiceStub:
    def __init__(self, *, delay_first_call_seconds: float = 0.0) -> None:
        self.options_call_count = 0
        self.delay_first_call_seconds = delay_first_call_seconds

    async def get_role_select_option_services(self):
        self.options_call_count += 1
        if self.options_call_count == 1 and self.delay_first_call_seconds > 0:
            await asyncio.sleep(self.delay_first_call_seconds)
        return [
            {
                'roleId': 1,
                'roleName': '管理员',
                'roleKey': 'admin',
            }
        ]


class _UserServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.profile_called_with = None
        self.scope_check_called_with = None
        self.detail_called_with = None
        self.auth_role_called_with = None

    async def get_user_list_services(self, query_db, query, data_scope_sql, is_page=False):
        self.list_called_with = (query_db, query, data_scope_sql, is_page)
        if is_page:
            return PageResponseModel(
                rows=[
                    {
                        'userId': 1,
                        'userName': 'admin',
                        'nickName': '管理员',
                        'status': '0',
                        'dept': {'deptId': 100, 'deptName': '研发部'},
                    }
                ],
                page_num=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'userId': 1,
                'userName': 'admin',
                'nickName': '管理员',
                'status': '0',
                'dept': {'deptId': 100, 'deptName': '研发部'},
            }
        ]

    async def user_profile_services(self, query_db, user_id):
        self.profile_called_with = (query_db, user_id)
        return {
            'data': {
                'userId': user_id,
                'userName': 'admin',
                'nickName': '管理员',
                'dept': {'deptId': 100, 'deptName': '研发部'},
                'role': [{'roleId': 1, 'roleName': '管理员'}],
            },
            'postGroup': '研发工程师',
            'roleGroup': '管理员',
        }

    async def check_user_data_scope_services(self, query_db, user_id, data_scope_sql):
        self.scope_check_called_with = (query_db, user_id, data_scope_sql)

    async def user_detail_services(self, query_db, user_id, posts=None, roles=None):
        self.detail_called_with = (query_db, user_id, posts, roles)
        return {
            'data': {
                'userId': user_id,
                'userName': 'admin',
                'nickName': '管理员',
                'dept': {'deptId': 100, 'deptName': '研发部'},
                'role': [{'roleId': 1, 'roleName': '管理员'}],
            },
            'postIds': [1],
            'posts': posts or [],
            'roleIds': [1],
            'roles': roles or [],
        }

    async def get_user_role_allocated_list_services(self, query_db, page_object):
        self.auth_role_called_with = (query_db, page_object)
        return {
            'roles': [
                {
                    'roleId': 1,
                    'roleName': '管理员',
                    'roleKey': 'admin',
                    'flag': True,
                }
            ],
            'user': {
                'userId': page_object.user_id,
                'userName': 'admin',
                'nickName': '管理员',
                'dept': {'deptId': 100, 'deptName': '研发部'},
                'role': [{'roleId': 1, 'roleName': '管理员'}],
            },
        }


@pytest.mark.asyncio
async def test_user_query_handlers_success() -> None:
    dept_service = _DeptServiceStub()
    post_service = _PostServiceStub()
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    query_db = object()

    dept_tree_handler = GetUserDeptTreeQueryHandler(dept_service)
    list_handler = GetUserListQueryHandler(user_service)
    profile_handler = GetUserProfileQueryHandler(user_service)
    detail_handler = GetUserDetailQueryHandler(user_service, role_service, post_service)
    auth_role_handler = GetUserAuthRoleQueryHandler(user_service)

    dept_tree_result = await dept_tree_handler.handle(
        GetUserDeptTreeQuery(data_scope_sql=' AND dept_id in (1)', operator='admin')
    )
    list_result = await list_handler.handle(
        GetUserListQuery(
            query_db=query_db,
            query=UserPageQueryModel(pageNum=1, pageSize=10),
            data_scope_sql=' AND user_id in (1)',
            is_page=True,
            operator='admin',
        )
    )
    profile_result = await profile_handler.handle(
        GetUserProfileQuery(
            query_db=query_db,
            user_id=1,
            operator='admin',
        )
    )
    detail_result = await detail_handler.handle(
        GetUserDetailQuery(
            query_db=query_db,
            user_id=1,
            data_scope_sql=' AND user_id in (1)',
            require_scope_check=True,
            operator='admin',
        )
    )
    auth_role_result = await auth_role_handler.handle(
        GetUserAuthRoleQuery(
            query_db=query_db,
            user_id=1,
            operator='admin',
        )
    )

    assert isinstance(dept_tree_result[0], DeptTreeNodeReadModel)
    assert isinstance(list_result, UserPageReadModel)
    assert isinstance(profile_result, UserProfileReadModel)
    assert isinstance(detail_result, UserDetailReadModel)
    assert isinstance(auth_role_result, UserRoleResponseReadModel)
    assert detail_result.data is not None
    assert detail_result.data.user_id == 1
    assert user_service.scope_check_called_with == (query_db, 1, ' AND user_id in (1)')
    assert role_service.options_call_count > 0
    assert post_service.list_called_with is not None


@pytest.mark.asyncio
async def test_user_detail_query_handler_skips_scope_check_when_not_required() -> None:
    post_service = _PostServiceStub()
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    query_db = object()
    handler = GetUserDetailQueryHandler(user_service, role_service, post_service)

    detail_result = await handler.handle(
        GetUserDetailQuery(
            query_db=query_db,
            user_id=1,
            data_scope_sql=' AND user_id in (1)',
            require_scope_check=False,
        )
    )

    assert isinstance(detail_result, UserDetailReadModel)
    assert user_service.scope_check_called_with is None


@pytest.mark.asyncio
async def test_user_detail_query_handler_fallback_when_composed_timeout() -> None:
    post_service = _PostServiceStub(delay_first_call_seconds=0.02)
    role_service = _RoleServiceStub(delay_first_call_seconds=0.02)
    user_service = _UserServiceStub()
    query_db = object()
    handler = GetUserDetailQueryHandler(user_service, role_service, post_service, timeout_seconds=0.001)

    detail_result = await handler.handle(
        GetUserDetailQuery(
            query_db=query_db,
            user_id=1,
            data_scope_sql='',
            require_scope_check=False,
        )
    )

    assert isinstance(detail_result, UserDetailReadModel)
    assert role_service.options_call_count == 2
    assert post_service.list_call_count == 2
    assert user_service.detail_called_with is not None
    assert user_service.detail_called_with[2]
    assert user_service.detail_called_with[3]


@pytest.mark.asyncio
async def test_system_mediator_dispatches_user_read_queries() -> None:
    dept_service = _DeptServiceStub()
    post_service = _PostServiceStub()
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    query_db = object()

    mediator = provide_system_mediator(
        dept_service=dept_service,
        post_service=post_service,
        role_service=role_service,
        user_service=user_service,
    )

    list_result = await mediator.query(
        GetUserListQuery(
            query_db=query_db,
            query=UserPageQueryModel(pageNum=1, pageSize=10),
            data_scope_sql=' AND user_id in (1)',
            is_page=True,
        )
    )
    detail_result = await mediator.query(
        GetUserDetailQuery(
            query_db=query_db,
            user_id=1,
            data_scope_sql=' AND user_id in (1)',
            require_scope_check=True,
        )
    )

    assert isinstance(list_result, UserPageReadModel)
    assert isinstance(detail_result, UserDetailReadModel)
    assert detail_result.data is not None
    assert detail_result.data.user_id == 1
