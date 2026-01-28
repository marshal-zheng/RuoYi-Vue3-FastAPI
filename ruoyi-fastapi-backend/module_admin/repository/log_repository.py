"""
日志 Repository

P1-019: 包含游标分页优化
"""
from datetime import datetime, time
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, delete, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.log_do import SysOperLog, SysLogininfor
from module_admin.repository.base_repository import BaseRepository
from utils.common_util import SnakeCaseUtil, CamelCaseUtil
from utils.page_util import PageUtil
from utils.time_format_util import TimeFormatUtil


class OperLogRepository(BaseRepository[SysOperLog]):
    """操作日志 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysOperLog)
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        title: Optional[str] = None,
        oper_name: Optional[str] = None,
        business_type: Optional[int] = None,
        status: Optional[int] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order_by_column: Optional[str] = None,
        is_asc: Optional[str] = None
    ):
        """分页查询操作日志"""
        # 排序处理
        if is_asc == 'ascending' and order_by_column:
            order_clause = asc(getattr(SysOperLog, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        elif is_asc == 'descending' and order_by_column:
            order_clause = desc(getattr(SysOperLog, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        else:
            order_clause = desc(SysOperLog.oper_time)
        
        conditions = []
        if title:
            conditions.append(SysOperLog.title.like(f'%{title}%'))
        if oper_name:
            conditions.append(SysOperLog.oper_name.like(f'%{oper_name}%'))
        if business_type is not None:
            conditions.append(SysOperLog.business_type == business_type)
        if status is not None:
            conditions.append(SysOperLog.status == status)
        if begin_time and end_time:
            conditions.append(
                SysOperLog.oper_time.between(
                    datetime.combine(TimeFormatUtil.parse_date(begin_time), time(0, 0, 0)),
                    datetime.combine(TimeFormatUtil.parse_date(end_time), time(23, 59, 59))
                )
            )
        
        query = (
            select(SysOperLog)
            .where(*conditions) if conditions else select(SysOperLog)
        ).order_by(order_clause).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, oper_id: int) -> int:
        """根据ID删除操作日志"""
        stmt = delete(SysOperLog).where(SysOperLog.oper_id == oper_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_ids(self, oper_ids: List[int]) -> int:
        """批量删除操作日志"""
        if not oper_ids:
            return 0
        stmt = delete(SysOperLog).where(SysOperLog.oper_id.in_(oper_ids))
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def clear_all(self) -> int:
        """清空操作日志"""
        stmt = delete(SysOperLog)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def paginate_cursor(
        self,
        page_size: int,
        cursor: Optional[int] = None,
        title: Optional[str] = None,
        oper_name: Optional[str] = None,
        business_type: Optional[int] = None,
        status: Optional[int] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        P1-019: 游标分页查询操作日志
        
        游标分页比 OFFSET 分页更高效，特别是在大数据量下
        - OFFSET 分页: 需要扫描并跳过 N 条记录
        - 游标分页: 直接定位到游标位置，不需要扫描
        
        Args:
            page_size: 每页数量
            cursor: 游标（上一页最后一条记录的 oper_id）
            其他参数: 过滤条件
        
        Returns:
            {
                'rows': [...],
                'next_cursor': int | None,
                'has_more': bool
            }
        """
        conditions = []
        
        if title:
            conditions.append(SysOperLog.title.like(f'%{title}%'))
        if oper_name:
            conditions.append(SysOperLog.oper_name.like(f'%{oper_name}%'))
        if business_type is not None:
            conditions.append(SysOperLog.business_type == business_type)
        if status is not None:
            conditions.append(SysOperLog.status == status)
        if begin_time and end_time:
            conditions.append(
                SysOperLog.oper_time.between(
                    datetime.combine(TimeFormatUtil.parse_date(begin_time), time(0, 0, 0)),
                    datetime.combine(TimeFormatUtil.parse_date(end_time), time(23, 59, 59))
                )
            )
        
        # 游标条件：获取 ID 小于游标的记录（降序排列）
        if cursor is not None:
            conditions.append(SysOperLog.oper_id < cursor)
        
        # 多获取一条，用于判断是否有下一页
        query = (
            select(SysOperLog)
            .where(*conditions) if conditions else select(SysOperLog)
        ).order_by(desc(SysOperLog.oper_id)).limit(page_size + 1)
        
        result = await self.db.execute(query)
        rows = result.scalars().all()
        
        # 判断是否有下一页
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]
        
        # 计算下一个游标
        next_cursor = rows[-1].oper_id if rows else None
        
        return {
            'rows': CamelCaseUtil.transform_result(rows),
            'next_cursor': next_cursor,
            'has_more': has_more,
            'page_size': page_size
        }


