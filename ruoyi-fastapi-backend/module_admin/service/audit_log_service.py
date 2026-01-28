from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from exceptions.exception import ValidationException
from config.error_codes import ErrorCode
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.audit_vo import AuditLogPageQueryModel, DeleteAuditLogModel
from module_admin.repository import AuditLogRepository
from utils.transaction_manager import transactional


class AuditLogService:
    """
    审计日志管理模块服务层
    """

    @classmethod
    async def get_audit_log_list_services(
        cls, query_db: AsyncSession, query_object: AuditLogPageQueryModel, is_page: bool = False
    ):
        audit_repo = AuditLogRepository(query_db)
        if is_page:
            audit_log_list_result = await audit_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                table_name=query_object.table_name,
                action=query_object.action,
                operator_name=query_object.operator_name,
                request_id=query_object.request_id,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
        else:
            audit_log_list_result = await audit_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                table_name=query_object.table_name,
                action=query_object.action,
                operator_name=query_object.operator_name,
                request_id=query_object.request_id,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
            if hasattr(audit_log_list_result, 'rows'):
                audit_log_list_result = audit_log_list_result.rows

        return audit_log_list_result

    @classmethod
    @transactional()
    async def delete_audit_log_services(cls, query_db: AsyncSession, page_object: DeleteAuditLogModel):
        if page_object.audit_ids:
            audit_repo = AuditLogRepository(query_db)
            audit_id_list = [int(audit_id) for audit_id in page_object.audit_ids.split(',')]
            await audit_repo.delete_by_ids(audit_id_list)
            return CrudResponseModel(is_success=True, message='删除成功')
        raise ValidationException(
            user_message='传入审计日志id为空',
            developer_message='Audit log IDs parameter is empty',
            field='audit_ids'
        )

    @classmethod
    @transactional()
    async def clear_audit_log_services(cls, query_db: AsyncSession):
        audit_repo = AuditLogRepository(query_db)
        await audit_repo.clear_all()
        return CrudResponseModel(is_success=True, message='清除成功')
