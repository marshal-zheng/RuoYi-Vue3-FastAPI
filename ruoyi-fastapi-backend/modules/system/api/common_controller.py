from fastapi import APIRouter, Depends, Request

from container.dependencies import service_provider
from modules.identity.ports import get_current_user
from modules.system.application.services.common_service import CommonService
from utils.log_util import logger
from utils.response_util import ResponseUtil

# Persistent files moved to /file-assets; the legacy upload/download/resource endpoints are retired.
commonController = APIRouter(prefix='/common', dependencies=[Depends(get_current_user)])


@commonController.get('/tables')
async def get_table_names(
    request: Request,
    common_service: CommonService = Depends(service_provider('common_service')),
):
    """
    获取数据库表名列表
    """
    table_list = await common_service.get_table_names_services()
    logger.info('获取表名列表成功')

    return ResponseUtil.ok_resource(table_list)
