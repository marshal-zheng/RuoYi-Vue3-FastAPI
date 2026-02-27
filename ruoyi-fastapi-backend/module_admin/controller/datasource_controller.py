from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.datasource_vo import DataSourceQueryModel, DataSourceModel, TestConnectionModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.datasource_service import DataSourceService
from modules.identity.application.services.login_service import LoginService
from utils.log_util import logger
from utils.response_util import ResponseUtil


datasourceController = APIRouter(prefix='/datasource', dependencies=[Depends(LoginService.get_current_user)])


@datasourceController.get('/list', dependencies=[Depends(CheckUserInterfaceAuth('datasource:list'))])
async def get_datasource_list(
    request: Request,
    name: str = None,
    type: str = None,
    status: str = None,
    page_num: int = 1,
    page_size: int = 10,
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    query = DataSourceQueryModel(name=name, type=type, status=status, page_num=page_num, page_size=page_size)
    result = await datasource_service.get_datasource_list_services(query)
    return ResponseUtil.success(rows=result['rows'], dict_content={'total': result['total']})


@datasourceController.get('/{datasource_id}', dependencies=[Depends(CheckUserInterfaceAuth('datasource:query'))])
async def get_datasource_detail(
    request: Request,
    datasource_id: int,
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.datasource_detail_services(datasource_id)
    return ResponseUtil.success(data=result)


@datasourceController.post('', dependencies=[Depends(CheckUserInterfaceAuth('datasource:add'))])
@Log(title='数据源管理', business_type=BusinessType.INSERT)
async def add_datasource(
    request: Request,
    data: DataSourceModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.add_datasource_services(data, current_user.user.user_name)
    return ResponseUtil.success(message=result.message)


@datasourceController.put('', dependencies=[Depends(CheckUserInterfaceAuth('datasource:edit'))])
@Log(title='数据源管理', business_type=BusinessType.UPDATE)
async def update_datasource(
    request: Request,
    data: DataSourceModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.edit_datasource_services(data, current_user.user.user_name)
    return ResponseUtil.success(message=result.message)


@datasourceController.delete('/{datasource_ids}', dependencies=[Depends(CheckUserInterfaceAuth('datasource:remove'))])
@Log(title='数据源管理', business_type=BusinessType.DELETE)
async def delete_datasource(
    request: Request,
    datasource_ids: str,
    query_db: AsyncSession = Depends(get_db),
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.delete_datasource_services(datasource_ids)
    return ResponseUtil.success(message=result.message)


@datasourceController.post('/test-connection', dependencies=[Depends(CheckUserInterfaceAuth('datasource:query'))])
async def test_datasource_connection(
    request: Request,
    data: TestConnectionModel,
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.test_connection_services(data)
    return ResponseUtil.success(
        data={'success': result.success, 'message': result.message, 'latencyMs': result.latency_ms}
    )


@datasourceController.post('/{datasource_id}/test', dependencies=[Depends(CheckUserInterfaceAuth('datasource:query'))])
async def test_saved_datasource(
    request: Request,
    datasource_id: int,
    datasource_service: DataSourceService = Depends(service_provider('datasource_service')),
):
    result = await datasource_service.test_saved_connection_services(datasource_id)
    return ResponseUtil.success(
        data={'success': result.success, 'message': result.message, 'latencyMs': result.latency_ms}
    )
