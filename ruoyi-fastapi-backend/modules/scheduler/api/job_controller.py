from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request
from utils.validation_util import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.job_vo import (
    DeleteJobLogModel,
    DeleteJobModel,
    EditJobModel,
    JobLogPageQueryModel,
    JobModel,
    JobPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.system.application.services import DictDataService, get_dict_data_service
from modules.scheduler.application.job_log_service import JobLogService
from modules.scheduler.application.job_service import JobService
from modules.identity.application.services.login_service import LoginService
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


jobController = APIRouter(prefix='/monitor', dependencies=[Depends(LoginService.get_current_user)])


@jobController.get(
    '/job/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:list'))]
)
async def get_system_job_list(
    request: Request,
    job_page_query: JobPageQueryModel = Depends(JobPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(service_provider('job_service')),
):
    # 获取分页数据
    notice_page_query_result = await job_service.get_job_list_services(job_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=notice_page_query_result)


@jobController.post('/job', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:add'))])
@ValidateFields(validate_model='add_job')
@Log(title='定时任务', business_type=BusinessType.INSERT)
async def add_system_job(
    request: Request,
    add_job: JobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    job_service: JobService = Depends(service_provider('job_service')),
):
    add_job.create_by = current_user.user.user_name
    add_job.create_time = datetime.now()
    add_job.update_by = current_user.user.user_name
    add_job.update_time = datetime.now()
    add_job_result = await job_service.add_job_services(add_job)
    logger.info(add_job_result.message)

    return ResponseUtil.success(message=add_job_result.message)


@jobController.put('/job', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:edit'))])
@ValidateFields(validate_model='edit_job')
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def edit_system_job(
    request: Request,
    edit_job: EditJobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    job_service: JobService = Depends(service_provider('job_service')),
):
    edit_job.update_by = current_user.user.user_name
    edit_job.update_time = datetime.now()
    edit_job_result = await job_service.edit_job_services(edit_job)
    logger.info(edit_job_result.message)

    return ResponseUtil.success(message=edit_job_result.message)


@jobController.put('/job/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:changeStatus'))])
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def change_system_job_status(
    request: Request,
    change_job: EditJobModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    job_service: JobService = Depends(service_provider('job_service')),
):
    edit_job = EditJobModel(
        jobId=change_job.job_id,
        status=change_job.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    edit_job_result = await job_service.edit_job_services(edit_job)
    logger.info(edit_job_result.message)

    return ResponseUtil.success(message=edit_job_result.message)


@jobController.put('/job/run', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:changeStatus'))])
@Log(title='定时任务', business_type=BusinessType.UPDATE)
async def execute_system_job(
    request: Request,
    execute_job: JobModel,
    query_db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(service_provider('job_service')),
):
    execute_job_result = await job_service.execute_job_once_services(execute_job)
    logger.info(execute_job_result.message)

    return ResponseUtil.success(message=execute_job_result.message)


@jobController.delete('/job/{job_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务', business_type=BusinessType.DELETE)
async def delete_system_job(
    request: Request,
    job_ids: str,
    query_db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(service_provider('job_service')),
):
    delete_job = DeleteJobModel(jobIds=job_ids)
    delete_job_result = await job_service.delete_job_services(delete_job)
    logger.info(delete_job_result.message)

    return ResponseUtil.success(message=delete_job_result.message)


@jobController.get(
    '/job/{job_id}', response_model=JobModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:query'))]
)
async def query_detail_system_job(
    request: Request,
    job_id: int,
    query_db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(service_provider('job_service')),
):
    job_detail_result = await job_service.job_detail_services(job_id)
    logger.info(f'获取job_id为{job_id}的信息成功')

    return ResponseUtil.success(data=job_detail_result)


@jobController.post('/job/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:export'))])
@Log(title='定时任务', business_type=BusinessType.EXPORT)
async def export_system_job_list(
    request: Request,
    job_page_query: JobPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(service_provider('job_service')),
    dict_data_service: DictDataService = Depends(get_dict_data_service),
):
    # 获取全量数据
    job_query_result = await job_service.get_job_list_services(job_page_query, is_page=False)
    job_export_result = await job_service.export_job_list_services(request, job_query_result, dict_data_service)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(job_export_result))


@jobController.get(
    '/jobLog/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:list'))]
)
async def get_system_job_log_list(
    request: Request,
    job_log_page_query: JobLogPageQueryModel = Depends(JobLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    job_log_service: JobLogService = Depends(service_provider('job_log_service')),
):
    # 获取分页数据
    job_log_page_query_result = await job_log_service.get_job_log_list_services(job_log_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=job_log_page_query_result)


@jobController.delete('/jobLog/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务调度日志', business_type=BusinessType.CLEAN)
async def clear_system_job_log(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    job_log_service: JobLogService = Depends(service_provider('job_log_service')),
):
    clear_job_log_result = await job_log_service.clear_job_log_services()
    logger.info(clear_job_log_result.message)

    return ResponseUtil.success(message=clear_job_log_result.message)


@jobController.delete('/jobLog/{job_log_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:remove'))])
@Log(title='定时任务调度日志', business_type=BusinessType.DELETE)
async def delete_system_job_log(
    request: Request,
    job_log_ids: str,
    query_db: AsyncSession = Depends(get_db),
    job_log_service: JobLogService = Depends(service_provider('job_log_service')),
):
    delete_job_log = DeleteJobLogModel(jobLogIds=job_log_ids)
    delete_job_log_result = await job_log_service.delete_job_log_services(delete_job_log)
    logger.info(delete_job_log_result.message)

    return ResponseUtil.success(message=delete_job_log_result.message)


@jobController.post('/jobLog/export', dependencies=[Depends(CheckUserInterfaceAuth('monitor:job:export'))])
@Log(title='定时任务调度日志', business_type=BusinessType.EXPORT)
async def export_system_job_log_list(
    request: Request,
    job_log_page_query: JobLogPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    job_log_service: JobLogService = Depends(service_provider('job_log_service')),
    dict_data_service: DictDataService = Depends(get_dict_data_service),
):
    # 获取全量数据
    job_log_query_result = await job_log_service.get_job_log_list_services(job_log_page_query, is_page=False)
    job_log_export_result = await job_log_service.export_job_log_list_services(
        request, job_log_query_result, dict_data_service
    )
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(job_log_export_result))
