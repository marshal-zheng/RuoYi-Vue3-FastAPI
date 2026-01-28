"""
岗位 Repository
"""
from typing import Optional, List
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.user_do import SysUserPost
from module_admin.entity.do.enums import StatusEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class PostRepository(BaseRepository[SysPost]):
    """岗位 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysPost)
    
    async def find_by_id(self, post_id: int) -> Optional[SysPost]:
        """根据ID查找岗位"""
        stmt = select(SysPost).where(SysPost.post_id == post_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_active_by_id(self, post_id: int) -> Optional[SysPost]:
        """根据ID查找有效岗位"""
        stmt = select(SysPost).where(
            SysPost.post_id == post_id,
            SysPost.status == StatusEnum.NORMAL.value
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_name_or_code(
        self,
        post_name: Optional[str] = None,
        post_code: Optional[str] = None,
        post_sort: Optional[int] = None
    ) -> Optional[SysPost]:
        """根据名称或编码查找岗位"""
        conditions = []
        if post_name:
            conditions.append(SysPost.post_name == post_name)
        if post_code:
            conditions.append(SysPost.post_code == post_code)
        if post_sort is not None:
            conditions.append(SysPost.post_sort == post_sort)
        
        stmt = select(SysPost).where(*conditions) if conditions else select(SysPost)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        post_code: Optional[str] = None,
        post_name: Optional[str] = None,
        status: Optional[str] = None
    ):
        """分页查询岗位"""
        conditions = []
        if post_code:
            conditions.append(SysPost.post_code.like(f'%{post_code}%'))
        if post_name:
            conditions.append(SysPost.post_name.like(f'%{post_name}%'))
        if status:
            conditions.append(SysPost.status == status)
        
        query = (
            select(SysPost)
            .where(*conditions) if conditions else select(SysPost)
        ).order_by(SysPost.post_sort).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def find_all_with_filters(
        self,
        post_code: Optional[str] = None,
        post_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SysPost]:
        """查询岗位列表（不分页）"""
        conditions = []
        if post_code:
            conditions.append(SysPost.post_code.like(f'%{post_code}%'))
        if post_name:
            conditions.append(SysPost.post_name.like(f'%{post_name}%'))
        if status:
            conditions.append(SysPost.status == status)
        
        stmt = (
            select(SysPost)
            .where(*conditions) if conditions else select(SysPost)
        ).order_by(SysPost.post_sort).distinct()
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_id(self, post_id: int) -> int:
        """根据ID删除岗位"""
        stmt = delete(SysPost).where(SysPost.post_id == post_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def count_users(self, post_id: int) -> int:
        """统计岗位关联的用户数量"""
        stmt = (
            select(func.count())
            .select_from(SysUserPost)
            .where(SysUserPost.post_id == post_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
