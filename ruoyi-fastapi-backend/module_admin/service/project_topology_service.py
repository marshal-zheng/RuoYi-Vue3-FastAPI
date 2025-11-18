from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.project_topology_dao import ProjectTopologyDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from utils.common_util import CamelCaseUtil


class ProjectTopologyService:
    """
    工程拓扑数据模块服务层
    """

    @classmethod
    async def save_project_topology_services(
        cls, query_db: AsyncSession, topology: ProjectTopologyModel
    ) -> CrudResponseModel:
        """
        保存工程拓扑数据 service
        """
        await ProjectTopologyDao.save_project_topology_dao(query_db, topology)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='拓扑保存成功')

    @classmethod
    async def get_project_topology_services(
        cls, query_db: AsyncSession, project_id: int, version_id: int | None = None
    ):
        """
        获取工程拓扑数据 service
        """
        topo = await ProjectTopologyDao.get_topology_by_project_and_version(
            query_db, project_id, version_id
        )
        if topo:
            return CamelCaseUtil.transform_result(topo)
        return CamelCaseUtil.transform_result({})
