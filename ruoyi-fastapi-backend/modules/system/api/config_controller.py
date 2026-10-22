from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel, DeleteConfigModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddConfigCommand,
    DeleteConfigCommand,
    EditConfigCommand,
    RefreshConfigCacheCommand,
)
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetConfigDetailQuery,
    GetConfigListQuery,
    GetConfigValueByKeyQuery,
)
from modules.system.application.read_models.config_read_models import ConfigDetailReadModel, ConfigPageReadModel
from modules.system.application.services.config_service import ConfigService
from utils.common_util import bytes2file_response
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

configController = APIRouter(prefix='/system/config', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_config_detail(request: Request, *, config_id: int, mediator: Mediator):
    detail_query = GetConfigDetailQuery(
        config_id=config_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(detail_query)


@configController.get(
    '/list', response_model=ConfigPageReadModel, dependencies=[Depends(CheckUserInterfaceAuth('system:config:list'))]
)
async def get_system_config_list(
    request: Request,
    config_page_query: ConfigPageQueryModel = Depends(ConfigPageQueryModel.as_query),
    mediator: Mediator = Depends(provide_system_mediator),
):
    config_query = GetConfigListQuery(
        query=config_page_query,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    config_page_query_result = await mediator.query(config_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(config_page_query_result)


@configController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:config:add'))])
@ValidateFields(validate_model='add_config')
@Log(title='参数管理', business_type=BusinessType.INSERT)
async def add_system_config(
    request: Request,
    add_config: ConfigModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_config.create_by = current_user.user.user_name
    add_config.create_time = datetime.now()
    add_config.update_by = current_user.user.user_name
    add_config.update_time = datetime.now()
    add_command = AddConfigCommand(
        query_db=query_db,
        config=add_config,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    config_id = require_int_value(add_result.data, 'configId', 'config_id', contract_name='system.config.create')
    resource = await _load_config_detail(request, config_id=int(config_id), mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/config/{config_id}')
    return ResponseUtil.created_resource(resource, location=location)


@configController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:config:edit'))])
@ValidateFields(validate_model='edit_config')
@Log(title='参数管理', business_type=BusinessType.UPDATE)
async def edit_system_config(
    request: Request,
    edit_config: ConfigModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_config.update_by = current_user.user.user_name
    edit_config.update_time = datetime.now()
    edit_command = EditConfigCommand(
        query_db=query_db,
        config=edit_config,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_config_detail(request, config_id=edit_config.config_id, mediator=mediator)
    return ResponseUtil.ok_resource(resource)


@configController.delete('/refreshCache', dependencies=[Depends(CheckUserInterfaceAuth('system:config:remove'))])
@Log(title='参数管理', business_type=BusinessType.UPDATE)
async def refresh_system_config(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    refresh_command = RefreshConfigCacheCommand(
        query_db=query_db,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    refresh_result = await mediator.send(refresh_command)
    message = refresh_result.data.get('message') if refresh_result.data else '刷新成功'
    logger.info(message)
    return ResponseUtil.ok_resource({'status': 'refreshed'})


@configController.delete('', dependencies=[Depends(CheckUserInterfaceAuth('system:config:remove'))])
@Log(title='参数管理', business_type=BusinessType.DELETE)
async def delete_system_config_empty(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_config = DeleteConfigModel(configIds='')
    delete_command = DeleteConfigCommand(
        query_db=query_db,
        delete_config=delete_config,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@configController.delete('/{config_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:config:remove'))])
@Log(title='参数管理', business_type=BusinessType.DELETE)
async def delete_system_config(
    request: Request,
    config_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_config = DeleteConfigModel(configIds=config_ids)
    delete_command = DeleteConfigCommand(
        query_db=query_db,
        delete_config=delete_config,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@configController.get(
    '/{config_id}',
    response_model=ConfigDetailReadModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:config:query'))],
)
async def query_detail_system_config(
    request: Request,
    config_id: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetConfigDetailQuery(
        config_id=config_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    config_detail_result = await mediator.query(detail_query)
    logger.info(f'获取config_id为{config_id}的信息成功')

    return ResponseUtil.ok_resource(config_detail_result)


@configController.get('/configKey/{config_key}')
async def query_system_config(
    request: Request,
    config_key: str,
    mediator: Mediator = Depends(provide_system_mediator),
):
    config_key_query = GetConfigValueByKeyQuery(
        config_key=config_key,
        redis_client=getattr(request.app.state, 'redis', None),
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    config_query_result = await mediator.query(config_key_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(config_query_result)


@configController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:config:export'))])
@Log(title='参数管理', business_type=BusinessType.EXPORT)
async def export_system_config_list(
    request: Request,
    config_page_query: ConfigPageQueryModel = Form(),
    mediator: Mediator = Depends(provide_system_mediator),
):
    config_query = GetConfigListQuery(
        query=config_page_query,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    config_query_result = await mediator.query(config_query)
    config_rows = [row.model_dump(by_alias=True) for row in config_query_result.items]
    config_export_result = await ConfigService.export_config_list_services(config_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(config_export_result))
