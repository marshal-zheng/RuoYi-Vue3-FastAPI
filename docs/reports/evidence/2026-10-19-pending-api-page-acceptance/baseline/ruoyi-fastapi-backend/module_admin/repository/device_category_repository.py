"""
设备分类 Repository
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.device_category_do import DeviceCategoryDO
from module_admin.entity.do.enums import StatusEnum
from module_admin.repository.base_repository import BaseRepository


class DeviceCategoryRepository(BaseRepository[DeviceCategoryDO]):
    """设备分类 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, DeviceCategoryDO)
    
    async def find_by_id(self, category_id: int) -> Optional[DeviceCategoryDO]:
        """根据ID查找分类"""
        stmt = select(DeviceCategoryDO).where(
            DeviceCategoryDO.device_category_id == category_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_name(self, name: str) -> Optional[DeviceCategoryDO]:
        """根据名称查找分类"""
        stmt = select(DeviceCategoryDO).where(DeviceCategoryDO.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_all_active(self) -> List[DeviceCategoryDO]:
        """获取所有有效分类"""
        stmt = (
            select(DeviceCategoryDO)
            .where(DeviceCategoryDO.status == StatusEnum.NORMAL.value)
            .order_by(DeviceCategoryDO.name)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Tuple[List[DeviceCategoryDO], int]:
        """分页查询分类"""
        conditions = []
        if name:
            conditions.append(DeviceCategoryDO.name.like(f'%{name}%'))
        if status:
            conditions.append(DeviceCategoryDO.status == status)
        if begin_time:
            conditions.append(DeviceCategoryDO.create_time >= begin_time)
        if end_time:
            conditions.append(DeviceCategoryDO.create_time <= end_time)
        
        # 查询总数
        count_stmt = select(func.count()).select_from(DeviceCategoryDO)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # 查询数据
        stmt = select(DeviceCategoryDO)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = (
            stmt.order_by(DeviceCategoryDO.create_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.db.execute(stmt)
        categories = result.scalars().all()
        
        return categories, total
    
    async def delete_by_ids(self, category_ids: List[int]) -> int:
        """批量删除分类"""
        if not category_ids:
            return 0
        stmt = delete(DeviceCategoryDO).where(
            DeviceCategoryDO.device_category_id.in_(category_ids)
        )
        result = await self.db.execute(stmt)
        return result.rowcount
