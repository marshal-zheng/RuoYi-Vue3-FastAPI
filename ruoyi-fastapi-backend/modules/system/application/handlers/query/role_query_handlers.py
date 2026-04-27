"""Query handlers for role operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from module_admin.entity.vo.dept_vo import DeptModel
from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.role_queries import (
    GetRoleAllocatedUsersQuery,
    GetRoleDeptTreeQuery,
    GetRoleDetailQuery,
    GetRoleListQuery,
    GetRoleUnallocatedUsersQuery,
)
from modules.system.application.query_services import ComposedQueryExecutor, ComposedQueryTimeoutError
from modules.system.application.read_models.dept_read_models import DeptTreeNodeReadModel
from modules.system.application.read_models.role_read_models import (
    RoleDeptTreeReadModel,
    RoleDetailReadModel,
    RoleItemReadModel,
    RolePageReadModel,
    RoleUserItemReadModel,
    RoleUserPageReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.dept_service import DeptService
    from modules.system.application.services.role_service import RoleService


def _extract_payload(raw: Any) -> dict[str, Any]:
    if hasattr(raw, 'model_dump'):
        return raw.model_dump(by_alias=False)
    if isinstance(raw, dict):
        return raw
    return {}


def _to_dept_tree_node(raw: Any) -> DeptTreeNodeReadModel:
    payload = dict(_extract_payload(raw))
    children_payload = payload.get('children') or []
    payload['children'] = [_to_dept_tree_node(child) for child in children_payload]
    return DeptTreeNodeReadModel.model_validate(payload)


def _to_role_item(raw: Any) -> RoleItemReadModel:
    return RoleItemReadModel.model_validate(_extract_payload(raw))


def _to_role_user_item(raw: Any) -> RoleUserItemReadModel:
    return RoleUserItemReadModel.model_validate(_extract_payload(raw))


class GetRoleDeptTreeQueryHandler(IQueryHandler[GetRoleDeptTreeQuery, RoleDeptTreeReadModel]):
    """Handle role department-tree query."""

    def __init__(
        self,
        role_service: RoleService,
        dept_service: DeptService,
        *,
        timeout_seconds: float = 0.2,
    ):
        self._role_service = role_service
        self._dept_service = dept_service
        self._composed_executor = ComposedQueryExecutor(
            query_name='GetRoleDeptTreeQuery',
            timeout_seconds=timeout_seconds,
        )

    async def handle(self, request: GetRoleDeptTreeQuery) -> RoleDeptTreeReadModel:
        try:
            composed_result = await self._composed_executor.run(
                {
                    'dept_tree': lambda: self._dept_service.get_dept_tree_services(DeptModel(), request.data_scope_sql),
                    'role_dept': lambda: self._role_service.get_role_dept_tree_services(request.role_id),
                },
                trace_id=request.trace_id,
                request_id=request.request_id,
            )
            dept_tree_result = composed_result['dept_tree']
            role_dept_result = composed_result['role_dept']
        except ComposedQueryTimeoutError:
            dept_tree_result = await self._dept_service.get_dept_tree_services(DeptModel(), request.data_scope_sql)
            role_dept_result = await self._role_service.get_role_dept_tree_services(request.role_id)

        role_dept_payload = _extract_payload(role_dept_result)
        checked_keys = role_dept_payload.get('checked_keys') or role_dept_payload.get('checkedKeys') or []
        return RoleDeptTreeReadModel(
            depts=[_to_dept_tree_node(row) for row in dept_tree_result],
            checked_keys=[int(key) for key in checked_keys],
        )


class GetRoleListQueryHandler(IQueryHandler[GetRoleListQuery, RolePageReadModel]):
    """Handle paged role list query."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: GetRoleListQuery) -> RolePageReadModel:
        list_result = await self._role_service.get_role_list_services(
            request.query,
            request.data_scope_sql,
            is_page=request.is_page,
        )

        if request.is_page:
            items = [_to_role_item(row) for row in list_result.items]
            return RolePageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_role_item(row) for row in list_result]
        return RolePageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetRoleDetailQueryHandler(IQueryHandler[GetRoleDetailQuery, RoleDetailReadModel]):
    """Handle role detail query."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: GetRoleDetailQuery) -> RoleDetailReadModel:
        if request.require_scope_check:
            await self._role_service.check_role_data_scope_services(str(request.role_id), request.data_scope_sql)

        detail_result = await self._role_service.role_detail_services(request.role_id)
        if detail_result is None:
            return RoleDetailReadModel()

        return RoleDetailReadModel.model_validate(_extract_payload(detail_result))


class GetRoleAllocatedUsersQueryHandler(IQueryHandler[GetRoleAllocatedUsersQuery, RoleUserPageReadModel]):
    """Handle allocated users query by role."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: GetRoleAllocatedUsersQuery) -> RoleUserPageReadModel:
        page_result = await self._role_service.get_role_user_allocated_list_services(
            request.query,
            request.data_scope_sql,
            is_page=request.is_page,
        )

        items = [_to_role_user_item(row) for row in page_result.items]
        return RoleUserPageReadModel(
            items=items,
            page=page_result.page,
            page_size=page_result.page_size,
            total=page_result.total,
            has_next=page_result.has_next,
        )


class GetRoleUnallocatedUsersQueryHandler(IQueryHandler[GetRoleUnallocatedUsersQuery, RoleUserPageReadModel]):
    """Handle unallocated users query by role."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: GetRoleUnallocatedUsersQuery) -> RoleUserPageReadModel:
        page_result = await self._role_service.get_role_user_unallocated_list_services(
            request.query,
            request.data_scope_sql,
            is_page=request.is_page,
        )

        items = [_to_role_user_item(row) for row in page_result.items]
        return RoleUserPageReadModel(
            items=items,
            page=page_result.page,
            page_size=page_result.page_size,
            total=page_result.total,
            has_next=page_result.has_next,
        )
