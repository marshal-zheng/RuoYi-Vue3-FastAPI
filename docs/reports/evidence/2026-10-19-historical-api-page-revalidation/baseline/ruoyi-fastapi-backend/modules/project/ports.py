"""Project context ports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from modules.project.domain.topology_view import ProjectTopologyView


@runtime_checkable
class IProjectTopologyReadPort(Protocol):
    """Read-only project topology contract exposed to other contexts."""

    async def get_project_topology(
        self,
        project_id: int,
        version_id: int | None = None,
    ) -> ProjectTopologyView | None:
        """Return normalized topology view for the given project/version."""
