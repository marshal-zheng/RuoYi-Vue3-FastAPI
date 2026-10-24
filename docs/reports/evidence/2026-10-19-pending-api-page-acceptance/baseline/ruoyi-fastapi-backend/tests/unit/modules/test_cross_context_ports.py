from __future__ import annotations

import pytest

from modules.project.domain.topology_view import ProjectTopologyView
from modules.project.infrastructure.topology_read_adapter import ProjectTopologyReadAdapter
from modules.simulation.infrastructure.project_topology_adapter import SimulationProjectTopologyAdapter


class _TopologyRepoStub:
    def __init__(self, record):
        self._record = record

    async def find_by_project_and_version(self, _project_id: int, _version_id: int | None = None):
        return self._record


class _ProjectReadPortStub:
    def __init__(self, view: ProjectTopologyView | None):
        self._view = view

    async def get_project_topology(self, project_id: int, version_id: int | None = None):
        assert project_id >= 0
        _ = version_id
        return self._view


class _TopologyRecord:
    def __init__(self, topology_data, project_id=None, version_id=None):
        self.topology_data = topology_data
        self.project_id = project_id
        self.version_id = version_id


@pytest.mark.asyncio
async def test_project_topology_read_adapter_maps_record() -> None:
    record = _TopologyRecord(topology_data={'nodes': [{'id': 'p1'}], 'links': []}, project_id=None, version_id=None)
    adapter = ProjectTopologyReadAdapter(_TopologyRepoStub(record))

    view = await adapter.get_project_topology(project_id=9, version_id=3)

    assert view is not None
    assert view.project_id == 9
    assert view.version_id == 3
    assert view.topology_data['nodes'][0]['id'] == 'p1'


@pytest.mark.asyncio
async def test_project_topology_read_adapter_returns_none_for_missing_record() -> None:
    adapter = ProjectTopologyReadAdapter(_TopologyRepoStub(None))

    view = await adapter.get_project_topology(project_id=1, version_id=None)

    assert view is None


@pytest.mark.asyncio
async def test_simulation_project_topology_adapter_delegates_to_project_port() -> None:
    view = ProjectTopologyView(project_id=2, version_id=1, topology_data={'nodes': [], 'links': []})
    adapter = SimulationProjectTopologyAdapter(_ProjectReadPortStub(view))

    result = await adapter.load_topology_for_simulation(project_id=2, version_id=1)

    assert result is view
