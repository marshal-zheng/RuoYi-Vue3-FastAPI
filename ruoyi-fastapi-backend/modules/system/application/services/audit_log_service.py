from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable, Optional
from exceptions.exception import ValidationException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.audit_vo import AuditLogPageQueryModel, DeleteAuditLogModel
from modules.system.infrastructure.audit_log_repository import AuditLogRepository
from utils.transaction_manager import transactional
from ports import IAuditLogRepository


class AuditLogService:
    """
    审计日志管理模块服务层
    """

    def __init__(
        self,
        query_db: Optional[AsyncSession] = None,
        audit_repo_factory: Optional[Callable[[AsyncSession], IAuditLogRepository]] = None,
    ):
        self.query_db = query_db
        self._audit_repo_factory = audit_repo_factory or AuditLogRepository

    def _resolve_query_db(self, query_db: Optional[AsyncSession]) -> AsyncSession:
        resolved_db = query_db or self.query_db
        if resolved_db is None:
            raise RuntimeError('query_db dependency is not configured')
        return resolved_db

    def _audit_repo(self, query_db: Optional[AsyncSession] = None) -> IAuditLogRepository:
        return self._audit_repo_factory(self._resolve_query_db(query_db))

    async def get_audit_log_list_services(
        self, query_db: AsyncSession, query_object: AuditLogPageQueryModel, is_page: bool = False
    ):
        audit_repo = self._audit_repo(query_db)
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

    @transactional()
    async def delete_audit_log_services(self, query_db: AsyncSession, page_object: DeleteAuditLogModel):
        if page_object.audit_ids:
            audit_repo = self._audit_repo(query_db)
            audit_id_list = [int(audit_id) for audit_id in page_object.audit_ids.split(',')]
            await audit_repo.delete_by_ids(audit_id_list)
            return CrudResponseModel(is_success=True, message='删除成功')
        raise ValidationException(
            user_message='传入审计日志id为空', developer_message='Audit log IDs parameter is empty', field='audit_ids'
        )

    @transactional()
    async def clear_audit_log_services(self, query_db: AsyncSession):
        audit_repo = self._audit_repo(query_db)
        await audit_repo.clear_all()
        return CrudResponseModel(is_success=True, message='清除成功')
