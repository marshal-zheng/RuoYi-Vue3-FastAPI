"""Project context read model for topology snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectTopologyView:
    """Normalized topology snapshot shared via project context ports."""

    project_id: int
    version_id: int | None
    topology_data: dict[str, Any]
