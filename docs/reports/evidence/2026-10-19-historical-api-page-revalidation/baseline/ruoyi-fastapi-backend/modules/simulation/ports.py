"""Simulation context ports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from modules.project.domain.topology_view import ProjectTopologyView


@runtime_checkable
class ISimulationProjectTopologyPort(Protocol):
    """Project-topology dependency required by simulation context."""

    async def load_topology_for_simulation(
        self,
        project_id: int,
        version_id: int | None = None,
    ) -> ProjectTopologyView | None:
        """Return project topology view used to bootstrap simulation engine."""
