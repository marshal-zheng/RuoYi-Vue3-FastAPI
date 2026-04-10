"""Query handlers for user operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from module_admin.entity.vo.dept_vo import DeptModel
from module_admin.entity.vo.post_vo import PostPageQueryModel
from module_admin.entity.vo.user_vo import UserRoleQueryModel
from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.user_queries import (
    GetUserAuthRoleQuery,
    GetUserDeptTreeQuery,
    GetUserDetailQuery,
    GetUserListQuery,
    GetUserProfileQuery,
)
from modules.system.application.query_services import ComposedQueryExecutor, ComposedQueryTimeoutError
from modules.system.application.read_models.dept_read_models import DeptTreeNodeReadModel
from modules.system.application.read_models.user_read_models import (
    UserAllocatedRoleReadModel,
    UserDetailReadModel,
    UserInfoReadModel,
    UserListItemReadModel,
    UserPageReadModel,
    UserProfileReadModel,
    UserRoleResponseReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.dept_service import DeptService
    from modules.system.application.services.post_service import PostService
    from modules.system.application.services.role_service import RoleService
    from modules.system.application.services.user_service import UserService


def _extract_payload(raw: Any) -> dict[str, Any]:
    if hasattr(raw, 'model_dump'):
        # API read models should keep camelCase aliases for nested option payloads
        # such as posts/roles, otherwise the frontend cannot resolve postName/roleName.
        return raw.model_dump(by_alias=True)
    if isinstance(raw, dict):
        return raw
    return {}


def _to_tree_node(raw: Any) -> DeptTreeNodeReadModel:
    payload = dict(_extract_payload(raw))
    children_payload = payload.get('children') or []
    payload['children'] = [_to_tree_node(child) for child in children_payload]
    return DeptTreeNodeReadModel.model_validate(payload)


def _to_user_info(raw: Any) -> UserInfoReadModel:
    return UserInfoReadModel.model_validate(_extract_payload(raw))


def _to_user_list_item(raw: Any) -> UserListItemReadModel:
    return UserListItemReadModel.model_validate(_extract_payload(raw))


def _to_allocated_role(raw: Any) -> UserAllocatedRoleReadModel:
    return UserAllocatedRoleReadModel.model_validate(_extract_payload(raw))


def _normalize_option_list(raw_list: Any) -> list[dict[str, Any]]:
    if raw_list is None:
        return []
    return [_extract_payload(item) for item in raw_list]


class GetUserDeptTreeQueryHandler(IQueryHandler[GetUserDeptTreeQuery, list[DeptTreeNodeReadModel]]):
    """Handle user department-tree query."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: GetUserDeptTreeQuery) -> list[DeptTreeNodeReadModel]:
        tree_result = await self._dept_service.get_dept_tree_services(DeptModel(), request.data_scope_sql)
        return [_to_tree_node(row) for row in tree_result]


class GetUserListQueryHandler(IQueryHandler[GetUserListQuery, UserPageReadModel]):
    """Handle paged user list query."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: GetUserListQuery) -> UserPageReadModel:
        list_result = await self._user_service.get_user_list_services(
            request.query_db,
            request.query,
            request.data_scope_sql,
            is_page=request.is_page,
        )

        if request.is_page:
            rows = [_to_user_list_item(row) for row in list_result.rows]
            return UserPageReadModel(
                rows=rows,
                page_num=list_result.page_num,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        rows = [_to_user_list_item(row) for row in list_result]
        return UserPageReadModel(
            rows=rows,
            page_num=1,
            page_size=len(rows),
            total=len(rows),
            has_next=False,
        )


class GetUserProfileQueryHandler(IQueryHandler[GetUserProfileQuery, UserProfileReadModel]):
    """Handle current user profile query."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: GetUserProfileQuery) -> UserProfileReadModel:
        profile_result = await self._user_service.user_profile_services(request.query_db, request.user_id)
        payload = _extract_payload(profile_result)
        data_payload = payload.get('data')
        payload['data'] = _to_user_info(data_payload) if data_payload else None
        return UserProfileReadModel.model_validate(payload)


class GetUserDetailQueryHandler(IQueryHandler[GetUserDetailQuery, UserDetailReadModel]):
    """Handle user detail query."""

    def __init__(
        self,
        user_service: UserService,
        role_service: RoleService,
        post_service: PostService,
        *,
        timeout_seconds: float = 0.25,
    ):
        self._user_service = user_service
        self._role_service = role_service
        self._post_service = post_service
        self._options_executor = ComposedQueryExecutor(
            query_name='GetUserDetailQuery.options',
            timeout_seconds=timeout_seconds,
        )

    async def handle(self, request: GetUserDetailQuery) -> UserDetailReadModel:
        if request.require_scope_check and request.user_id not in {'', None}:
            await self._user_service.check_user_data_scope_services(
                request.query_db,
                int(request.user_id),
                request.data_scope_sql,
            )

        role_options, post_options = await self._load_options_with_fallback(request)
        detail_result = await self._user_service.user_detail_services(
            request.query_db,
            request.user_id,
            posts=post_options,
            roles=role_options,
        )

        payload = _extract_payload(detail_result)
        if not payload:
            payload = {
                'posts': _normalize_option_list(post_options),
                'roles': _normalize_option_list(role_options),
            }

        data_payload = payload.get('data')
        payload['data'] = _to_user_info(data_payload) if data_payload else None
        payload['posts'] = _normalize_option_list(payload.get('posts'))
        payload['roles'] = _normalize_option_list(payload.get('roles'))

        return UserDetailReadModel.model_validate(payload)

    async def _load_options_with_fallback(self, request: GetUserDetailQuery) -> tuple[Any, Any]:
        try:
            composed_result = await self._options_executor.run(
                {
                    'roles': self._role_service.get_role_select_option_services,
                    'posts': lambda: self._post_service.get_post_list_services(PostPageQueryModel(), is_page=False),
                },
                trace_id=request.trace_id,
                request_id=request.request_id,
            )
            return composed_result['roles'], composed_result['posts']
        except ComposedQueryTimeoutError:
            role_options = await self._role_service.get_role_select_option_services()
            post_options = await self._post_service.get_post_list_services(PostPageQueryModel(), is_page=False)
            return role_options, post_options


class GetUserAuthRoleQueryHandler(IQueryHandler[GetUserAuthRoleQuery, UserRoleResponseReadModel]):
    """Handle allocated-role query by user id."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: GetUserAuthRoleQuery) -> UserRoleResponseReadModel:
        query = UserRoleQueryModel(userId=request.user_id)
        auth_role_result = await self._user_service.get_user_role_allocated_list_services(request.query_db, query)

        payload = _extract_payload(auth_role_result)
        roles = [_to_allocated_role(row) for row in (payload.get('roles') or [])]
        user_payload = payload.get('user')

        return UserRoleResponseReadModel(
            roles=roles,
            user=_to_user_info(user_payload) if user_payload else None,
        )
