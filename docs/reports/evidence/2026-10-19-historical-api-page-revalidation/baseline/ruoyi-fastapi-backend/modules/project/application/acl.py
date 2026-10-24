"""ACL mappers that isolate project context read models."""

from __future__ import annotations

import json
from typing import Any

from modules.project.domain.topology_view import ProjectTopologyView


def map_project_topology_record(record: Any) -> ProjectTopologyView:
    """Convert repository record to project topology read model."""
    return map_project_topology_record_with_fallback(record)


def map_project_topology_record_with_fallback(
    record: Any,
    *,
    fallback_project_id: int | None = None,
    fallback_version_id: int | None = None,
) -> ProjectTopologyView:
    """Convert repository record to project topology read model with optional fallback ids."""
    if record is None:
        raise ValueError('project topology record is required')

    raw_topology = getattr(record, 'topology_data', None)
    if raw_topology is None:
        raise ValueError('project topology data is missing')

    project_id = getattr(record, 'project_id', None)
    if project_id is None:
        project_id = fallback_project_id
    if project_id is None:
        raise ValueError('project_id is missing in project topology record')

    normalized_topology = normalize_topology_payload(raw_topology)
    version_id = getattr(record, 'version_id', None)
    if version_id is None:
        version_id = fallback_version_id
    return ProjectTopologyView(
        project_id=int(project_id),
        version_id=int(version_id) if version_id is not None else None,
        topology_data=normalized_topology,
    )


def normalize_topology_payload(payload: Any) -> dict[str, Any]:
    """Normalize topology payload into a dictionary."""
    parsed_payload = payload
    if isinstance(payload, str):
        parsed_payload = json.loads(payload)
    if not isinstance(parsed_payload, dict):
        raise ValueError('topology_data must be a JSON object')
    return parsed_payload
