from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.online_vo import DeleteOnlineModel, OnlineQueryModel
from modules.identity.ports import get_current_user
from modules.system.application.services.online_service import OnlineService
from utils.log_util import logger
from utils.response_util import ResponseUtil


onlineController = APIRouter(prefix='/monitor/online', dependencies=[Depends(get_current_user)])


@onlineController.get('/list', dependencies=[Depends(CheckUserInterfaceAuth('monitor:online:list'))])
async def get_monitor_online_list(
    request: Request,
    online_page_query: OnlineQueryModel = Depends(OnlineQueryModel.as_query),
    online_service: OnlineService = Depends(service_provider('online_service', require_session=False)),
):
    # 获取全量数据
    online_query_result = await online_service.get_online_list_services(request, online_page_query)
    logger.info('获取成功')

    return ResponseUtil.ok_collection(items=online_query_result)


@onlineController.delete('/{token_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:online:forceLogout'))])
@Log(title='在线用户', business_type=BusinessType.FORCE)
async def delete_monitor_online(
    request: Request,
    token_ids: str,
    query_db: AsyncSession = Depends(get_db),
    online_service: OnlineService = Depends(service_provider('online_service', require_session=False)),
):
    delete_online = DeleteOnlineModel(tokenIds=token_ids)
    delete_online_result = await online_service.delete_online_services(request, delete_online)
    logger.info(delete_online_result.message)

    return ResponseUtil.no_content()
