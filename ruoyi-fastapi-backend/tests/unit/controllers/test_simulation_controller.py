"""Simulation controller contract tests for orchestration boundaries."""

import json
from types import SimpleNamespace

import pytest

from module_admin.controller import simulation_controller


def _route_map(router):
    mapped = set()
    for route in router.routes:
        methods = getattr(route, 'methods', None)
        if methods:
            mapped.add((route.path, tuple(sorted(m for m in methods if m not in {'HEAD', 'OPTIONS'}))))
            continue
        mapped.add((route.path, ('WEBSOCKET',)))
    return mapped


class _FakeRequest:
    def __init__(self, path: str, payload: dict | None = None):
        self.headers = {
            'Authorization': '',
            'User-Agent': 'pytest',
            'X-Forwarded-For': '127.0.0.1',
            'Content-Type': 'application/json',
        }
        self.method = 'POST'
        self.url = SimpleNamespace(path=path)
        self.path_params = {}
        self._payload = payload or {}

    async def body(self):
        return json.dumps(self._payload).encode('utf-8')

    async def form(self):
        return {}


def test_simulation_router_registers_core_session_endpoints():
    routes = _route_map(simulation_controller.simulationController)
    assert ('/simulation/sessions', ('POST',)) in routes
    assert ('/simulation/sessions/{session_id}/start', ('POST',)) in routes
    assert ('/simulation/sessions/{session_id}/stop', ('POST',)) in routes
    assert ('/simulation/sessions/{session_id}/ws', ('WEBSOCKET',)) in routes


@pytest.mark.asyncio
async def test_push_simulation_data_delegates_to_service(monkeypatch):
    calls = {}

    class _FakeSimulationService:
        async def stream_session_updates(self, session_id: str, **kwargs):
            calls['session_id'] = session_id
            calls['kwargs'] = kwargs

    await simulation_controller.push_simulation_data('session-test', _FakeSimulationService())

    assert calls['session_id'] == 'session-test'
    assert calls['kwargs']['worker_id'] == simulation_controller.SESSION_PRODUCER_WORKER_ID
    assert callable(calls['kwargs']['has_connections'])
    assert callable(calls['kwargs']['broadcast'])


