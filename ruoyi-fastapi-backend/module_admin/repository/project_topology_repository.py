"""
项目拓扑 Repository
"""
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.project_topology_do import SysProjectTopology
from module_admin.repository.base_repository import BaseRepository


class ProjectTopologyRepository(BaseRepository[SysProjectTopology]):
    """项目拓扑 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysProjectTopology)
    
    async def find_by_project_and_version(
        self,
        project_id: int,
        version_id: Optional[int] = None
    ) -> Optional[SysProjectTopology]:
        """
        根据项目ID和版本ID获取拓扑数据
        使用子查询避免对大 JSON 字段排序
        """
        # 子查询获取最新的 topology_id
        id_query = select(SysProjectTopology.topology_id).where(
            SysProjectTopology.project_id == project_id
        )
        if version_id is not None:
            id_query = id_query.where(SysProjectTopology.version_id == version_id)
        id_query = id_query.order_by(desc(SysProjectTopology.update_time)).limit(1)
        
        id_result = await self.db.execute(id_query)
        topology_id = id_result.scalar()
        
        if topology_id is None:
            return None
        
        # 根据主键直接获取
        stmt = select(SysProjectTopology).where(SysProjectTopology.topology_id == topology_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def save_topology(
        self,
        project_id: int,
        topology_data: Any,
        version_id: Optional[int] = None,
        create_by: Optional[str] = None,
        update_by: Optional[str] = None
    ) -> SysProjectTopology:
        """
        保存拓扑数据（存在则更新，不存在则新增）
        """
        existing = await self.find_by_project_and_version(project_id, version_id)
        now = datetime.now()
        
        if existing:
            # 更新现有记录
            stmt = (
                update(SysProjectTopology)
                .where(SysProjectTopology.topology_id == existing.topology_id)
                .values(
                    topology_data=topology_data,
                    version_id=version_id,
                    update_by=update_by,
                    update_time=now
                )
            )
            await self.db.execute(stmt)
            await self.db.flush()
            
            # 清理重复记录
            await self._cleanup_duplicates(project_id, version_id, existing.topology_id)
            return existing
        
        # 新增记录
        db_topology = SysProjectTopology(
            project_id=project_id,
            version_id=version_id,
            topology_data=topology_data,
            create_by=create_by,
            create_time=now,
            update_by=update_by,
            update_time=now
        )
        self.db.add(db_topology)
        await self.db.flush()
        
        # 清理重复记录
        await self._cleanup_duplicates(project_id, version_id, db_topology.topology_id)
        return db_topology
    
    async def _cleanup_duplicates(
        self,
        project_id: int,
        version_id: Optional[int],
        keep_topology_id: int
    ):
        """清理重复的拓扑记录"""
        conditions = [
            SysProjectTopology.project_id == project_id,
            SysProjectTopology.topology_id != keep_topology_id
        ]
        if version_id is None:
            conditions.append(SysProjectTopology.version_id.is_(None))
        else:
            conditions.append(SysProjectTopology.version_id == version_id)
        
        stmt = delete(SysProjectTopology).where(*conditions)
        await self.db.execute(stmt)
    
    async def find_by_version_ids(
        self,
        project_id: int,
        version_ids: List[int]
    ) -> List[SysProjectTopology]:
        """根据版本ID列表获取拓扑数据"""
        if not version_ids:
            return []
        
        stmt = select(SysProjectTopology).where(
            SysProjectTopology.project_id == project_id,
            SysProjectTopology.version_id.in_(version_ids)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
