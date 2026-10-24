from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.http_contracts import CollectionResult
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.dict_vo import (
    DeleteDictDataModel,
    DeleteDictTypeModel,
    DictDataModel,
    DictDataPageQueryModel,
    DictTypeModel,
    DictTypePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddDictDataCommand,
    AddDictTypeCommand,
    DeleteDictDataCommand,
    DeleteDictTypeCommand,
    EditDictDataCommand,
    EditDictTypeCommand,
    RefreshDictCacheCommand,
)
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetDictDataByTypeQuery,
    GetDictDataDetailQuery,
    GetDictDataListQuery,
    GetDictTypeDetailQuery,
    GetDictTypeListQuery,
    GetDictTypeOptionsQuery,
)
from modules.system.application.services import (
    DictDataService,
    DictTypeService,
    get_dict_data_service,
    get_dict_type_service,
)
from utils.common_util import bytes2file_response
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

dictController = APIRouter(prefix='/system/dict', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_dict_type_detail(request: Request, *, dict_id: int, mediator: Mediator):
    detail_query = GetDictTypeDetailQuery(
        dict_id=dict_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(detail_query)


async def _load_dict_data_detail(request: Request, *, dict_code: int, mediator: Mediator):
    detail_query = GetDictDataDetailQuery(
        dict_code=dict_code,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(detail_query)


@dictController.get(
    '/type/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:list'))]
)
async def get_system_dict_type_list(
    request: Request,
    dict_type_page_query: DictTypePageQueryModel = Depends(DictTypePageQueryModel.as_query),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_type_query = GetDictTypeListQuery(
        query=dict_type_page_query,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_type_page_query_result = await mediator.query(dict_type_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dict_type_page_query_result)


@dictController.post('/type', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:add'))])
@ValidateFields(validate_model='add_dict_type')
@Log(title='字典类型', business_type=BusinessType.INSERT)
async def add_system_dict_type(
    request: Request,
    add_dict_type: DictTypeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_command = AddDictTypeCommand(
        query_db=query_db,
        dict_type=add_dict_type,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    dict_id = require_int_value(add_result.data, 'dictId', 'dict_id', contract_name='system.dict-type.create')
    resource = await _load_dict_type_detail(request, dict_id=int(dict_id), mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/dict/type/{dict_id}')
    return ResponseUtil.created_resource(resource, location=location)


@dictController.put('/type', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:edit'))])
@ValidateFields(validate_model='edit_dict_type')
@Log(title='字典类型', business_type=BusinessType.UPDATE)
async def edit_system_dict_type(
    request: Request,
    edit_dict_type: DictTypeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_command = EditDictTypeCommand(
        query_db=query_db,
        dict_type=edit_dict_type,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_dict_type_detail(request, dict_id=edit_dict_type.dict_id, mediator=mediator)
    return ResponseUtil.ok_resource(resource)


@dictController.delete('/type/refreshCache', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典类型', business_type=BusinessType.UPDATE)
async def refresh_system_dict(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    refresh_command = RefreshDictCacheCommand(
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


@dictController.delete('/type/{dict_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典类型', business_type=BusinessType.DELETE)
async def delete_system_dict_type(
    request: Request,
    dict_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_dict_type = DeleteDictTypeModel(dictIds=dict_ids)
    delete_command = DeleteDictTypeCommand(
        query_db=query_db,
        delete_dict_type=delete_dict_type,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@dictController.get('/type/optionselect', response_model=CollectionResult[DictTypeModel])
async def query_system_dict_type_options(
    request: Request,
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_type_query = GetDictTypeOptionsQuery(
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_type_query_result = await mediator.query(dict_type_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dict_type_query_result)


@dictController.get(
    '/type/{dict_id}', response_model=DictTypeModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:query'))]
)
async def query_detail_system_dict_type(
    request: Request,
    dict_id: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetDictTypeDetailQuery(
        dict_id=dict_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_type_detail_result = await mediator.query(detail_query)
    logger.info(f'获取dict_id为{dict_id}的信息成功')

    return ResponseUtil.ok_resource(dict_type_detail_result)


@dictController.post('/type/export', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:export'))])
@Log(title='字典类型', business_type=BusinessType.EXPORT)
async def export_system_dict_type_list(
    request: Request,
    dict_type_page_query: DictTypePageQueryModel = Form(),
    dict_type_service: DictTypeService = Depends(get_dict_type_service),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_type_query = GetDictTypeListQuery(
        query=dict_type_page_query,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_type_query_result = await mediator.query(dict_type_query)
    dict_type_rows = [row.model_dump(by_alias=True) for row in dict_type_query_result.items]
    dict_type_export_result = await dict_type_service.export_dict_type_list_services(dict_type_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(dict_type_export_result))


@dictController.get('/data/type/{dict_type}')
async def query_system_dict_type_data(
    request: Request,
    dict_type: str,
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_data_query = GetDictDataByTypeQuery(
        dict_type=dict_type,
        redis_client=getattr(request.app.state, 'redis', None),
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_data_query_result = await mediator.query(dict_data_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dict_data_query_result)


@dictController.get(
    '/data/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:list'))]
)
async def get_system_dict_data_list(
    request: Request,
    dict_data_page_query: DictDataPageQueryModel = Depends(DictDataPageQueryModel.as_query),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_data_query = GetDictDataListQuery(
        query=dict_data_page_query,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_data_page_query_result = await mediator.query(dict_data_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(dict_data_page_query_result)


@dictController.post('/data', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:add'))])
@ValidateFields(validate_model='add_dict_data')
@Log(title='字典数据', business_type=BusinessType.INSERT)
async def add_system_dict_data(
    request: Request,
    add_dict_data: DictDataModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_command = AddDictDataCommand(
        query_db=query_db,
        dict_data=add_dict_data,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    dict_code = require_int_value(add_result.data, 'dictCode', 'dict_code', contract_name='system.dict-data.create')
    resource = await _load_dict_data_detail(request, dict_code=int(dict_code), mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/dict/data/{dict_code}')
    return ResponseUtil.created_resource(resource, location=location)


@dictController.put('/data', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:edit'))])
@ValidateFields(validate_model='edit_dict_data')
@Log(title='字典数据', business_type=BusinessType.UPDATE)
async def edit_system_dict_data(
    request: Request,
    edit_dict_data: DictDataModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_command = EditDictDataCommand(
        query_db=query_db,
        dict_data=edit_dict_data,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_dict_data_detail(request, dict_code=edit_dict_data.dict_code, mediator=mediator)
    return ResponseUtil.ok_resource(resource)


@dictController.delete('/data/{dict_codes}', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典数据', business_type=BusinessType.DELETE)
async def delete_system_dict_data(
    request: Request,
    dict_codes: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_dict_data = DeleteDictDataModel(dictCodes=dict_codes)
    delete_command = DeleteDictDataCommand(
        query_db=query_db,
        delete_dict_data=delete_dict_data,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@dictController.get(
    '/data/{dict_code}',
    response_model=DictDataModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:dict:query'))],
)
async def query_detail_system_dict_data(
    request: Request,
    dict_code: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetDictDataDetailQuery(
        dict_code=dict_code,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    detail_dict_data_result = await mediator.query(detail_query)
    logger.info(f'获取dict_code为{dict_code}的信息成功')

    return ResponseUtil.ok_resource(detail_dict_data_result)


@dictController.post('/data/export', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:export'))])
@Log(title='字典数据', business_type=BusinessType.EXPORT)
async def export_system_dict_data_list(
    request: Request,
    dict_data_page_query: DictDataPageQueryModel = Form(),
    dict_data_service: DictDataService = Depends(get_dict_data_service),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dict_data_query = GetDictDataListQuery(
        query=dict_data_page_query,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dict_data_query_result = await mediator.query(dict_data_query)
    dict_data_rows = [row.model_dump(by_alias=True) for row in dict_data_query_result.items]
    dict_data_export_result = await dict_data_service.export_dict_data_list_services(dict_data_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(dict_data_export_result))
