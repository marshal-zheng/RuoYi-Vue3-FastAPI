"""Unit tests for ProjectService core utilities."""

from datetime import datetime as real_datetime
from unittest.mock import AsyncMock

import pytest

from modules.project.application.services.project_service import ProjectService


class FixedDatetime:
    @classmethod
    def now(cls) -> real_datetime:
        return real_datetime(2026, 2, 10, 9, 30, 0)


class TestProjectServiceCodeGeneration:
    @pytest.mark.asyncio
    async def test_generate_project_code_starts_from_one(self, monkeypatch):
        mock_get_max = AsyncMock(return_value=None)
        project_repo = type('FakeProjectRepo', (), {'get_max_project_code_by_prefix': mock_get_max})()
        service = ProjectService(
            project_repo=project_repo,
            version_repo=AsyncMock(),
            topology_repo=AsyncMock(),
            device_repo=AsyncMock(),
            interface_repo=AsyncMock(),
            query_db=AsyncMock(),
        )
        monkeypatch.setattr('modules.project.application.services.project_service.datetime', FixedDatetime)

        code = await service._generate_project_code()

        assert code == 'PRJ202602100001'
        mock_get_max.assert_awaited_once()
        assert mock_get_max.await_args.args[0] == 'PRJ20260210'

    @pytest.mark.asyncio
    async def test_generate_project_code_increments_existing(self, monkeypatch):
        mock_get_max = AsyncMock(return_value='PRJ202602100009')
        project_repo = type('FakeProjectRepo', (), {'get_max_project_code_by_prefix': mock_get_max})()
        service = ProjectService(
            project_repo=project_repo,
            version_repo=AsyncMock(),
            topology_repo=AsyncMock(),
            device_repo=AsyncMock(),
            interface_repo=AsyncMock(),
            query_db=AsyncMock(),
        )
        monkeypatch.setattr('modules.project.application.services.project_service.datetime', FixedDatetime)

        code = await service._generate_project_code()

        assert code == 'PRJ202602100010'
        mock_get_max.assert_awaited_once()
        assert mock_get_max.await_args.args[0] == 'PRJ20260210'


class TestProjectServiceTopologyMapping:
    def test_extract_device_ids_from_topology(self):
        topology = {
            'graph': {
                'cells': [
                    {'data': {'deviceId': 1}},
                    {'data': {'deviceId': '2'}},
                ]
            },
            'nodes': [
                {'data': {'deviceId': 2}},
                {'data': {'deviceId': '3'}},
            ],
        }

        device_ids = ProjectService._extract_device_ids_from_topology(topology)

        assert device_ids == {1, 2, 3}

    def test_extract_device_ids_from_empty_topology(self):
        assert ProjectService._extract_device_ids_from_topology({}) == set()
        assert ProjectService._extract_device_ids_from_topology(None) == set()

    def test_update_topology_device_ids_updates_copy_only(self):
        source = {
            'graph': {'cells': [{'data': {'deviceId': 10}}, {'data': {'deviceId': 20}}]},
            'nodes': [{'data': {'deviceId': 10}}, {'data': {'deviceId': 99}}],
        }
        mapping = {10: 1000, 20: 2000}

        updated = ProjectService._update_topology_device_ids(source, mapping)

        assert updated['graph']['cells'][0]['data']['deviceId'] == 1000
        assert updated['graph']['cells'][1]['data']['deviceId'] == 2000
        assert updated['nodes'][0]['data']['deviceId'] == 1000
        assert updated['nodes'][1]['data']['deviceId'] == 99
        # source should remain unchanged
        assert source['graph']['cells'][0]['data']['deviceId'] == 10
        assert source['nodes'][0]['data']['deviceId'] == 10


class TestProjectServiceFilename:
    def test_safe_filename_replaces_unsafe_chars(self):
        raw = '  demo / test:*?"<>| project  '
        safe = ProjectService._safe_filename(raw)
        assert safe == 'demo_test_project'

    def test_safe_filename_falls_back_when_empty(self):
        assert ProjectService._safe_filename('   ') == 'project'
        assert ProjectService._safe_filename('') == 'project'
