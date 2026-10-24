"""ACL mappers for simulation context."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.project.domain.topology_view import ProjectTopologyView


def to_simulation_topology(view: ProjectTopologyView) -> dict[str, Any]:
    """Convert project topology view into simulation-owned topology payload."""
    # Return a deep copy so simulation cannot mutate project context data by reference.
    return deepcopy(view.topology_data)
