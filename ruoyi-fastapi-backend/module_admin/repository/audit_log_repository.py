"""
审计日志 Repository
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import select, delete, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.audit_log_do import SysAuditLog
from module_admin.repository.base_repository import BaseRepository
from utils.common_util import SnakeCaseUtil
from utils.page_util import PageUtil
from utils.time_format_util import TimeFormatUtil


class AuditLogRepository(BaseRepository[SysAuditLog]):
    """审计日志 Repository"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, SysAuditLog)

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        table_name: Optional[str] = None,
        action: Optional[str] = None,
        operator_name: Optional[str] = None,
        request_id: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order_by_column: Optional[str] = None,
        is_asc: Optional[str] = None,
    ):
        if is_asc == 'ascending' and order_by_column:
            order_clause = asc(getattr(SysAuditLog, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        elif is_asc == 'descending' and order_by_column:
            order_clause = desc(getattr(SysAuditLog, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        else:
            order_clause = desc(SysAuditLog.create_time)

        conditions = []
        if table_name:
            conditions.append(SysAuditLog.table_name.like(f'%{table_name}%'))
        if action:
            conditions.append(SysAuditLog.action == action)
        if operator_name:
            conditions.append(SysAuditLog.operator_name.like(f'%{operator_name}%'))
        if request_id:
            conditions.append(SysAuditLog.request_id == request_id)
        if begin_time and end_time:
            conditions.append(
                SysAuditLog.create_time.between(
                    datetime.combine(TimeFormatUtil.parse_date(begin_time), time(0, 0, 0)),
                    datetime.combine(TimeFormatUtil.parse_date(end_time), time(23, 59, 59)),
                )
            )

        query = (select(SysAuditLog).where(*conditions) if conditions else select(SysAuditLog)).order_by(order_clause)
        return await PageUtil.paginate(self.db, query, page, page_size, True)

    async def delete_by_id(self, audit_id: int) -> int:
        stmt = delete(SysAuditLog).where(SysAuditLog.audit_id == audit_id)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def delete_by_ids(self, audit_ids: List[int]) -> int:
        if not audit_ids:
            return 0
        stmt = delete(SysAuditLog).where(SysAuditLog.audit_id.in_(audit_ids))
        result = await self.db.execute(stmt)
        return result.rowcount

    async def clear_all(self) -> int:
        stmt = delete(SysAuditLog)
        result = await self.db.execute(stmt)
        return result.rowcount
