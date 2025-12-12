from typing import List

from sqlalchemy import delete, desc, select, update
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
        使用子查询避免对大 JSON 字段排序导致 sort buffer 溢出
        """
        # 子查询：只查 topology_id（小字段），排序不涉及大 JSON
        id_query = select(SysProjectTopology.topology_id).where(
            SysProjectTopology.project_id == project_id
        )
        if version_id is not None:
            id_query = id_query.where(SysProjectTopology.version_id == version_id)
        id_query = id_query.order_by(desc(SysProjectTopology.update_time)).limit(1)

        id_result = await db.execute(id_query)
        topology_id = id_result.scalar()

        if topology_id is None:
            return None

        # 根据主键直接获取完整行，无需排序
        result = await db.execute(
            select(SysProjectTopology).where(SysProjectTopology.topology_id == topology_id)
        )
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
            # 清理同一工程+版本下的历史重复拓扑记录，仅保留最新一条
            cleanup_where = [
                SysProjectTopology.project_id == topology.project_id,
                SysProjectTopology.topology_id != existing.topology_id,
            ]
            if topology.version_id is None:
                cleanup_where.append(SysProjectTopology.version_id.is_(None))
            else:
                cleanup_where.append(SysProjectTopology.version_id == topology.version_id)
            await db.execute(delete(SysProjectTopology).where(*cleanup_where))
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
        # 兜底清理重复记录（并发写入等场景可能产生重复）
        cleanup_where = [
            SysProjectTopology.project_id == topology.project_id,
            SysProjectTopology.topology_id != db_topology.topology_id,
        ]
        if topology.version_id is None:
            cleanup_where.append(SysProjectTopology.version_id.is_(None))
        else:
            cleanup_where.append(SysProjectTopology.version_id == topology.version_id)
        await db.execute(delete(SysProjectTopology).where(*cleanup_where))
        return db_topology

    @classmethod
    async def get_topologies_by_version_ids(
        cls, db: AsyncSession, project_id: int, version_ids: List[int]
    ) -> List[SysProjectTopology]:
        """
        根据版本ID列表获取拓扑数据
        """
        if not version_ids:
            return []
        query = select(SysProjectTopology).where(
            SysProjectTopology.project_id == project_id,
            SysProjectTopology.version_id.in_(version_ids)
        )
        result = await db.execute(query)
        return result.scalars().all()
