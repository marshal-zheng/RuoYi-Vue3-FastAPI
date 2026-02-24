"""Query handlers for department operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from module_admin.entity.vo.dept_vo import DeptModel
from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.dept_queries import (
    GetDeptDetailQuery,
    GetDeptEditOptionQuery,
    GetDeptListQuery,
    GetDeptTreeSelectQuery,
)
from modules.system.application.read_models.dept_read_models import (
    DeptDetailReadModel,
    DeptItemReadModel,
    DeptTreeNodeReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.dept_service import DeptService


def _to_dept_item(raw: Any) -> DeptItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return DeptItemReadModel.model_validate(payload)


def _to_tree_node(raw: Any) -> DeptTreeNodeReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = dict(raw)
    else:
        payload = {}

    children_payload = payload.get('children') or []
    payload['children'] = [_to_tree_node(child) for child in children_payload]
    return DeptTreeNodeReadModel.model_validate(payload)


class GetDeptEditOptionQueryHandler(IQueryHandler[GetDeptEditOptionQuery, list[DeptItemReadModel]]):
    """Handle department edit-option query."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: GetDeptEditOptionQuery) -> list[DeptItemReadModel]:
        query = DeptModel(deptId=request.dept_id)
        list_result = await self._dept_service.get_dept_for_edit_option_services(query, request.data_scope_sql)
        return [_to_dept_item(row) for row in list_result]


class GetDeptListQueryHandler(IQueryHandler[GetDeptListQuery, list[DeptItemReadModel]]):
    """Handle department list query."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: GetDeptListQuery) -> list[DeptItemReadModel]:
        list_result = await self._dept_service.get_dept_list_services(request.query, request.data_scope_sql)
        return [_to_dept_item(row) for row in list_result]


class GetDeptTreeSelectQueryHandler(IQueryHandler[GetDeptTreeSelectQuery, list[DeptTreeNodeReadModel]]):
    """Handle department tree-select query."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: GetDeptTreeSelectQuery) -> list[DeptTreeNodeReadModel]:
        list_result = await self._dept_service.get_dept_tree_services(request.query, request.data_scope_sql)
        return [_to_tree_node(row) for row in list_result]


class GetDeptDetailQueryHandler(IQueryHandler[GetDeptDetailQuery, DeptDetailReadModel]):
    """Handle department detail query."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: GetDeptDetailQuery) -> DeptDetailReadModel:
        if request.require_scope_check:
            await self._dept_service.check_dept_data_scope_services(request.dept_id, request.data_scope_sql)

        detail_result = await self._dept_service.dept_detail_services(request.dept_id)
        if detail_result is None:
            return DeptDetailReadModel()

        if hasattr(detail_result, 'model_dump'):
            payload = detail_result.model_dump(by_alias=False)
        elif isinstance(detail_result, dict):
            payload = detail_result
        else:
            payload = {}

        return DeptDetailReadModel.model_validate(payload)
