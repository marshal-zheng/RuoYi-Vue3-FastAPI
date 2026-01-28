"""
配置 Repository
提供系统配置相关的数据访问操作
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.config_do import SysConfig
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil


class ConfigRepository(BaseRepository[SysConfig]):
    """
    配置 Repository
    
    继承 BaseRepository 并扩展配置特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysConfig)
    
    async def find_by_id(self, config_id: int) -> Optional[SysConfig]:
        """根据ID查找配置"""
        stmt = select(SysConfig).where(SysConfig.config_id == config_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_key(self, config_key: str) -> Optional[SysConfig]:
        """根据配置键查找配置"""
        stmt = select(SysConfig).where(SysConfig.config_key == config_key)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_key_and_value(
        self,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None
    ) -> Optional[SysConfig]:
        """根据配置键和值查找配置"""
        conditions = []
        if config_key:
            conditions.append(SysConfig.config_key == config_key)
        if config_value:
            conditions.append(SysConfig.config_value == config_value)
        
        stmt = select(SysConfig).where(*conditions) if conditions else select(SysConfig)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        config_name: Optional[str] = None,
        config_key: Optional[str] = None,
        config_type: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """
        分页查询配置
        
        Args:
            page: 页码
            page_size: 每页数量
            config_name: 配置名称
            config_key: 配置键
            config_type: 配置类型
            begin_time: 开始时间
            end_time: 结束时间
        
        Returns:
            分页结果
        """
        conditions = []
        
        if config_name:
            conditions.append(SysConfig.config_name.like(f'%{config_name}%'))
        if config_key:
            conditions.append(SysConfig.config_key.like(f'%{config_key}%'))
        if config_type:
            conditions.append(SysConfig.config_type == config_type)
        if begin_time and end_time:
            conditions.append(
                SysConfig.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        query = (
            select(SysConfig)
            .where(*conditions) if conditions else select(SysConfig)
        ).order_by(SysConfig.config_id).distinct()
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def delete_by_id(self, config_id: int) -> int:
        """根据ID删除配置"""
        stmt = delete(SysConfig).where(SysConfig.config_id == config_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_ids(self, config_ids: List[int]) -> int:
        """批量删除配置"""
        if not config_ids:
            return 0
        stmt = delete(SysConfig).where(SysConfig.config_id.in_(config_ids))
        result = await self.db.execute(stmt)
        return result.rowcount