class LoginLogRepository(BaseRepository[SysLogininfor]):
    """登录日志 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysLogininfor)
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        ipaddr: Optional[str] = None,
        user_name: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order_by_column: Optional[str] = None,
        is_asc: Optional[str] = None
    ):
        """分页查询登录日志"""
        # 排序处理
        if is_asc == 'ascending' and order_by_column:
            order_clause = asc(getattr(SysLogininfor, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        elif is_asc == 'descending' and order_by_column:
            order_clause = desc(getattr(SysLogininfor, SnakeCaseUtil.camel_to_snake(order_by_column), None))
        else:
            order_clause = desc(SysLogininfor.login_time)
        
        conditions = []
        if ipaddr:
            conditions.append(SysLogininfor.ipaddr.like(f'%{ipaddr}%'))
        if user_name:
            conditions.append(SysLogininfor.user_name.like(f'%{user_name}%'))
        if status:
            conditions.append(SysLogininfor.status == status)
        if begin_time and end_time:
            conditions.append(
                SysLogininfor.login_time.between(
                    datetime.combine(TimeFormatUtil.parse_date(begin_time), time(0, 0, 0)),
                    datetime.combine(TimeFormatUtil.parse_date(end_time), time(23, 59, 59))
                )
            )
        
        query = (
            select(SysLogininfor)
            .where(*conditions) if conditions else select(SysLogininfor)
        ).order_by(order_clause).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, info_id: int) -> int:
        """根据ID删除登录日志"""
        stmt = delete(SysLogininfor).where(SysLogininfor.info_id == info_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_ids(self, info_ids: List[int]) -> int:
        """批量删除登录日志"""
        if not info_ids:
            return 0
        stmt = delete(SysLogininfor).where(SysLogininfor.info_id.in_(info_ids))
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def clear_all(self) -> int:
        """清空登录日志"""
        stmt = delete(SysLogininfor)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def paginate_cursor(
        self,
        page_size: int,
        cursor: Optional[int] = None,
        ipaddr: Optional[str] = None,
        user_name: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        P1-019: 游标分页查询登录日志
        
        游标分页比 OFFSET 分页更高效，特别是在大数据量下
        
        Args:
            page_size: 每页数量
            cursor: 游标（上一页最后一条记录的 info_id）
            其他参数: 过滤条件
        
        Returns:
            {
                'rows': [...],
                'next_cursor': int | None,
                'has_more': bool
            }
        """
        conditions = []
        
        if ipaddr:
            conditions.append(SysLogininfor.ipaddr.like(f'%{ipaddr}%'))
        if user_name:
            conditions.append(SysLogininfor.user_name.like(f'%{user_name}%'))
        if status:
            conditions.append(SysLogininfor.status == status)
        if begin_time and end_time:
            conditions.append(
                SysLogininfor.login_time.between(
                    datetime.combine(TimeFormatUtil.parse_date(begin_time), time(0, 0, 0)),
                    datetime.combine(TimeFormatUtil.parse_date(end_time), time(23, 59, 59))
                )
            )
        
        # 游标条件：获取 ID 小于游标的记录（降序排列）
        if cursor is not None:
            conditions.append(SysLogininfor.info_id < cursor)
        
        # 多获取一条，用于判断是否有下一页
        query = (
            select(SysLogininfor)
            .where(*conditions) if conditions else select(SysLogininfor)
        ).order_by(desc(SysLogininfor.info_id)).limit(page_size + 1)
        
        result = await self.db.execute(query)
        rows = result.scalars().all()
        
        # 判断是否有下一页
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]
        
        # 计算下一个游标
        next_cursor = rows[-1].info_id if rows else None
        
        return {
            'rows': CamelCaseUtil.transform_result(rows),
            'next_cursor': next_cursor,
            'has_more': has_more,
            'page_size': page_size
        }
