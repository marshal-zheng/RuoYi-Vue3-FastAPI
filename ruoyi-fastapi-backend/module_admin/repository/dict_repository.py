"""
字典 Repository
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.dict_do import SysDictType, SysDictData
from module_admin.entity.do.enums import StatusEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil
from utils.time_format_util import list_format_datetime


class DictTypeRepository(BaseRepository[SysDictType]):
    """字典类型 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysDictType)
    
    async def find_by_id(self, dict_id: int) -> Optional[SysDictType]:
        """根据ID查找字典类型"""
        stmt = select(SysDictType).where(SysDictType.dict_id == dict_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_type(self, dict_type: str) -> Optional[SysDictType]:
        """根据字典类型查找"""
        stmt = select(SysDictType).where(SysDictType.dict_type == dict_type)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_type_or_name(
        self,
        dict_type: Optional[str] = None,
        dict_name: Optional[str] = None
    ) -> Optional[SysDictType]:
        """根据类型或名称查找"""
        conditions = []
        if dict_type:
            conditions.append(SysDictType.dict_type == dict_type)
        if dict_name:
            conditions.append(SysDictType.dict_name == dict_name)
        
        stmt = select(SysDictType).where(*conditions) if conditions else select(SysDictType)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all(self) -> List[dict]:
        """获取所有字典类型"""
        stmt = select(SysDictType)
        result = await self.db.execute(stmt)
        return list_format_datetime(result.scalars().all())
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        dict_name: Optional[str] = None,
        dict_type: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询字典类型"""
        conditions = []
        if dict_name:
            conditions.append(SysDictType.dict_name.like(f'%{dict_name}%'))
        if dict_type:
            conditions.append(SysDictType.dict_type.like(f'%{dict_type}%'))
        if status:
            conditions.append(SysDictType.status == status)
        if begin_time and end_time:
            conditions.append(
                SysDictType.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        query = (
            select(SysDictType)
            .where(*conditions) if conditions else select(SysDictType)
        ).order_by(SysDictType.dict_id).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, dict_id: int) -> int:
        """根据ID删除字典类型"""
        stmt = delete(SysDictType).where(SysDictType.dict_id == dict_id)
        result = await self.db.execute(stmt)
        return result.rowcount


class DictDataRepository(BaseRepository[SysDictData]):
    """字典数据 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysDictData)
    
    async def find_by_code(self, dict_code: int) -> Optional[SysDictData]:
        """根据字典编码查找"""
        stmt = select(SysDictData).where(SysDictData.dict_code == dict_code)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_type_and_label(
        self,
        dict_type: str,
        dict_label: str,
        dict_value: Optional[str] = None
    ) -> Optional[SysDictData]:
        """根据类型、标签、值查找"""
        conditions = [
            SysDictData.dict_type == dict_type,
            SysDictData.dict_label == dict_label
        ]
        if dict_value:
            conditions.append(SysDictData.dict_value == dict_value)
        
        stmt = select(SysDictData).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_type(self, dict_type: str) -> List[SysDictData]:
        """根据字典类型查找所有数据"""
        stmt = (
            select(SysDictData)
            .select_from(SysDictType)
            .where(
                SysDictType.dict_type == dict_type,
                SysDictType.status == StatusEnum.NORMAL.value
            )
            .join(
                SysDictData,
                and_(
                    SysDictType.dict_type == SysDictData.dict_type,
                    SysDictData.status == StatusEnum.NORMAL.value
                ),
                isouter=True
            )
            .order_by(SysDictData.dict_sort)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        dict_type: Optional[str] = None,
        dict_label: Optional[str] = None,
        status: Optional[str] = None
    ):
        """分页查询字典数据"""
        conditions = []
        if dict_type:
            conditions.append(SysDictData.dict_type == dict_type)
        if dict_label:
            conditions.append(SysDictData.dict_label.like(f'%{dict_label}%'))
        if status:
            conditions.append(SysDictData.status == status)
        
        query = (
            select(SysDictData)
            .where(*conditions) if conditions else select(SysDictData)
        ).order_by(SysDictData.dict_sort).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_code(self, dict_code: int) -> int:
        """根据编码删除字典数据"""
        stmt = delete(SysDictData).where(SysDictData.dict_code == dict_code)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def count_by_type(self, dict_type: str) -> int:
        """统计字典类型下的数据数量"""
        stmt = (
            select(func.count())
            .select_from(SysDictData)
            .where(SysDictData.dict_type == dict_type)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
