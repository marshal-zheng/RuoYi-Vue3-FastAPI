"""
定时任务 Repository
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from module_admin.entity.do.job_do import SysJob, SysJobLog
from module_admin.entity.do.enums import JobStatusEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class JobRepository(BaseRepository[SysJob]):
    """定时任务 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysJob)
    
    async def find_by_id(self, job_id: int) -> Optional[SysJob]:
        """根据ID查找定时任务"""
        stmt = select(SysJob).where(SysJob.job_id == job_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_info(
        self,
        job_name: Optional[str] = None,
        job_group: Optional[str] = None,
        job_executor: Optional[str] = None,
        invoke_target: Optional[str] = None,
        job_args: Optional[str] = None,
        job_kwargs: Optional[str] = None,
        cron_expression: Optional[str] = None
    ) -> Optional[SysJob]:
        """根据任务信息查找"""
        conditions = []
        if job_name:
            conditions.append(SysJob.job_name == job_name)
        if job_group:
            conditions.append(SysJob.job_group == job_group)
        if job_executor:
            conditions.append(SysJob.job_executor == job_executor)
        if invoke_target:
            conditions.append(SysJob.invoke_target == invoke_target)
        if job_args:
            conditions.append(SysJob.job_args == job_args)
        if job_kwargs:
            conditions.append(SysJob.job_kwargs == job_kwargs)
        if cron_expression:
            conditions.append(SysJob.cron_expression == cron_expression)
        
        if not conditions:
            return None
        
        stmt = select(SysJob).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self) -> List[SysJob]:
        """获取所有激活的定时任务（用于调度器）"""
        stmt = (
            select(SysJob)
            .where(SysJob.status == JobStatusEnum.NORMAL.value)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        job_name: Optional[str] = None,
        job_group: Optional[str] = None,
        status: Optional[str] = None
    ):
        """分页查询定时任务"""
        conditions = []
        if job_name:
            conditions.append(SysJob.job_name.like(f'%{job_name}%'))
        if job_group:
            conditions.append(SysJob.job_group == job_group)
        if status:
            conditions.append(SysJob.status == status)
        
        query = (
            select(SysJob)
            .where(*conditions) if conditions else select(SysJob)
        ).order_by(SysJob.job_id).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, job_id: int) -> int:
        """根据ID删除定时任务"""
        stmt = delete(SysJob).where(SysJob.job_id == job_id)
        result = await self.db.execute(stmt)
        return result.rowcount


class JobLogRepository(BaseRepository[SysJobLog]):
    """定时任务日志 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysJobLog)
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        job_name: Optional[str] = None,
        job_group: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询任务日志"""
        conditions = []
        if job_name:
            conditions.append(SysJobLog.job_name.like(f'%{job_name}%'))
        if job_group:
            conditions.append(SysJobLog.job_group == job_group)
        if status:
            conditions.append(SysJobLog.status == status)
        if begin_time and end_time:
            conditions.append(
                SysJobLog.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        query = (
            select(SysJobLog)
            .where(*conditions) if conditions else select(SysJobLog)
        ).order_by(desc(SysJobLog.create_time)).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    def add_sync(self, db: Session, job_log: SysJobLog) -> SysJobLog:
        """同步添加任务日志（用于调度器回调）"""
        db.add(job_log)
        db.flush()
        return job_log
    
    async def delete_by_id(self, job_log_id: int) -> int:
        """根据ID删除任务日志"""
        stmt = delete(SysJobLog).where(SysJobLog.job_log_id == job_log_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_ids(self, job_log_ids: List[int]) -> int:
        """批量删除任务日志"""
        if not job_log_ids:
            return 0
        stmt = delete(SysJobLog).where(SysJobLog.job_log_id.in_(job_log_ids))
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def clear_all(self) -> int:
        """清空任务日志"""
        stmt = delete(SysJobLog)
        result = await self.db.execute(stmt)
        return result.rowcount
