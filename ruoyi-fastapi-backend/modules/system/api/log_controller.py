from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.log_vo import (
    DeleteLoginLogModel,
    DeleteOperLogModel,
    LoginLogPageQueryModel,
    OperLogPageQueryModel,
    UnlockUser,
)
from modules.system.application.services import DictDataService, get_dict_data_service
from modules.system.application.services.log_service import LoginLogService, OperationLogService
from modules.identity.ports import get_current_user
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


logController = APIRouter(prefix='/monitor', dependencies=[Depends(get_current_user)])


@logController.get(
    '/operlog/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:list'))],
)
async def get_system_operation_log_list(
    request: Request,
    operation_log_page_query: OperLogPageQueryModel = Depends(OperLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    operation_log_service: OperationLogService = Depends(service_provider('operation_log_service')),
):
    # 获取分页数据
    operation_log_page_query_result = await operation_log_service.get_operation_log_list_services(
        operation_log_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=operation_log_page_query_result)


@logController.delete('/operlog/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:remove'))])
@Log(title='操作日志', business_type=BusinessType.CLEAN)
async def clear_system_operation_log(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    operation_log_service: OperationLogService = Depends(service_provider('operation_log_service')),
):
    clear_operation_log_result = await operation_log_service.clear_operation_log_services()
    logger.info(clear_operation_log_result.message)

    return ResponseUtil.success(message=clear_operation_log_result.message)


@logController.delete('/operlog/{oper_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:remove'))])
@Log(title='操作日志', business_type=BusinessType.DELETE)
async def delete_system_operation_log(
    request: Request,
    oper_ids: str,
    query_db: AsyncSession = Depends(get_db),
    operation_log_service: OperationLogService = Depends(service_provider('operation_log_service')),
):
    delete_operation_log = DeleteOperLogModel(operIds=oper_ids)
    delete_operation_log_result = await operation_log_service.delete_operation_log_services(delete_operation_log)
    logger.info(delete_operation_log_result.message)

    return ResponseUtil.success(message=delete_operation_log_result.message)


@logController.post('/operlog/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:operlog:export'))])
@Log(title='操作日志', business_type=BusinessType.EXPORT)
async def export_system_operation_log_list(
    request: Request,
    operation_log_page_query: OperLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    operation_log_service: OperationLogService = Depends(service_provider('operation_log_service')),
    dict_data_service: DictDataService = Depends(get_dict_data_service),
):
    # 获取全量数据
    operation_log_query_result = await operation_log_service.get_operation_log_list_services(
        operation_log_page_query, is_page=False
    )
    operation_log_export_result = await operation_log_service.export_operation_log_list_services(
        request, operation_log_query_result, dict_data_service
    )
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(operation_log_export_result))


@logController.get(
    '/logininfor/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:list'))],
)
async def get_system_login_log_list(
    request: Request,
    login_log_page_query: LoginLogPageQueryModel = Depends(LoginLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    login_log_service: LoginLogService = Depends(service_provider('login_log_service')),
):
    # 获取分页数据
    login_log_page_query_result = await login_log_service.get_login_log_list_services(
        login_log_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=login_log_page_query_result)


@logController.delete('/logininfor/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:remove'))])
@Log(title='登录日志', business_type=BusinessType.CLEAN)
async def clear_system_login_log(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    login_log_service: LoginLogService = Depends(service_provider('login_log_service')),
):
    clear_login_log_result = await login_log_service.clear_login_log_services()
    logger.info(clear_login_log_result.message)

    return ResponseUtil.success(message=clear_login_log_result.message)


@logController.delete(
    '/logininfor/{info_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:remove'))]
)
@Log(title='登录日志', business_type=BusinessType.DELETE)
async def delete_system_login_log(
    request: Request,
    info_ids: str,
    query_db: AsyncSession = Depends(get_db),
    login_log_service: LoginLogService = Depends(service_provider('login_log_service')),
):
    delete_login_log = DeleteLoginLogModel(infoIds=info_ids)
    delete_login_log_result = await login_log_service.delete_login_log_services(delete_login_log)
    logger.info(delete_login_log_result.message)

    return ResponseUtil.success(message=delete_login_log_result.message)


@logController.get(
    '/logininfor/unlock/{user_name}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:unlock'))]
)
@Log(title='账户解锁', business_type=BusinessType.OTHER)
async def unlock_system_user(
    request: Request,
    user_name: str,
    query_db: AsyncSession = Depends(get_db),
    login_log_service: LoginLogService = Depends(service_provider('login_log_service')),
):
    unlock_user = UnlockUser(userName=user_name)
    unlock_user_result = await login_log_service.unlock_user_services(request, unlock_user)
    logger.info(unlock_user_result.message)

    return ResponseUtil.success(message=unlock_user_result.message)


@logController.post('/logininfor/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:logininfor:export'))])
@Log(title='登录日志', business_type=BusinessType.EXPORT)
async def export_system_login_log_list(
    request: Request,
    login_log_page_query: LoginLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    login_log_service: LoginLogService = Depends(service_provider('login_log_service')),
):
    # 获取全量数据
    login_log_query_result = await login_log_service.get_login_log_list_services(login_log_page_query, is_page=False)
    login_log_export_result = await login_log_service.export_login_log_list_services(login_log_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(login_log_export_result))
