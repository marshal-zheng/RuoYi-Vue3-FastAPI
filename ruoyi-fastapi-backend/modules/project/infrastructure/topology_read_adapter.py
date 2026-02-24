"""Project context read-port adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.project.application.acl import map_project_topology_record_with_fallback
from modules.project.ports import IProjectTopologyReadPort

if TYPE_CHECKING:
    from modules.project.domain.topology_view import ProjectTopologyView
    from ports import IProjectTopologyRepository


class ProjectTopologyReadAdapter(IProjectTopologyReadPort):
    """Adapt legacy repository output into project context read model."""

    def __init__(self, topology_repository: IProjectTopologyRepository):
        self._topology_repository = topology_repository

    async def get_project_topology(
        self,
        project_id: int,
        version_id: int | None = None,
    ) -> ProjectTopologyView | None:
        topology_record = await self._topology_repository.find_by_project_and_version(project_id, version_id)
        if topology_record is None:
            return None
        return map_project_topology_record_with_fallback(
            topology_record,
            fallback_project_id=project_id,
            fallback_version_id=version_id,
        )
