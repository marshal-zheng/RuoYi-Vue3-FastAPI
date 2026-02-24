"""
通知公告 Repository
"""
from datetime import datetime, time
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.notice_do import NoticeDO
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class NoticeRepository(BaseRepository[NoticeDO]):
    """通知公告 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, NoticeDO)
    
    async def find_by_id(self, notice_id: int) -> Optional[NoticeDO]:
        """根据ID查找通知"""
        stmt = select(NoticeDO).where(NoticeDO.notice_id == notice_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_content(
        self,
        notice_title: str,
        notice_type: str,
        notice_content: str
    ) -> Optional[NoticeDO]:
        """根据内容查找通知"""
        stmt = select(NoticeDO).where(
            NoticeDO.notice_title == notice_title,
            NoticeDO.notice_type == notice_type,
            NoticeDO.notice_content == notice_content
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        notice_title: Optional[str] = None,
        create_by: Optional[str] = None,
        notice_type: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询通知"""
        conditions = []
        if notice_title:
            conditions.append(NoticeDO.notice_title.like(f'%{notice_title}%'))
        if create_by:
            conditions.append(NoticeDO.create_by.like(f'%{create_by}%'))
        if notice_type:
            conditions.append(NoticeDO.notice_type == notice_type)
        if begin_time and end_time:
            conditions.append(
                NoticeDO.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        query = (
            select(NoticeDO)
            .where(*conditions) if conditions else select(NoticeDO)
        ).order_by(NoticeDO.notice_id).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, notice_id: int) -> int:
        """根据ID删除通知"""
        stmt = delete(NoticeDO).where(NoticeDO.notice_id == notice_id)
        result = await self.db.execute(stmt)
        return result.rowcount
