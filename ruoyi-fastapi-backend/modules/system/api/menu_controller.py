from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.http_contracts import CollectionResult
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuModel, MenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddMenuCommand, DeleteMenuCommand, EditMenuCommand
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetMenuDetailQuery,
    GetMenuListQuery,
    GetMenuTreeQuery,
    GetRoleMenuTreeQuery,
)
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

menuController = APIRouter(prefix='/system/menu', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_menu_detail(request: Request, *, menu_id: int, mediator: Mediator):
    detail_query = GetMenuDetailQuery(
        menu_id=menu_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    menu_detail_result = await mediator.query(detail_query)
    return menu_detail_result


@menuController.get('/treeselect')
async def get_system_menu_tree(
    request: Request,
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    menu_query = GetMenuTreeQuery(
        current_user=current_user,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    menu_query_result = await mediator.query(menu_query)
    logger.info('获取成功')

    return ResponseUtil.ok_collection(items=menu_query_result)


@menuController.get('/roleMenuTreeselect/{role_id}')
async def get_system_role_menu_tree(
    request: Request,
    role_id: int,
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    role_menu_query = GetRoleMenuTreeQuery(
        role_id=role_id,
        current_user=current_user,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    role_menu_query_result = await mediator.query(role_menu_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(role_menu_query_result)


@menuController.get(
    '/list',
    response_model=CollectionResult[MenuModel],
    dependencies=[Depends(CheckUserInterfaceAuth('system:menu:list'))],
)
async def get_system_menu_list(
    request: Request,
    menu_query: MenuQueryModel = Depends(MenuQueryModel.as_query),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    list_query = GetMenuListQuery(
        query=menu_query,
        current_user=current_user,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    menu_query_result = await mediator.query(list_query)
    logger.info('获取成功')

    return ResponseUtil.ok_collection(items=menu_query_result)


@menuController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:add'))])
@ValidateFields(validate_model='add_menu')
@Log(title='菜单管理', business_type=BusinessType.INSERT)
async def add_system_menu(
    request: Request,
    add_menu: MenuModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_menu.create_by = current_user.user.user_name
    add_menu.create_time = datetime.now()
    add_menu.update_by = current_user.user.user_name
    add_menu.update_time = datetime.now()

    add_command = AddMenuCommand(
        query_db=query_db,
        menu=add_menu,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    menu_id = require_int_value(add_result.data, 'menuId', 'menu_id', contract_name='system.menu.create')
    resource = await _load_menu_detail(request, menu_id=int(menu_id), mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/menu/{menu_id}')
    return ResponseUtil.created_resource(resource, location=location)


@menuController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:edit'))])
@ValidateFields(validate_model='edit_menu')
@Log(title='菜单管理', business_type=BusinessType.UPDATE)
async def edit_system_menu(
    request: Request,
    edit_menu: MenuModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_menu.update_by = current_user.user.user_name
    edit_menu.update_time = datetime.now()

    edit_command = EditMenuCommand(
        query_db=query_db,
        menu=edit_menu,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_menu_detail(request, menu_id=edit_menu.menu_id, mediator=mediator)
    return ResponseUtil.ok_resource(resource)


@menuController.delete('/{menu_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:remove'))])
@Log(title='菜单管理', business_type=BusinessType.DELETE)
async def delete_system_menu(
    request: Request,
    menu_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_menu = DeleteMenuModel(menuIds=menu_ids)
    delete_command = DeleteMenuCommand(
        query_db=query_db,
        delete_menu=delete_menu,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@menuController.delete('/', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:remove'))])
@Log(title='菜单管理', business_type=BusinessType.DELETE)
async def delete_system_menu_empty(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_menu = DeleteMenuModel(menuIds='')
    delete_command = DeleteMenuCommand(
        query_db=query_db,
        delete_menu=delete_menu,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@menuController.get(
    '/{menu_id}',
    response_model=MenuModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:menu:query'))],
)
async def query_detail_system_menu(
    request: Request,
    menu_id: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    menu_detail_result = await _load_menu_detail(request, menu_id=menu_id, mediator=mediator)
    logger.info(f'获取menu_id为{menu_id}的信息成功')
    return ResponseUtil.ok_resource(menu_detail_result)
