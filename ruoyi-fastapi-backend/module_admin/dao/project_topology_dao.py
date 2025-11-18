from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.project_topology_do import SysProjectTopology
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel


class ProjectTopologyDao:
    """
    工程拓扑数据模块数据库操作层
    """

    @classmethod
    async def get_topology_by_project_and_version(
        cls, db: AsyncSession, project_id: int, version_id: int | None = None
    ):
        """
        根据工程ID和可选版本ID获取拓扑数据
        """
        query = select(SysProjectTopology).where(SysProjectTopology.project_id == project_id)

        if version_id is not None:
            query = query.where(SysProjectTopology.version_id == version_id)

        # 最新的拓扑记录优先
        query = query.order_by(desc(SysProjectTopology.update_time))

        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def save_project_topology_dao(
        cls, db: AsyncSession, topology: ProjectTopologyModel
    ) -> SysProjectTopology:
        """
        保存工程拓扑数据（存在则更新，不存在则新增）
        """
        existing = await cls.get_topology_by_project_and_version(
            db, topology.project_id, topology.version_id
        )

        if existing:
            await db.execute(
                update(SysProjectTopology)
                .where(SysProjectTopology.topology_id == existing.topology_id)
                .values(
                    topology_data=topology.topology_data,
                    version_id=topology.version_id,
                    update_by=topology.update_by,
                    update_time=topology.update_time,
                )
            )
            await db.flush()
            return existing

        db_topology = SysProjectTopology(
            project_id=topology.project_id,
            version_id=topology.version_id,
            topology_data=topology.topology_data,
            create_by=topology.create_by,
            create_time=topology.create_time,
            update_by=topology.update_by,
            update_time=topology.update_time,
        )
        db.add(db_topology)
        await db.flush()
        return db_topology
