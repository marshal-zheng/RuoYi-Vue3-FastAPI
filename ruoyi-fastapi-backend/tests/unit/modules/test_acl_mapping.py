from __future__ import annotations

import json

import pytest

from modules.project.application.acl import (
    map_project_topology_record,
    map_project_topology_record_with_fallback,
    normalize_topology_payload,
)
from modules.project.domain.topology_view import ProjectTopologyView
from modules.simulation.application.acl import to_simulation_topology


class _TopologyRecord:
    def __init__(self, project_id: int | None, version_id: int | None, topology_data):
        self.project_id = project_id
        self.version_id = version_id
        self.topology_data = topology_data


def test_map_project_topology_record_from_dict_payload() -> None:
    record = _TopologyRecord(project_id=101, version_id=2, topology_data={'nodes': [{'id': 'a'}], 'links': []})

    view = map_project_topology_record(record)

    assert isinstance(view, ProjectTopologyView)
    assert view.project_id == 101
    assert view.version_id == 2
    assert view.topology_data['nodes'][0]['id'] == 'a'


def test_map_project_topology_record_from_json_string() -> None:
    payload = {'nodes': [{'id': 'n-1'}], 'links': [{'source': 'n-1', 'target': 'n-2'}]}
    record = _TopologyRecord(project_id=9, version_id=None, topology_data=json.dumps(payload))

    view = map_project_topology_record(record)

    assert view.version_id is None
    assert view.topology_data == payload


def test_map_project_topology_record_with_fallback_ids() -> None:
    record = _TopologyRecord(project_id=None, version_id=None, topology_data={'nodes': [], 'links': []})

    view = map_project_topology_record_with_fallback(
        record,
        fallback_project_id=11,
        fallback_version_id=5,
    )

    assert view.project_id == 11
    assert view.version_id == 5


def test_normalize_topology_payload_rejects_non_object_json() -> None:
    with pytest.raises(ValueError, match='JSON object'):
        normalize_topology_payload('[1,2,3]')


def test_to_simulation_topology_returns_deep_copy() -> None:
    source = ProjectTopologyView(
        project_id=1,
        version_id=1,
        topology_data={'nodes': [{'id': 'x'}], 'links': []},
    )

    mapped = to_simulation_topology(source)
    mapped['nodes'][0]['id'] = 'mutated'

    assert source.topology_data['nodes'][0]['id'] == 'x'
    assert mapped['nodes'][0]['id'] == 'mutated'
