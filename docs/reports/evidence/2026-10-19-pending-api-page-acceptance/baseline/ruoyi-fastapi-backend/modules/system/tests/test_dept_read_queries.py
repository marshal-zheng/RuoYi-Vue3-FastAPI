from __future__ import annotations

import pytest

from module_admin.entity.vo.dept_vo import DeptQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.dept_query_handlers import (
    GetDeptDetailQueryHandler,
    GetDeptEditOptionQueryHandler,
    GetDeptListQueryHandler,
    GetDeptTreeSelectQueryHandler,
)
from modules.system.application.queries import (
    GetDeptDetailQuery,
    GetDeptEditOptionQuery,
    GetDeptListQuery,
    GetDeptTreeSelectQuery,
)
from modules.system.application.read_models import (
    DeptDetailReadModel,
    DeptItemReadModel,
    DeptTreeNodeReadModel,
)


class _DeptServiceStub:
    def __init__(self) -> None:
        self.edit_option_called_with = None
        self.list_called_with = None
        self.tree_called_with = None
        self.scope_check_called_with = None
        self.detail_called_with = None

    async def get_dept_for_edit_option_services(self, query, data_scope_sql):
        self.edit_option_called_with = (query, data_scope_sql)
        return [
            {
                'deptId': 2,
                'deptName': '研发部',
                'parentId': 1,
                'status': '0',
            }
        ]

    async def get_dept_list_services(self, query, data_scope_sql):
        self.list_called_with = (query, data_scope_sql)
        return [
            {
                'deptId': 1,
                'deptName': '总公司',
                'parentId': 0,
                'status': '0',
            }
        ]

    async def get_dept_tree_services(self, query, data_scope_sql):
        self.tree_called_with = (query, data_scope_sql)
        return [
            {
                'id': 1,
                'label': '总公司',
                'parentId': 0,
                'children': [
                    {
                        'id': 2,
                        'label': '研发部',
                        'parentId': 1,
                    }
                ],
            }
        ]

    async def check_dept_data_scope_services(self, dept_id, data_scope_sql):
        self.scope_check_called_with = (dept_id, data_scope_sql)

    async def dept_detail_services(self, dept_id):
        self.detail_called_with = dept_id
        return {
            'deptId': dept_id,
            'deptName': '研发部',
            'parentId': 1,
            'status': '0',
        }


@pytest.mark.asyncio
async def test_dept_query_handlers_success() -> None:
    dept_service = _DeptServiceStub()
    edit_option_handler = GetDeptEditOptionQueryHandler(dept_service)
    list_handler = GetDeptListQueryHandler(dept_service)
    tree_handler = GetDeptTreeSelectQueryHandler(dept_service)
    detail_handler = GetDeptDetailQueryHandler(dept_service)

    edit_option_result = await edit_option_handler.handle(
        GetDeptEditOptionQuery(dept_id=2, data_scope_sql=' AND dept_id in (1,2)', operator='admin')
    )
    list_result = await list_handler.handle(
        GetDeptListQuery(
            query=DeptQueryModel(deptName='总'),
            data_scope_sql=' AND dept_id in (1,2)',
            operator='admin',
        )
    )
    tree_result = await tree_handler.handle(
        GetDeptTreeSelectQuery(data_scope_sql=' AND dept_id in (1,2)', operator='admin')
    )
    detail_result = await detail_handler.handle(
        GetDeptDetailQuery(
            dept_id=2,
            data_scope_sql=' AND dept_id in (1,2)',
            require_scope_check=True,
            operator='admin',
        )
    )

    assert isinstance(edit_option_result[0], DeptItemReadModel)
    assert isinstance(list_result[0], DeptItemReadModel)
    assert isinstance(tree_result[0], DeptTreeNodeReadModel)
    assert isinstance(detail_result, DeptDetailReadModel)
    assert detail_result.dept_id == 2
    assert dept_service.edit_option_called_with is not None
    assert dept_service.list_called_with is not None
    assert dept_service.tree_called_with is not None
    assert dept_service.scope_check_called_with == (2, ' AND dept_id in (1,2)')


@pytest.mark.asyncio
async def test_dept_detail_query_handler_skips_scope_check_when_not_required() -> None:
    dept_service = _DeptServiceStub()
    detail_handler = GetDeptDetailQueryHandler(dept_service)

    detail_result = await detail_handler.handle(
        GetDeptDetailQuery(
            dept_id=2,
            data_scope_sql=' AND dept_id in (1,2)',
            require_scope_check=False,
        )
    )

    assert isinstance(detail_result, DeptDetailReadModel)
    assert dept_service.scope_check_called_with is None
    assert dept_service.detail_called_with == 2


@pytest.mark.asyncio
async def test_system_mediator_dispatches_dept_read_queries() -> None:
    dept_service = _DeptServiceStub()
    mediator = provide_system_mediator(dept_service=dept_service)

    list_result = await mediator.query(
        GetDeptListQuery(
            query=DeptQueryModel(deptName='总'),
            data_scope_sql=' AND dept_id in (1,2)',
        )
    )
    detail_result = await mediator.query(
        GetDeptDetailQuery(
            dept_id=2,
            data_scope_sql=' AND dept_id in (1,2)',
            require_scope_check=True,
        )
    )

    assert isinstance(list_result[0], DeptItemReadModel)
    assert isinstance(detail_result, DeptDetailReadModel)
    assert detail_result.dept_id == 2
