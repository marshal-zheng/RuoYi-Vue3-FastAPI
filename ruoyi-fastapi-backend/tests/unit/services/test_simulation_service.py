"""Simulation service unit tests for the repository-based architecture."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from exceptions.exception import ValidationException
from module_admin.entity.do.enums import SimulationStatusEnum
from module_admin.entity.vo.simulation_vo import CreateSimulationSessionModel
from module_admin.service.simulation_service import SimulationService


@pytest.fixture(autouse=True)
def _reset_simulation_service_state():
    """Avoid cross-test contamination from SimulationService class-level caches."""
    SimulationService._active_engines.clear()
    SimulationService._session_configs.clear()
    SimulationService._snapshot_write_at.clear()
    SimulationService._snapshot_status.clear()
    yield
    SimulationService._active_engines.clear()
    SimulationService._session_configs.clear()
    SimulationService._snapshot_write_at.clear()
    SimulationService._snapshot_status.clear()


def test_validate_topology_reports_errors_for_empty_topology():
    service = SimulationService()
    result = service.validate_topology_services({"nodes": [], "edges": []})

    assert result["is_valid"] is False
    assert result["error_count"] >= 2
    assert isinstance(result["errors"], list)


def test_validate_topology_accepts_minimal_valid_topology():
    service = SimulationService()
    topology = {
        "nodes": [
            {"id": "n1", "data": {"ports": [{"id": "p1", "type": "CAN"}]}},
            {"id": "n2", "data": {"ports": [{"id": "p2", "type": "CAN"}]}}
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "sourcePort": "p1",
                "targetPort": "p2",
            }
        ],
    }

    result = service.validate_topology_services(topology)

    assert result["is_valid"] is True
    assert result["error_count"] == 0


def test_simulation_service_contract_methods_exist():
    service = SimulationService()
    assert callable(service.create_session_services)
    assert callable(service.start_session_services)
    assert callable(service.stop_session_services)
    assert callable(service.get_session_status_services)


@pytest.mark.asyncio
async def test_create_session_uses_message_kwarg_for_snapshot(monkeypatch):
    service = SimulationService()

    class StubTopologyRepo:
        def __init__(self, _db):
            pass

        async def find_by_project_and_version(self, _project_id, _version_id):
            return SimpleNamespace(topology_data={"nodes": [], "edges": []})

    class StubSessionRepo:
        def __init__(self, _db):
            pass

        async def add(self, session_obj):
            return session_obj

    class StubEngine:
        def __init__(self, _session_id, _topology_data, injection_strategy="random", injection_params=None):
            self.status = SimulationStatusEnum.CREATED.value
            self._injection_strategy = injection_strategy
            self._injection_params = injection_params or {}

    persist_snapshot = AsyncMock()
    monkeypatch.setattr("module_admin.service.simulation_service.ProjectTopologyRepository", StubTopologyRepo)
    monkeypatch.setattr("module_admin.service.simulation_service.SimulationSessionRepository", StubSessionRepo)
    monkeypatch.setattr("module_admin.service.simulation_service.SimulationEngine", StubEngine)
    monkeypatch.setattr(service, "_persist_runtime_snapshot", persist_snapshot)

    query_db = AsyncMock()
    create_request = CreateSimulationSessionModel(project_id=1, version_id=1, create_by="tester")
    result = await service.create_session_services(query_db, create_request)

    assert result["status"] == SimulationStatusEnum.CREATED.value
    kwargs = persist_snapshot.await_args.kwargs
    assert kwargs.get("message") == "仿真会话创建成功"
    assert "user_message" not in kwargs


@pytest.mark.asyncio
async def test_start_session_uses_message_kwarg_for_snapshot(monkeypatch):
    service = SimulationService()

    class StubSessionRepo:
        def __init__(self, _db):
            pass

        async def update_status(self, _session_id, _status, _end_time):
            return None

    class StubEngine:
        def __init__(self):
            self.status = SimulationStatusEnum.CREATED.value
            self.start = AsyncMock()

    persist_snapshot = AsyncMock()
    monkeypatch.setattr("module_admin.service.simulation_service.SimulationSessionRepository", StubSessionRepo)
    monkeypatch.setattr(service, "_persist_runtime_snapshot", persist_snapshot)

    engine = StubEngine()
    SimulationService._active_engines["sid-start"] = engine
    SimulationService._session_configs["sid-start"] = {"project_id": 1, "version_id": 1}

    await service.start_session_services(AsyncMock(), "sid-start")

    kwargs = persist_snapshot.await_args.kwargs
    assert kwargs.get("message") == "仿真已启动"
    assert "user_message" not in kwargs


@pytest.mark.asyncio
async def test_stop_session_uses_message_kwarg_for_snapshot(monkeypatch):
    service = SimulationService()

    class StubSessionRepo:
        def __init__(self, _db):
            pass

        async def update_status(self, _session_id, _status, _end_time):
            return None

    class StubEngine:
        def __init__(self):
            self.status = SimulationStatusEnum.RUNNING.value
            self.stop = AsyncMock()

    persist_snapshot = AsyncMock()
    persist_data = AsyncMock()
    monkeypatch.setattr("module_admin.service.simulation_service.SimulationSessionRepository", StubSessionRepo)
    monkeypatch.setattr(service, "_persist_runtime_snapshot", persist_snapshot)
    monkeypatch.setattr(service, "_persist_simulation_data", persist_data)

    engine = StubEngine()
    SimulationService._active_engines["sid-stop"] = engine
    SimulationService._session_configs["sid-stop"] = {"project_id": 1, "version_id": 1}

    await service.stop_session_services(AsyncMock(), "sid-stop")

    kwargs = persist_snapshot.await_args.kwargs
    assert kwargs.get("message") == "仿真已停止"
    assert "user_message" not in kwargs


@pytest.mark.asyncio
async def test_pause_session_uses_message_kwarg_for_snapshot(monkeypatch):
    service = SimulationService()

    class StubSessionRepo:
        def __init__(self, _db):
            pass

        async def update_status(self, _session_id, _status, _end_time):
            return None

    class StubEngine:
        def __init__(self):
            self.status = SimulationStatusEnum.RUNNING.value
            self.pause = AsyncMock()

    persist_snapshot = AsyncMock()
    monkeypatch.setattr("module_admin.service.simulation_service.SimulationSessionRepository", StubSessionRepo)
    monkeypatch.setattr(service, "_persist_runtime_snapshot", persist_snapshot)

    engine = StubEngine()
    SimulationService._active_engines["sid-pause"] = engine
    SimulationService._session_configs["sid-pause"] = {"project_id": 1, "version_id": 1}

    await service.pause_session_services(AsyncMock(), "sid-pause")

    kwargs = persist_snapshot.await_args.kwargs
    assert kwargs.get("message") == "仿真已暂停"
    assert "user_message" not in kwargs


def test_build_fault_injection_request_with_payload_and_explicit_session():
    service = SimulationService()
    request = service.build_fault_injection_request_services(
        session_id="session-path",
        payload={
            "sessionId": "session-body",
            "faultType": "packet_loss",
            "targetId": "edge-1",
            "params": {"lossRate": 0.2},
        },
        require_session_id=False,
    )

    assert request["session_id"] == "session-path"
    assert request["fault_type"] == "packet_loss"
    assert request["target_id"] == "edge-1"
    assert request["params"] == {"lossRate": 0.2}


def test_build_fault_injection_request_uses_payload_as_params_when_missing_params():
    service = SimulationService()
    request = service.build_fault_injection_request_services(
        payload={
            "session_id": "session-1",
            "fault_type": "delay",
            "target_id": "edge-2",
            "delayMs": 200,
        },
        require_session_id=True,
    )

    assert request["session_id"] == "session-1"
    assert request["fault_type"] == "delay"
    assert request["target_id"] == "edge-2"
    assert request["params"]["delayMs"] == 200


def test_build_fault_injection_request_rejects_missing_fault_fields():
    service = SimulationService()
    with pytest.raises(ValidationException):
        service.build_fault_injection_request_services(
            session_id="session-1",
            payload={"sessionId": "session-1"},
            require_session_id=False,
        )


def test_build_fault_injection_request_rejects_missing_session_for_upsert():
    service = SimulationService()
    with pytest.raises(ValidationException):
        service.build_fault_injection_request_services(
            payload={"faultType": "disconnect", "targetId": "node-1"},
            require_session_id=True,
        )


def test_require_session_id_returns_stripped_value():
    service = SimulationService()
    assert service.require_session_id("  session-1  ") == "session-1"


def test_require_session_id_raises_validation_for_empty_value():
    service = SimulationService()
    with pytest.raises(ValidationException):
        service.require_session_id("   ")


def test_apply_fault_injection_delegates_request_parsing_and_injection(monkeypatch):
    service = SimulationService()
    calls = {}

    def _build_fault_injection_request(**kwargs):
        calls["build_kwargs"] = kwargs
        return {
            "session_id": "session-x",
            "fault_type": "packet_loss",
            "target_id": "edge-1",
            "params": {"lossRate": 0.2},
        }

    def _inject_fault(session_id: str, fault_type: str, target_id: str, params):
        calls["inject_args"] = {
            "session_id": session_id,
            "fault_type": fault_type,
            "target_id": target_id,
            "params": params,
        }
        return {"faultId": "f-1"}

    monkeypatch.setattr(service, "build_fault_injection_request", _build_fault_injection_request)
    monkeypatch.setattr(service, "inject_fault", _inject_fault)

    result = service.apply_fault_injection(
        session_id="session-path",
        fault_type="packet_loss",
        target_id="edge-1",
        payload={"lossRate": 0.2},
        require_session_id=False,
    )

    assert calls["build_kwargs"]["session_id"] == "session-path"
    assert calls["build_kwargs"]["require_session_id"] is False
    assert calls["inject_args"] == {
        "session_id": "session-x",
        "fault_type": "packet_loss",
        "target_id": "edge-1",
        "params": {"lossRate": 0.2},
    }
    assert result == {
        "session_id": "session-x",
        "fault_type": "packet_loss",
        "target_id": "edge-1",
        "result": {"faultId": "f-1"},
    }


def test_resolve_speed_input_defaults_to_one():
    service = SimulationService()
    assert service.resolve_speed_input(None) == 1.0


def test_resolve_speed_input_parses_numeric_strings():
    service = SimulationService()
    assert service.resolve_speed_input({"speed": "2.5"}) == pytest.approx(2.5)


def test_resolve_speed_input_rejects_invalid_value():
    service = SimulationService()
    with pytest.raises(ValidationException):
        service.resolve_speed_input({"speed": "invalid"})


def test_resolve_duration_input_prefers_explicit_and_normalizes_non_positive():
    service = SimulationService()
    assert service.resolve_duration_input(duration=15, payload={"duration": 30}) == pytest.approx(15.0)
    assert service.resolve_duration_input(duration=0) is None
    assert service.resolve_duration_input(duration=-5) is None
    assert service.resolve_duration_input(duration=None, payload={"duration": "20"}) == pytest.approx(20.0)


def test_compute_push_interval_respects_speed_bounds():
    fast_interval = SimulationService._compute_push_interval(speed=4.0)
    slow_interval = SimulationService._compute_push_interval(speed=0.5)
    out_of_range_fast = SimulationService._compute_push_interval(speed=100.0)
    out_of_range_slow = SimulationService._compute_push_interval(speed=0.01)

    assert fast_interval == pytest.approx(0.025)
    assert slow_interval == pytest.approx(0.2)
    assert out_of_range_fast == pytest.approx(0.025)
    assert out_of_range_slow == pytest.approx(0.2)


def test_compute_push_limits_clamps_messages_bandwidth_and_alarms():
    high = SimulationService._compute_push_limits(speed=4.0)
    low = SimulationService._compute_push_limits(speed=0.5)
    mid = SimulationService._compute_push_limits(speed=1.5)

    assert high["messages"] == 200
    assert high["bandwidth"] == 400
    assert high["alarms"] == 200
    assert low["messages"] == 50
    assert low["bandwidth"] == 100
    assert low["alarms"] == 50
    assert mid["messages"] == 75
    assert mid["bandwidth"] == 300
    assert mid["alarms"] == 150
    assert mid["animations"] == 20
    assert mid["faults"] == 50


def test_should_collect_from_engine_requires_owner_engine_and_non_stopped():
    assert SimulationService._should_collect_from_engine(True, True, SimulationStatusEnum.RUNNING.value) is True
    assert SimulationService._should_collect_from_engine(False, True, SimulationStatusEnum.RUNNING.value) is False
    assert SimulationService._should_collect_from_engine(True, False, SimulationStatusEnum.RUNNING.value) is False
    assert SimulationService._should_collect_from_engine(True, True, SimulationStatusEnum.STOPPED.value) is False


@pytest.mark.asyncio
async def test_stream_session_updates_caps_owner_events_before_shared_append(monkeypatch):
    service = SimulationService()
    limits = SimulationService._compute_push_limits(0.5)

    monkeypatch.setattr(
        SimulationService,
        "_compute_push_interval",
        staticmethod(lambda _speed, *_args, **_kwargs: 0.0),
    )
    monkeypatch.setattr(
        service,
        "get_shared_session_status",
        AsyncMock(
            return_value={
                "status": SimulationStatusEnum.RUNNING.value,
                "speed": 0.5,
                "enginePresent": True,
            }
        ),
    )
    monkeypatch.setattr(service, "claim_runtime_producer_owner", AsyncMock(return_value=True))
    monkeypatch.setattr(service, "release_runtime_producer_owner", AsyncMock())

    bandwidth_batches = [[{"id": i} for i in range(300)]]
    alarm_batches = [[{"id": i} for i in range(250)]]
    fault_batches = [([{"id": i} for i in range(120)], 120)]
    message_batches = [[{"id": i} for i in range(80)]]

    def _pop_batch(batches):
        return batches.pop(0) if batches else []

    monkeypatch.setattr(
        service,
        "get_new_messages",
        lambda _session_id, limit=20: _pop_batch(message_batches)[-limit:],
    )
    monkeypatch.setattr(service, "get_new_bandwidth", lambda _session_id: _pop_batch(bandwidth_batches))
    monkeypatch.setattr(service, "get_new_alarms", lambda _session_id: _pop_batch(alarm_batches))
    monkeypatch.setattr(
        service,
        "get_new_fault_events",
        lambda _session_id, offset=0: fault_batches.pop(0) if fault_batches else ([], offset),
    )

    append_runtime_events = AsyncMock()
    broadcast = AsyncMock()
    monkeypatch.setattr(service, "append_runtime_events", append_runtime_events)

    connection_states = [True, False]

    async def has_connections(_session_id: str) -> bool:
        return connection_states.pop(0)

    await service.stream_session_updates(
        "session-owner",
        has_connections=has_connections,
        broadcast=broadcast,
        worker_id="worker-a",
    )

    stream_payload_sizes = {call.args[1]: len(call.args[2]) for call in append_runtime_events.await_args_list}
    assert stream_payload_sizes["messages"] == limits["messages"]
    assert stream_payload_sizes["bandwidth"] == limits["bandwidth"]
    assert stream_payload_sizes["alarms"] == limits["alarms"]
    assert stream_payload_sizes["faults"] == limits["faults"]

    alarm_pushes = [call.args[1] for call in broadcast.await_args_list if call.args[1]["type"] == "alarms"]
    assert alarm_pushes
    assert len(alarm_pushes[0]["data"]) == limits["alarms"]


@pytest.mark.asyncio
async def test_stream_session_updates_reads_alarm_stream_with_alarm_limit(monkeypatch):
    service = SimulationService()
    limits = SimulationService._compute_push_limits(0.5)

    monkeypatch.setattr(
        service,
        "get_shared_session_status",
        AsyncMock(
            return_value={
                "status": SimulationStatusEnum.RUNNING.value,
                "speed": 0.5,
                "enginePresent": False,
            }
        ),
    )
    monkeypatch.setattr(service, "claim_runtime_producer_owner", AsyncMock(return_value=False))
    monkeypatch.setattr(service, "get_runtime_stream_size", AsyncMock(return_value=0))
    get_runtime_events_since = AsyncMock(side_effect=[([], 0), ([], 0), ([], 0), ([], 0)])
    monkeypatch.setattr(service, "get_runtime_events_since", get_runtime_events_since)

    connection_states = [True, False]

    async def has_connections(_session_id: str) -> bool:
        return connection_states.pop(0)

    await service.stream_session_updates(
        "session-shared",
        has_connections=has_connections,
        broadcast=AsyncMock(),
        worker_id="worker-b",
    )

    alarm_call = get_runtime_events_since.await_args_list[2]
    assert alarm_call.args[1] == "alarms"
    assert alarm_call.args[3] == limits["alarms"]


@pytest.mark.asyncio
async def test_read_messages_with_fallback_reads_shared_stream_when_realtime_empty(monkeypatch):
    service = SimulationService()
    monkeypatch.setattr(service, "get_realtime_messages", lambda _sid, _limit=100: [])
    get_runtime_latest_events = AsyncMock(return_value=[{"messageId": "m-1"}])
    monkeypatch.setattr(service, "get_runtime_latest_events", get_runtime_latest_events)

    result = await service.read_messages_with_fallback("session-1", 20)

    assert result == [{"messageId": "m-1"}]
    get_runtime_latest_events.assert_awaited_once_with("session-1", "messages", 20)


@pytest.mark.asyncio
async def test_read_bandwidth_with_fallback_filters_shared_data_by_port(monkeypatch):
    service = SimulationService()
    monkeypatch.setattr(service, "get_realtime_bandwidth", lambda _sid, _port_id=None: [])
    get_runtime_latest_events = AsyncMock(
        return_value=[
            {"portId": "p-1", "value": 10},
            {"port_id": "p-2", "value": 20},
            {"portId": "p-2", "value": 30},
        ]
    )
    monkeypatch.setattr(service, "get_runtime_latest_events", get_runtime_latest_events)

    result = await service.read_bandwidth_with_fallback("session-1", port_id="p-2", limit=400)

    assert result == [{"port_id": "p-2", "value": 20}, {"portId": "p-2", "value": 30}]
    get_runtime_latest_events.assert_awaited_once_with("session-1", "bandwidth", 400)


@pytest.mark.asyncio
async def test_read_alarms_with_fallback_prefers_realtime(monkeypatch):
    service = SimulationService()
    monkeypatch.setattr(service, "get_realtime_alarms", lambda _sid: [{"alarmId": "a-1"}])
    get_runtime_latest_events = AsyncMock(return_value=[{"alarmId": "shared-a"}])
    monkeypatch.setattr(service, "get_runtime_latest_events", get_runtime_latest_events)

    result = await service.read_alarms_with_fallback("session-1", 200)

    assert result == [{"alarmId": "a-1"}]
    get_runtime_latest_events.assert_not_awaited()
