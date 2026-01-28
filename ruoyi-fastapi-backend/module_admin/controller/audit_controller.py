from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.audit_vo import AuditLogPageQueryModel, DeleteAuditLogModel
from module_admin.service.audit_log_service import AuditLogService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


auditController = APIRouter(prefix='/monitor', dependencies=[Depends(LoginService.get_current_user)])


@auditController.get(
    '/audit/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:audit:list'))],
)
async def get_system_audit_log_list(
    request: Request,
    audit_log_page_query: AuditLogPageQueryModel = Depends(AuditLogPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    audit_log_page_query_result = await AuditLogService.get_audit_log_list_services(
        query_db, audit_log_page_query, is_page=True
    )
    logger.info('获取成功')
    return ResponseUtil.success(model_content=audit_log_page_query_result)


@auditController.delete('/audit/clean', dependencies=[Depends(CheckUserInterfaceAuth('monitor:audit:remove'))])
@Log(title='审计日志', business_type=BusinessType.CLEAN)
async def clear_system_audit_log(request: Request, query_db: AsyncSession = Depends(get_db)):
    clear_audit_log_result = await AuditLogService.clear_audit_log_services(query_db)
    logger.info(clear_audit_log_result.message)
    return ResponseUtil.success(message=clear_audit_log_result.message)


@auditController.delete('/audit/{audit_ids}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:audit:remove'))])
@Log(title='审计日志', business_type=BusinessType.DELETE)
async def delete_system_audit_log(request: Request, audit_ids: str, query_db: AsyncSession = Depends(get_db)):
    delete_audit_log = DeleteAuditLogModel(auditIds=audit_ids)
    delete_audit_log_result = await AuditLogService.delete_audit_log_services(query_db, delete_audit_log)
    logger.info(delete_audit_log_result.message)
    return ResponseUtil.success(message=delete_audit_log_result.message)
