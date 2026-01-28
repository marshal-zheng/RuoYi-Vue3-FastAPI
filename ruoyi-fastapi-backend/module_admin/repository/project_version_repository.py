"""
项目版本 Repository
"""
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.project_version_do import SysProjectVersion
from module_admin.entity.do.enums import DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil
from utils.db_filters import not_deleted


class ProjectVersionRepository(BaseRepository[SysProjectVersion]):
    """项目版本 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysProjectVersion)
    
    async def find_by_id(self, version_id: int) -> Optional[SysProjectVersion]:
        """根据ID查找版本"""
        stmt = select(SysProjectVersion).where(
            SysProjectVersion.version_id == version_id,
            not_deleted(SysProjectVersion.del_flag)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_project(self, project_id: int) -> List[SysProjectVersion]:
        """根据项目ID查找所有版本"""
        stmt = (
            select(SysProjectVersion)
            .where(
                SysProjectVersion.project_id == project_id,
                not_deleted(SysProjectVersion.del_flag)
            )
            .order_by(SysProjectVersion.create_time)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        project_id: Optional[int] = None,
        version_name: Optional[str] = None,
        version_number: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """分页查询版本"""
        conditions = [not_deleted(SysProjectVersion.del_flag)]
        
        if project_id:
            conditions.append(SysProjectVersion.project_id == project_id)
        if version_name:
            conditions.append(SysProjectVersion.version_name.like(f'%{version_name}%'))
        if version_number:
            conditions.append(SysProjectVersion.version_number.like(f'%{version_number}%'))
        if begin_time and end_time:
            conditions.append(SysProjectVersion.create_time.between(begin_time, end_time))
        
        query = (
            select(SysProjectVersion)
            .where(*conditions)
            .order_by(desc(SysProjectVersion.create_time))
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def check_version_number_unique(
        self,
        project_id: int,
        version_number: str,
        exclude_version_id: Optional[int] = None
    ) -> bool:
        """检查版本号是否唯一"""
        conditions = [
            SysProjectVersion.project_id == project_id,
            SysProjectVersion.version_number == version_number,
            not_deleted(SysProjectVersion.del_flag)
        ]
        if exclude_version_id:
            conditions.append(SysProjectVersion.version_id != exclude_version_id)
        
        stmt = select(SysProjectVersion).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first() is None
    
    async def count_by_projects(self, project_ids: List[int]) -> Dict[int, int]:
        """统计项目版本数量"""
        if not project_ids:
            return {}
        
        stmt = (
            select(
                SysProjectVersion.project_id,
                func.count(SysProjectVersion.version_id).label('version_count')
            )
            .where(
                SysProjectVersion.project_id.in_(project_ids),
                not_deleted(SysProjectVersion.del_flag)
            )
            .group_by(SysProjectVersion.project_id)
        )
        result = await self.db.execute(stmt)
        return {row.project_id: row.version_count for row in result.all()}
    
    async def find_locked_by_projects(self, project_ids: List[int]) -> Dict[int, List[SysProjectVersion]]:
        """获取项目下的固化版本"""
        if not project_ids:
            return {}
        
        stmt = select(SysProjectVersion).where(
            SysProjectVersion.project_id.in_(project_ids),
            not_deleted(SysProjectVersion.del_flag),
            SysProjectVersion.is_locked == '1'
        )
        result = await self.db.execute(stmt)
        locked_versions = result.scalars().all()
        
        locked_map = {}
        for version in locked_versions:
            locked_map.setdefault(version.project_id, []).append(version)
        return locked_map
    
    async def lock_version(
        self,
        version_id: int,
        is_locked: str,
        update_by: str,
        locked_by: Optional[str] = None,
        locked_time: Optional[datetime] = None
    ) -> bool:
        """固化/解除固化版本"""
        update_data = {
            'is_locked': is_locked,
            'update_by': update_by,
            'update_time': datetime.now()
        }
        
        if is_locked == '1':
            update_data['locked_by'] = locked_by
            update_data['locked_time'] = locked_time
        else:
            update_data['locked_by'] = None
            update_data['locked_time'] = None
        
        stmt = (
            update(SysProjectVersion)
            .where(SysProjectVersion.version_id == version_id)
            .values(**update_data)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
    
    async def unlock_by_project(self, project_id: int, operator: Optional[str] = None) -> int:
        """批量解除项目下的固化版本"""
        stmt = (
            update(SysProjectVersion)
            .where(
                SysProjectVersion.project_id == project_id,
                not_deleted(SysProjectVersion.del_flag),
                SysProjectVersion.is_locked == '1'
            )
            .values(
                is_locked='0',
                locked_by=None,
                locked_time=None,
                update_by=operator,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def soft_delete_batch(
        self,
        version_ids: List[int],
        update_by: str
    ) -> int:
        """批量软删除版本"""
        if not version_ids:
            return 0
        stmt = (
            update(SysProjectVersion)
            .where(SysProjectVersion.version_id.in_(version_ids))
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
