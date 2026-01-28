from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from module_admin.repository import ProjectTopologyRepository
from utils.common_util import CamelCaseUtil
from utils.transaction_manager import transactional


class ProjectTopologyService:
    """
    工程拓扑数据模块服务层
    """

    @classmethod
    @transactional()
    async def save_project_topology_services(
        cls, query_db: AsyncSession, topology: ProjectTopologyModel
    ) -> CrudResponseModel:
        """
        保存工程拓扑数据 service
        """
        topology_repo = ProjectTopologyRepository(query_db)
        await topology_repo.save_topology(
            project_id=topology.project_id,
            version_id=topology.version_id,
            topology_data=topology.topology_data,
            create_by=topology.create_by,
            update_by=topology.update_by
        )
        return CrudResponseModel(is_success=True, message='拓扑保存成功')

    @classmethod
    async def get_project_topology_services(
        cls, query_db: AsyncSession, project_id: int, version_id: int | None = None
    ):
        """
        获取工程拓扑数据 service
        """
        topology_repo = ProjectTopologyRepository(query_db)
        topo = await topology_repo.find_by_project_and_version(project_id, version_id)
        if topo:
            return CamelCaseUtil.transform_result(topo)
        return CamelCaseUtil.transform_result({})
