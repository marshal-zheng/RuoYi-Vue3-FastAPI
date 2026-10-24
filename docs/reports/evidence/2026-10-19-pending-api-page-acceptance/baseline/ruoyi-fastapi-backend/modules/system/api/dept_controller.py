from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.http_contracts import CollectionResult
from config.enums import BusinessType
from config.get_db import get_db
from container.dependencies import service_provider
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel, DeptQueryModel
from module_admin.entity.vo.dept_write_vo import DeptCreateModel, DeptUpdateModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddDeptCommand, DeleteDeptCommand, EditDeptCommand
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetDeptDetailQuery,
    GetDeptEditOptionQuery,
    GetDeptListQuery,
    GetDeptTreeSelectQuery,
)
from modules.system.application.services.dept_service import DeptService
from utils.common_util import bytes2file_response
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil

deptController = APIRouter(prefix='/system/dept', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_dept_detail(
    request: Request,
    *,
    dept_id: int,
    current_user: CurrentUserModel,
    data_scope_sql: str,
    mediator: Mediator,
    require_scope_check: bool | None = None,
):
    detail_query = GetDeptDetailQuery(
        dept_id=dept_id,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin if require_scope_check is None else require_scope_check,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(detail_query)


@deptController.get(
    '/list/exclude/{dept_id}',
    response_model=CollectionResult[DeptModel],
    dependencies=[Depends(CheckUserInterfaceAuth('system:dept:list'))],
)
async def get_system_dept_tree_for_edit_option(
    request: Request,
    dept_id: int,
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dept_query = GetDeptEditOptionQuery(
        dept_id=dept_id,
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dept_query_result = await mediator.query(dept_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dept_query_result)


@deptController.get(
    '/list',
    response_model=CollectionResult[DeptModel],
    dependencies=[Depends(CheckUserInterfaceAuth('system:dept:list'))],
)
async def get_system_dept_list(
    request: Request,
    dept_query: DeptQueryModel = Depends(DeptQueryModel.as_query),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    query = GetDeptListQuery(
        query=dept_query,
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dept_query_result = await mediator.query(query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dept_query_result)


@deptController.get('/treeselect', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:list'))])
async def get_system_dept_tree_select(
    request: Request,
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dept_query = GetDeptTreeSelectQuery(
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dept_query_result = await mediator.query(dept_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dept_query_result)


@deptController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:add'))])
@Log(title='部门管理', business_type=BusinessType.INSERT)
async def add_system_dept(
    request: Request,
    add_dept: DeptCreateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_dept = DeptModel(**add_dept.model_dump(exclude_unset=True))
    add_dept.create_by = current_user.user.user_name
    add_dept.create_time = datetime.now()
    add_dept.update_by = current_user.user.user_name
    add_dept.update_time = datetime.now()
    add_command = AddDeptCommand(
        query_db=query_db,
        dept=add_dept,
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    dept_id = require_int_value(add_result.data, 'deptId', 'dept_id', contract_name='system.dept.create')
    resource = await _load_dept_detail(
        request,
        dept_id=int(dept_id),
        current_user=current_user,
        data_scope_sql='',
        mediator=mediator,
        require_scope_check=False,
    )
    location = ResponseUtil.build_absolute_location(request, f'/system/dept/{dept_id}')
    return ResponseUtil.created_resource(resource, location=location)


@deptController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:edit'))])
@Log(title='部门管理', business_type=BusinessType.UPDATE)
async def edit_system_dept(
    request: Request,
    edit_dept: DeptUpdateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_dept = DeptModel(**edit_dept.model_dump(exclude_unset=True))
    edit_dept.update_by = current_user.user.user_name
    edit_dept.update_time = datetime.now()
    edit_command = EditDeptCommand(
        query_db=query_db,
        dept=edit_dept,
        redis_client=getattr(request.app.state, 'redis', None),
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_dept_detail(
        request,
        dept_id=edit_dept.dept_id,
        current_user=current_user,
        data_scope_sql=data_scope_sql,
        mediator=mediator,
    )
    return ResponseUtil.ok_resource(resource)


@deptController.delete('/{dept_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:remove'))])
@Log(title='部门管理', business_type=BusinessType.DELETE)
async def delete_system_dept(
    request: Request,
    dept_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_dept = DeleteDeptModel(deptIds=dept_ids)
    delete_dept.update_by = current_user.user.user_name
    delete_dept.update_time = datetime.now()
    delete_command = DeleteDeptCommand(
        query_db=query_db,
        delete_dept=delete_dept,
        redis_client=getattr(request.app.state, 'redis', None),
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@deptController.get(
    '/{dept_id}', response_model=DeptModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dept:query'))]
)
async def query_detail_system_dept(
    request: Request,
    dept_id: int,
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetDeptDetailQuery(
        dept_id=dept_id,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    detail_dept_result = await mediator.query(detail_query)
    logger.info(f'获取dept_id为{dept_id}的信息成功')

    return ResponseUtil.ok_resource(detail_dept_result)


@deptController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:dept:export'))])
@Log(title='部门管理', business_type=BusinessType.EXPORT)
async def export_system_dept_list(
    request: Request,
    dept_query: DeptQueryModel = Form(),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    dept_service: DeptService = Depends(service_provider('dept_service')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    list_query = GetDeptListQuery(
        query=dept_query,
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dept_query_result = await mediator.query(list_query)
    dept_rows = [row.model_dump(by_alias=True) for row in dept_query_result]
    dept_export_result = await dept_service.export_dept_list_services(dept_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(dept_export_result))