@pytest.mark.asyncio
async def test_get_simulation_messages_delegates_data_resolution_to_service():
    calls = {}

    class _FakeSimulationService:
        async def read_messages_with_fallback(self, session_id: str, limit: int):
            calls['session_id'] = session_id
            calls['limit'] = limit
            return [{'messageId': 'm-1'}]

    response = await simulation_controller.get_simulation_messages(
        request=None,
        session_id='session-1',
        limit=50,
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {'session_id': 'session-1', 'limit': 50}
    assert payload == {'items': [{'messageId': 'm-1'}]}


@pytest.mark.asyncio
async def test_get_simulation_bandwidth_delegates_data_resolution_to_service():
    calls = {}

    class _FakeSimulationService:
        async def read_bandwidth_with_fallback(self, session_id: str, port_id: str | None = None, limit: int = 400):
            calls['session_id'] = session_id
            calls['port_id'] = port_id
            calls['limit'] = limit
            return [{'portId': 'p-1', 'value': 1}]

    response = await simulation_controller.get_simulation_bandwidth(
        request=None,
        session_id='session-1',
        port_id='p-1',
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {'session_id': 'session-1', 'port_id': 'p-1', 'limit': 400}
    assert payload == {'items': [{'portId': 'p-1', 'value': 1}]}


@pytest.mark.asyncio
async def test_get_simulation_alarms_delegates_data_resolution_to_service():
    calls = {}

    class _FakeSimulationService:
        async def read_alarms_with_fallback(self, session_id: str, limit: int = 200):
            calls['session_id'] = session_id
            calls['limit'] = limit
            return [{'alarmId': 'a-1'}]

    response = await simulation_controller.get_simulation_alarms(
        request=None,
        session_id='session-1',
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {'session_id': 'session-1', 'limit': 200}
    assert payload == {'items': [{'alarmId': 'a-1'}]}


@pytest.mark.asyncio
async def test_set_simulation_speed_delegates_speed_resolution_to_service():
    calls = {}

    class _FakeSimulationService:
        def resolve_speed_input(self, payload: dict):
            calls['resolved_from_payload'] = payload
            return 2.5

        async def set_speed(self, session_id: str, speed: float):
            calls['set_speed_args'] = {'session_id': session_id, 'speed': speed}

            class _Result:
                def model_dump(self):
                    return {'isSuccess': True, 'message': 'ok'}

            return _Result()

    response = await simulation_controller.set_simulation_speed(
        request=None,
        session_id='session-1',
        body={'speed': '2.5'},
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {
        'resolved_from_payload': {'speed': '2.5'},
        'set_speed_args': {'session_id': 'session-1', 'speed': 2.5},
    }
    assert payload == {'isSuccess': True, 'message': 'ok'}


@pytest.mark.asyncio
async def test_set_simulation_duration_delegates_duration_resolution_to_service():
    calls = {}

    class _FakeSimulationService:
        def resolve_duration_input(self, *, duration=None, payload=None):
            calls['resolved_from_input'] = {'duration': duration, 'payload': payload}
            return 45.0

        async def set_duration(self, session_id: str, duration):
            calls['set_duration_args'] = {'session_id': session_id, 'duration': duration}

            class _Result:
                def model_dump(self):
                    return {'isSuccess': True, 'message': 'ok'}

            return _Result()

    response = await simulation_controller.set_simulation_duration(
        request=None,
        session_id='session-1',
        duration=30.0,
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {
        'resolved_from_input': {'duration': 30.0, 'payload': None},
        'set_duration_args': {'session_id': 'session-1', 'duration': 45.0},
    }
    assert payload == {'isSuccess': True, 'message': 'ok'}


@pytest.mark.asyncio
async def test_inject_fault_delegates_decision_to_service():
    calls = {}

    class _FakeSimulationService:
        def apply_fault_injection(self, **kwargs):
            calls['kwargs'] = kwargs
            return {
                'session_id': 'session-1',
                'fault_type': 'packet_loss',
                'target_id': 'edge-1',
                'result': {'faultId': 'f-1'},
            }

    response = await simulation_controller.inject_fault(
        request=_FakeRequest(
            '/simulation/sessions/session-1/faults',
            payload={'lossRate': 0.2},
        ),
        session_id='session-1',
        fault_type='packet_loss',
        target_id='edge-1',
        payload={'lossRate': 0.2},
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls['kwargs']['session_id'] == 'session-1'
    assert calls['kwargs']['require_session_id'] is False
    assert payload == {'faultId': 'f-1'}


@pytest.mark.asyncio
async def test_upsert_fault_delegates_decision_to_service():
    calls = {}

    class _FakeSimulationService:
        def apply_fault_injection(self, **kwargs):
            calls['kwargs'] = kwargs
            return {
                'session_id': 'session-upsert',
                'fault_type': 'delay',
                'target_id': 'edge-9',
                'result': {'faultId': 'f-9'},
            }

    response = await simulation_controller.upsert_fault(
        request=None,
        payload={'sessionId': 'session-upsert', 'faultType': 'delay', 'targetId': 'edge-9'},
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls['kwargs']['require_session_id'] is True
    assert payload == {'faultId': 'f-9'}


@pytest.mark.asyncio
async def test_query_faults_delegates_session_validation_to_service():
    calls = {}

    class _FakeSimulationService:
        def require_session_id(self, session_id: str):
            calls['validated_session'] = session_id
            return 'session-normalized'

        def list_faults(self, session_id: str):
            calls['list_faults_session'] = session_id
            return [{'faultId': 'f-1'}]

    response = await simulation_controller.query_faults(
        session_id='session-raw',
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {
        'validated_session': 'session-raw',
        'list_faults_session': 'session-normalized',
    }
    assert payload == {'items': [{'faultId': 'f-1'}]}


@pytest.mark.asyncio
async def test_delete_fault_delegates_session_validation_to_service():
    calls = {}

    class _FakeSimulationService:
        def require_session_id(self, session_id: str):
            calls['validated_session'] = session_id
            return 'session-normalized'

        def clear_fault(self, session_id: str, fault_id: str):
            calls['clear_fault_args'] = {'session_id': session_id, 'fault_id': fault_id}

            class _Result:
                def model_dump(self):
                    return {'isSuccess': True, 'message': 'ok'}

            return _Result()

    response = await simulation_controller.delete_fault(
        fault_id='fault-1',
        session_id='session-raw',
        simulation_service=_FakeSimulationService(),
    )

    payload = json.loads(response.body)
    assert calls == {
        'validated_session': 'session-raw',
        'clear_fault_args': {'session_id': 'session-normalized', 'fault_id': 'fault-1'},
    }
    assert payload == {'isSuccess': True, 'message': 'ok'}
