from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from container.dependencies import service_provider
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.role_vo import AddRoleModel, DeleteRoleModel, RoleModel, RolePageQueryModel
from module_admin.entity.vo.user_vo import CrudUserRoleModel, CurrentUserModel, UserRolePageQueryModel
from modules.identity.ports import get_current_user
from modules.system.application.services.role_service import RoleService
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddRoleCommand,
    AddRoleUserCommand,
    AssignRoleDataScopeCommand,
    CancelRoleUserCommand,
    ChangeRoleStatusCommand,
    DeleteRoleCommand,
    EditRoleCommand,
)
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetRoleAllocatedUsersQuery,
    GetRoleDeptTreeQuery,
    GetRoleDetailQuery,
    GetRoleListQuery,
    GetRoleUnallocatedUsersQuery,
)
from utils.common_util import bytes2file_response
from utils.http_contract_responses import ok_page_result, require_int_value
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

roleController = APIRouter(prefix='/system/role', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_role_detail(
    request: Request,
    *,
    role_id: int,
    mediator: Mediator,
    data_scope_sql: str = '',
    require_scope_check: bool = False,
):
    role_detail_query = GetRoleDetailQuery(
        role_id=role_id,
        data_scope_sql=data_scope_sql,
        require_scope_check=require_scope_check,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_detail_result = await mediator.query(role_detail_query)
    if role_detail_result is None:
        return {}
    return role_detail_result.model_dump(by_alias=False)


@roleController.get('/deptTree/{role_id}', dependencies=[Depends(CheckUserInterfaceAuth('system:role:query'))])
async def get_system_role_dept_tree(
    request: Request,
    role_id: int,
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dept_tree_query = GetRoleDeptTreeQuery(
        role_id=role_id,
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_dept_query_result = await mediator.query(dept_tree_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(role_dept_query_result)


@roleController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))]
)
async def get_system_role_list(
    request: Request,
    role_page_query: RolePageQueryModel = Depends(RolePageQueryModel.as_query),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    role_list_query = GetRoleListQuery(
        query=role_page_query,
        data_scope_sql=data_scope_sql,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_page_query_result = await mediator.query(role_list_query)
    logger.info('获取成功')

    return ok_page_result(role_page_query_result)


@roleController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:role:add'))])
@ValidateFields(validate_model='add_role')
@Log(title='角色管理', business_type=BusinessType.INSERT)
async def add_system_role(
    request: Request,
    add_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_role.create_by = current_user.user.user_name
    add_role.create_time = datetime.now()
    add_role.update_by = current_user.user.user_name
    add_role.update_time = datetime.now()
    add_command = AddRoleCommand(
        query_db=query_db,
        role=add_role,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    role_id = require_int_value(add_result.data, 'roleId', 'role_id', contract_name='system.role.create')
    resource = await _load_role_detail(request, role_id=role_id, mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/role/{role_id}')
    return ResponseUtil.created_resource(resource, location=location)


@roleController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@ValidateFields(validate_model='edit_role')
@Log(title='角色管理', business_type=BusinessType.UPDATE)
async def edit_system_role(
    request: Request,
    edit_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_role.update_by = current_user.user.user_name
    edit_role.update_time = datetime.now()
    edit_command = EditRoleCommand(
        query_db=query_db,
        role=edit_role,
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_role_detail(
        request,
        role_id=edit_role.role_id,
        mediator=mediator,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
    )
    return ResponseUtil.ok_resource(resource)


@roleController.put('/dataScope', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def edit_system_role_datascope(
    request: Request,
    role_data_scope: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_role = AddRoleModel(
        roleId=role_data_scope.role_id,
        dataScope=role_data_scope.data_scope,
        deptIds=role_data_scope.dept_ids,
        deptCheckStrictly=role_data_scope.dept_check_strictly,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
    )
    grant_command = AssignRoleDataScopeCommand(
        query_db=query_db,
        role=edit_role,
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    grant_result = await mediator.send(grant_command)
    message = grant_result.data.get('message') if grant_result.data else '分配成功'
    logger.info(message)

    resource = await _load_role_detail(
        request,
        role_id=role_data_scope.role_id,
        mediator=mediator,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
    )
    return ResponseUtil.ok_resource(resource)


@roleController.delete('/{role_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:role:remove'))])
@Log(title='角色管理', business_type=BusinessType.DELETE)
async def delete_system_role(
    request: Request,
    role_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_role = DeleteRoleModel(roleIds=role_ids, updateBy=current_user.user.user_name, updateTime=datetime.now())
    delete_command = DeleteRoleCommand(
        query_db=query_db,
        delete_role=delete_role,
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


@roleController.get(
    '/{role_id}', response_model=RoleModel, dependencies=[Depends(CheckUserInterfaceAuth('system:role:query'))]
)
async def query_detail_system_role(
    request: Request,
    role_id: int,
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    role_detail_result = await _load_role_detail(
        request,
        role_id=role_id,
        mediator=mediator,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
    )
    logger.info(f'获取role_id为{role_id}的信息成功')

    return ResponseUtil.ok_resource(role_detail_result)


@roleController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:role:export'))])
@Log(title='角色管理', business_type=BusinessType.EXPORT)
async def export_system_role_list(
    request: Request,
    role_page_query: RolePageQueryModel = Form(),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    role_service: RoleService = Depends(service_provider('role_service')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    role_list_query = GetRoleListQuery(
        query=role_page_query,
        data_scope_sql=data_scope_sql,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_query_result = await mediator.query(role_list_query)
    role_rows = [row.model_dump(by_alias=True) for row in role_query_result.items]
    role_export_result = await role_service.export_role_list_services(role_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(role_export_result))


@roleController.put('/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.UPDATE)
async def reset_system_role_status(
    request: Request,
    change_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_role = AddRoleModel(
        roleId=change_role.role_id,
        status=change_role.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    change_status_command = ChangeRoleStatusCommand(
        query_db=query_db,
        role=edit_role,
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    change_status_result = await mediator.send(change_status_command)
    message = change_status_result.data.get('message') if change_status_result.data else '更新成功'
    logger.info(message)

    resource = await _load_role_detail(
        request,
        role_id=change_role.role_id,
        mediator=mediator,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
    )
    return ResponseUtil.ok_resource(resource)


@roleController.get(
    '/authUser/allocatedList',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))],
)
async def get_system_allocated_user_list(
    request: Request,
    user_role: UserRolePageQueryModel = Depends(UserRolePageQueryModel.as_query),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    allocated_query = GetRoleAllocatedUsersQuery(
        query=user_role,
        data_scope_sql=data_scope_sql,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_user_allocated_page_query_result = await mediator.query(allocated_query)
    logger.info('获取成功')

    return ok_page_result(role_user_allocated_page_query_result)


@roleController.get(
    '/authUser/unallocatedList',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))],
)
async def get_system_unallocated_user_list(
    request: Request,
    user_role: UserRolePageQueryModel = Depends(UserRolePageQueryModel.as_query),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    unallocated_query = GetRoleUnallocatedUsersQuery(
        query=user_role,
        data_scope_sql=data_scope_sql,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_user_unallocated_page_query_result = await mediator.query(unallocated_query)
    logger.info('获取成功')

    return ok_page_result(role_user_unallocated_page_query_result)


@roleController.put('/authUser/selectAll', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def add_system_role_user(
    request: Request,
    add_role_user: CrudUserRoleModel = Depends(CrudUserRoleModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    grant_command = AddRoleUserCommand(
        role_user=add_role_user,
        query_db=query_db,
        enforce_data_scope=not current_user.user.admin,
        data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    grant_result = await mediator.send(grant_command)
    message = grant_result.data.get('message') if grant_result.data else '分配成功'
    logger.info(message)

    return ResponseUtil.no_content()


@roleController.put('/authUser/cancel', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def cancel_system_role_user(
    request: Request,
    cancel_user_role: CrudUserRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    cancel_command = CancelRoleUserCommand(
        role_user=cancel_user_role,
        query_db=query_db,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    cancel_result = await mediator.send(cancel_command)
    message = cancel_result.data.get('message') if cancel_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@roleController.put('/authUser/cancelAll', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def batch_cancel_system_role_user(
    request: Request,
    batch_cancel_user_role: CrudUserRoleModel = Depends(CrudUserRoleModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    cancel_command = CancelRoleUserCommand(
        role_user=batch_cancel_user_role,
        query_db=query_db,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    cancel_result = await mediator.send(cancel_command)
    message = cancel_result.data.get('message') if cancel_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()
