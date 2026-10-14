"""All status sources publish the same WebSocket wire keys without touching external stores."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from module_admin.service.simulation_service import SimulationService


@pytest.fixture
def service(monkeypatch):
    instance = SimulationService()
    monkeypatch.setattr(instance, '_active_engines', {})
    monkeypatch.setattr(instance, '_session_configs', {'saved-session': {'project_id': 7}})
    monkeypatch.setattr(instance, '_persist_runtime_snapshot', AsyncMock())
    return instance


def assert_wire_status(status, session_id, expected_status):
    assert status['sessionId'] == session_id
    assert status['status'] == expected_status
    assert isinstance(status['messageCount'], int)
    assert isinstance(status['alarmCount'], int)
    assert 'session_id' not in status
    assert 'message_count' not in status
    assert 'alarm_count' not in status


def test_cached_stopped_status_has_the_same_wire_keys_as_active_engine(service):
    status = service.get_session_status_services('saved-session')
    assert_wire_status(status, 'saved-session', 'stopped')
    assert status['enginePresent'] is False


async def test_shared_stopped_status_preserves_the_wire_contract(service):
    status = await service.get_shared_session_status_services('saved-session')
    assert_wire_status(status, 'saved-session', 'stopped')
    service._persist_runtime_snapshot.assert_awaited_once()


def test_missing_session_status_is_a_complete_not_found_frame(service):
    status = service.get_session_status_services('missing-session')
    assert_wire_status(status, 'missing-session', 'not_found')
    assert status['messageCount'] == 0
    assert status['alarmCount'] == 0


def test_active_engine_status_keeps_its_real_counters(service):
    service._active_engines['running-session'] = SimpleNamespace(
        get_status=lambda: {
            'session_id': 'running-session',
            'status': 'running',
            'message_count': 13,
            'alarm_count': 2,
        }
    )
    status = service.get_session_status_services('running-session')
    assert_wire_status(status, 'running-session', 'running')
    assert status['messageCount'] == 13
    assert status['alarmCount'] == 2
