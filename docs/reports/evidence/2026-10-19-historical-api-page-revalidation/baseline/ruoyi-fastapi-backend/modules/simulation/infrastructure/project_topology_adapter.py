"""Simulation context adapters for cross-context project topology reads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.simulation.ports import ISimulationProjectTopologyPort

if TYPE_CHECKING:
    from modules.project.domain.topology_view import ProjectTopologyView
    from modules.project.ports import IProjectTopologyReadPort


class SimulationProjectTopologyAdapter(ISimulationProjectTopologyPort):
    """Bridge simulation context to project context read port."""

    def __init__(self, project_topology_reader: IProjectTopologyReadPort):
        self._project_topology_reader = project_topology_reader

    async def load_topology_for_simulation(
        self,
        project_id: int,
        version_id: int | None = None,
    ) -> ProjectTopologyView | None:
        return await self._project_topology_reader.get_project_topology(project_id=project_id, version_id=version_id)
