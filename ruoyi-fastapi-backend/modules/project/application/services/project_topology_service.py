from datetime import datetime
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.get_db import get_db
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from utils.common_util import CamelCaseUtil
from utils.transaction_manager import transactional
from ports import IProjectTopologyRepository


class ProjectTopologyService:
    """
    工程拓扑数据模块服务层
    """

    def __init__(self, topology_repo: IProjectTopologyRepository):
        self.query_db = getattr(topology_repo, 'db', None)
        self.topology_repo = topology_repo

    async def save_project_topology(
        self, topology: ProjectTopologyModel, operator: Optional[str] = None
    ) -> CrudResponseModel:
        return await self.save_project_topology_services(topology, operator=operator)

    async def get_project_topology(self, project_id: int, version_id: Optional[int] = None):
        return await self.get_project_topology_services(project_id, version_id)

    @transactional()
    async def save_project_topology_services(
        self,
        topology: ProjectTopologyModel,
        operator: Optional[str] = None,
    ) -> CrudResponseModel:
        """
        保存工程拓扑数据 service
        """
        now = datetime.now()
        effective_operator = operator or topology.update_by or topology.create_by or 'system'
        if not topology.create_by:
            topology.create_by = effective_operator
        if not topology.create_time:
            topology.create_time = now
        if not topology.update_by:
            topology.update_by = effective_operator
        if not topology.update_time:
            topology.update_time = now

        await self.topology_repo.save_topology(
            project_id=topology.project_id,
            version_id=topology.version_id,
            topology_data=topology.topology_data,
            create_by=topology.create_by,
            update_by=topology.update_by,
        )
        return CrudResponseModel(is_success=True, message='拓扑保存成功')

    async def get_project_topology_services(
        self, project_id: int, version_id: Optional[int] = None
    ):
        """
        获取工程拓扑数据 service
        """
        topo = await self.topology_repo.find_by_project_and_version(project_id, version_id)
        if topo:
            return CamelCaseUtil.transform_result(topo)
        return CamelCaseUtil.transform_result({})


def get_project_topology_service(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
) -> ProjectTopologyService:
    container = getattr(request.app.state, 'container', None)
    if container is None:
        raise RuntimeError('Application container is not initialized')
    return container.project_topology_service(query_db)
