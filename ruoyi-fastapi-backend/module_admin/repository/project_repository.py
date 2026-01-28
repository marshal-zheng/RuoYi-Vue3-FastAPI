"""
项目 Repository
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.project_do import SysProject
from module_admin.entity.do.enums import DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class ProjectRepository(BaseRepository[SysProject]):
    """项目 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysProject)
    
    async def find_by_id(self, project_id: int) -> Optional[SysProject]:
        """根据ID查找项目"""
        stmt = select(SysProject).where(
            SysProject.project_id == project_id,
            SysProject.del_flag == DelFlagEnum.EXIST.value
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self) -> List[SysProject]:
        """获取所有有效项目"""
        stmt = (
            select(SysProject)
            .where(SysProject.del_flag == DelFlagEnum.EXIST.value)
            .order_by(desc(SysProject.create_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询项目"""
        conditions = [SysProject.del_flag == DelFlagEnum.EXIST.value]
        
        if begin_time and end_time:
            conditions.append(SysProject.create_time.between(begin_time, end_time))
        
        query = (
            select(SysProject)
            .where(*conditions)
            .order_by(desc(SysProject.create_time))
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def soft_delete(self, project_id: int, update_by: str) -> bool:
        """软删除项目"""
        stmt = (
            update(SysProject)
            .where(SysProject.project_id == project_id)
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
    
    async def soft_delete_batch(
        self,
        project_ids: List[int],
        update_by: str
    ) -> int:
        """批量软删除项目"""
        if not project_ids:
            return 0
        stmt = (
            update(SysProject)
            .where(SysProject.project_id.in_(project_ids))
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
