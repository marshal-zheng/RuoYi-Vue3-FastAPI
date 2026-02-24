from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile
from container.dependencies import service_provider
from modules.system.application.services.common_service import CommonService
from modules.identity.ports import get_current_user
from utils.log_util import logger
from utils.response_util import ResponseUtil

commonController = APIRouter(prefix='/common', dependencies=[Depends(get_current_user)])


@commonController.post('/upload')
async def common_upload(
    request: Request,
    file: UploadFile = File(...),
    common_service: CommonService = Depends(service_provider('common_service')),
):
    upload_result = await common_service.upload_service(request, file)
    logger.info('上传成功')

    return ResponseUtil.success(model_content=upload_result.result)


@commonController.get('/download')
async def common_download(
    request: Request,
    background_tasks: BackgroundTasks,
    file_name: str = Query(alias='fileName'),
    delete: bool = Query(),
    common_service: CommonService = Depends(service_provider('common_service')),
):
    download_result = await common_service.download_services(background_tasks, file_name, delete)
    logger.info(download_result.message)

    return ResponseUtil.streaming(data=download_result.result)


@commonController.get('/download/resource')
async def common_download_resource(
    request: Request,
    resource: str = Query(),
    common_service: CommonService = Depends(service_provider('common_service')),
):
    download_resource_result = await common_service.download_resource_services(resource)
    logger.info(download_resource_result.message)

    return ResponseUtil.streaming(data=download_resource_result.result)


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

    return ResponseUtil.success(data=table_list)
