"""
协议 Repository
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.protocol_do import ProtocolDO
from module_admin.entity.do.enums import DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class ProtocolRepository(BaseRepository[ProtocolDO]):
    """协议 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, ProtocolDO)
    
    async def find_by_id(self, protocol_id: int) -> Optional[ProtocolDO]:
        """根据ID查找协议"""
        stmt = select(ProtocolDO).where(
            ProtocolDO.protocol_id == protocol_id,
            ProtocolDO.del_flag == DelFlagEnum.EXIST.value
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_name(self, protocol_name: str) -> Optional[ProtocolDO]:
        """根据名称查找协议"""
        stmt = select(ProtocolDO).where(
            ProtocolDO.protocol_name == protocol_name,
            ProtocolDO.del_flag == DelFlagEnum.EXIST.value
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self) -> List[ProtocolDO]:
        """获取所有有效协议"""
        stmt = (
            select(ProtocolDO)
            .where(ProtocolDO.del_flag == DelFlagEnum.EXIST.value)
            .order_by(desc(ProtocolDO.update_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        protocol_name: Optional[str] = None,
        protocol_type: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询协议"""
        conditions = [ProtocolDO.del_flag == DelFlagEnum.EXIST.value]
        
        if protocol_name:
            conditions.append(ProtocolDO.protocol_name.like(f'%{protocol_name}%'))
        if protocol_type:
            conditions.append(ProtocolDO.protocol_type == protocol_type)
        if begin_time and end_time:
            conditions.append(ProtocolDO.create_time.between(begin_time, end_time))
        
        query = (
            select(ProtocolDO)
            .where(*conditions)
            .order_by(desc(ProtocolDO.update_time))
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def soft_delete_batch(
        self,
        protocol_ids: List[int],
        update_by: str
    ) -> int:
        """批量软删除协议"""
        if not protocol_ids:
            return 0
        stmt = (
            update(ProtocolDO)
            .where(ProtocolDO.protocol_id.in_(protocol_ids))
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
