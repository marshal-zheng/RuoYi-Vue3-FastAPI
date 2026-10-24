from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exceptions.handle import handle_exception
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.api import dev_menu_sync_controller as controller_module
from modules.system.runtime import DevManagedDataHotReconcileRuntime, DevMenuEventBroker
from scripts.internal.db_workflow.managed_data_fast_reconcile_service import ManagedDataFastReconcileReport


def _build_admin_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['*:*:*'],
        roles=['admin'],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='admin',
        ),
    )


def _build_non_admin_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['system:menu:list'],
        roles=['common'],
        user=UserInfoModel(
            userId=2,
            userName='common',
            nickName='common',
        ),
    )


@pytest.fixture
def controller_context():
    app = FastAPI()
    handle_exception(app)
    app.state.dev_menu_sync_runtime = None
    app.state.dev_managed_data_hot_reconcile_runtime = None
    app.state.dev_menu_event_broker = DevMenuEventBroker(heartbeat_seconds=60, replay_buffer_size=1)
    app.state.dev_managed_data_hot_reconcile_event_broker = app.state.dev_menu_event_broker
    app.state.capability_gate_service = object()
    app.state.redis = object()
    app.include_router(controller_module.devMenuSyncController)

    async def override_get_current_user() -> CurrentUserModel:
        return _build_admin_user()

    async def override_get_db():
        yield None

    app.dependency_overrides[controller_module.get_current_user] = override_get_current_user
    app.dependency_overrides[controller_module.get_db] = override_get_db

    with TestClient(app) as client:
        yield client, app, controller_module


def _enable_dev_menu_api(controller_module, monkeypatch) -> None:
    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'development', raising=False)
    monkeypatch.setattr(
        controller_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        True,
        raising=False,
    )


def test_signature_endpoint_returns_signature_when_enabled(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    get_signature = AsyncMock(return_value='signature-demo')
    monkeypatch.setattr(controller_module.DevMenuSignatureService, 'get_user_signature', get_signature)

    response = client.get('/dev/menu/signature')
    assert response.status_code == 200
    payload = response.json()
    assert 'data' not in payload
    assert payload['signature'] == 'signature-demo'
    assert payload['lastSyncStatus'] in {'idle', 'ok', 'failed'}
    get_signature.assert_awaited()


def test_status_endpoint_returns_runtime_diagnostics(controller_context, monkeypatch, tmp_path):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    runtime = DevManagedDataHotReconcileRuntime(
        modules_root=tmp_path,
        watch_interval_ms=25,
        debounce_ms=15,
        retry_backoff_ms=1500,
        retry_max_backoff_ms=9000,
    )
    runtime.state.last_seen_snapshot_checksum = 'snapshot-seen'
    runtime.state.last_applied_snapshot_checksum = 'snapshot-applied'
    runtime.state.last_applied_compiled_checksum = 'compiled-applied'
    runtime.state.pending_snapshot_checksum = 'snapshot-pending'
    runtime.state.retry_count = 2
    runtime.state.last_sync_success = False
    runtime.state.last_sync_at = datetime(2026, 4, 7, 8, 0, 0, tzinfo=UTC)
    runtime.state.last_trigger = 'file_change'
    runtime.state.last_error = 'postcondition verification failed'
    runtime.state.last_event_id = 4
    runtime.state.next_retry_at = datetime(2026, 4, 7, 8, 0, 5, tzinfo=UTC)
    app.state.dev_menu_sync_runtime = runtime
    app.state.dev_managed_data_hot_reconcile_runtime = runtime

    response = client.get('/dev/menu/status')
    assert response.status_code == 200
    payload = response.json()
    assert 'data' not in payload
    assert payload['enabled'] is True
    assert payload['modulesRoot'] == str(tmp_path)
    assert payload['modulesRootExists'] is True
    assert payload['manifestCount'] == 0
    assert payload['watchIntervalMs'] == 200
    assert payload['debounceMs'] == 250
    assert payload['retryBackoffMs'] == 1000
    assert payload['retryMaxBackoffMs'] == 30000
    assert payload['lastSeenSnapshotChecksum'] == 'snapshot-seen'
    assert payload['lastAppliedSnapshotChecksum'] == 'snapshot-applied'
    assert payload['lastAppliedCompiledChecksum'] == 'compiled-applied'
    assert payload['pendingSnapshotChecksum'] == 'snapshot-pending'
    assert payload['retryCount'] == 2
    assert payload['lastSyncStatus'] == 'failed'
    assert payload['lastTrigger'] == 'file_change'
    assert payload['lastError'] == 'postcondition verification failed'
    assert payload['lastEventId'] == 4
    assert payload['nextRetryAt'] == '2026-04-07T08:00:05+00:00'


def test_signature_endpoint_returns_404_when_unavailable(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'prod', raising=False)
    monkeypatch.setattr(controller_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'development', raising=False)
    monkeypatch.setattr(
        controller_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        True,
        raising=False,
    )

    response = client.get('/dev/menu/signature')
    assert response.status_code == 404


def test_signature_endpoint_returns_404_when_switch_disabled(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'development', raising=False)
    monkeypatch.setattr(
        controller_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        False,
        raising=False,
    )

    response = client.get('/dev/menu/signature')
    assert response.status_code == 404


def test_signature_endpoint_returns_404_when_workflow_not_development(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'migration', raising=False)
    monkeypatch.setattr(
        controller_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        True,
        raising=False,
    )

    response = client.get('/dev/menu/signature')
    assert response.status_code == 404


def test_events_endpoint_streams_ready_event_and_headers(controller_context, monkeypatch):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)

    async def _mock_stream(*, user_id: int | None, last_event_id: int | None = None):
        assert user_id == 1
        assert last_event_id is None
        yield b'event: ready\ndata: {"connectedAt":"2026-04-06T12:00:00+00:00"}\n\n'

    monkeypatch.setattr(app.state.dev_menu_event_broker, 'stream', _mock_stream)
    response = client.get('/dev/menu/events')

    lines = response.text.splitlines()
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['connection'] == 'keep-alive'
    assert response.headers['x-accel-buffering'] == 'no'
    assert 'event: ready' in lines
    ready_data = next(line for line in lines if line.startswith('data: '))
    assert 'connectedAt' in ready_data


def test_events_endpoint_returns_404_when_broker_missing(controller_context, monkeypatch):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    app.state.dev_menu_event_broker = None
    app.state.dev_managed_data_hot_reconcile_event_broker = None

    response = client.get('/dev/menu/events')
    assert response.status_code == 404


def test_sync_endpoint_requires_admin(controller_context, monkeypatch):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)

    async def override_get_current_user() -> CurrentUserModel:
        return _build_non_admin_user()

    app.dependency_overrides[controller_module.get_current_user] = override_get_current_user
    response = client.post('/dev/menu/sync', json={'dryRun': True})
    assert response.status_code == 403


def test_sync_endpoint_supports_dry_run(controller_context, monkeypatch):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    reconcile = AsyncMock(
        return_value=ManagedDataFastReconcileReport(
            success=True,
            trigger='manual',
            compiled_checksum='checksum-dry-run',
            duration_ms=12,
            affected_objects=('sys_menu:dashboard', 'sys_role_menu:admin:dashboard'),
            applied_operations=2,
            skipped_operations=1,
            postcondition_status='skipped',
            dry_run=True,
            state_changed=False,
            synced_at=datetime(2026, 4, 6, 12, 0, 0, tzinfo=UTC),
        )
    )
    monkeypatch.setattr(controller_module.ManagedDataFastReconcileService, 'reconcile', reconcile)

    response = client.post('/dev/menu/sync', json={'dryRun': True, 'trigger': 'manual'})
    assert response.status_code == 200
    payload = response.json()
    assert 'data' not in payload
    assert payload['dryRun'] is True
    assert payload['compiledChecksum'] == 'checksum-dry-run'
    assert payload['affectedObjectsCount'] == 2
    assert payload['appliedOperations'] == 2
    assert payload['changedDomains'] == ['menus', 'role_grants']
    assert payload['menuReloadRequired'] is True
    assert payload['postconditionStatus'] == 'skipped'
    assert hasattr(app.state, 'capability_gate_service') is True
    reconcile.assert_awaited_once_with(trigger='manual', dry_run=True, previous_compiled_checksum=None)


def test_sync_endpoint_publishes_menu_changed_and_updates_runtime(controller_context, monkeypatch, tmp_path):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path, watch_interval_ms=10, debounce_ms=0)
    runtime.state.last_applied_compiled_checksum = 'checksum-old'
    app.state.dev_menu_sync_runtime = runtime
    app.state.dev_managed_data_hot_reconcile_runtime = runtime

    reconcile = AsyncMock(
        return_value=ManagedDataFastReconcileReport(
            success=True,
            trigger='manual',
            compiled_checksum='checksum-new',
            duration_ms=18,
            affected_objects=('sys_menu:dashboard',),
            applied_operations=1,
            skipped_operations=0,
            metadata_updated_objects=1,
            metadata_deactivated_objects=0,
            postcondition_status='clean',
            dry_run=False,
            state_changed=True,
            synced_at=datetime(2026, 4, 6, 12, 0, 1, tzinfo=UTC),
        )
    )
    monkeypatch.setattr(controller_module.ManagedDataFastReconcileService, 'reconcile', reconcile)

    response = client.post('/dev/menu/sync', json={'dryRun': False, 'trigger': 'manual'})
    assert response.status_code == 200
    payload = response.json()
    assert 'data' not in payload
    assert payload['stateChanged'] is True
    assert payload['compiledChecksum'] == 'checksum-new'
    assert payload['changedDomains'] == ['menus']
    assert payload['menuReloadRequired'] is True
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_applied_compiled_checksum == 'checksum-new'
    assert runtime.state.last_event_id == 1
    assert app.state.dev_menu_event_broker.last_event_id == 1
    assert len(app.state.dev_menu_event_broker.replay_events) == 1
    assert hasattr(app.state, 'capability_gate_service') is False
    replay_event = app.state.dev_menu_event_broker.replay_events[0]
    assert replay_event.event == 'menu_changed'
    assert replay_event.data['compiledChecksum'] == 'checksum-new'
    reconcile.assert_awaited_once_with(
        trigger='manual',
        dry_run=False,
        previous_compiled_checksum='checksum-old',
    )


def test_sync_endpoint_does_not_publish_menu_changed_for_config_only_mutation(
    controller_context, monkeypatch, tmp_path
):
    client, app, controller_module = controller_context

    _enable_dev_menu_api(controller_module, monkeypatch)
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path, watch_interval_ms=10, debounce_ms=0)
    runtime.state.last_applied_compiled_checksum = 'checksum-old'
    app.state.dev_menu_sync_runtime = runtime
    app.state.dev_managed_data_hot_reconcile_runtime = runtime

    reconcile = AsyncMock(
        return_value=ManagedDataFastReconcileReport(
            success=True,
            trigger='manual',
            compiled_checksum='checksum-config-only',
            duration_ms=9,
            affected_objects=('sys_config:device.default.timeout',),
            applied_operations=1,
            skipped_operations=0,
            metadata_updated_objects=1,
            metadata_deactivated_objects=0,
            postcondition_status='clean',
            dry_run=False,
            state_changed=True,
            synced_at=datetime(2026, 4, 6, 12, 0, 2, tzinfo=UTC),
        )
    )
    monkeypatch.setattr(controller_module.ManagedDataFastReconcileService, 'reconcile', reconcile)

    response = client.post('/dev/menu/sync', json={'dryRun': False, 'trigger': 'manual'})
    assert response.status_code == 200
    payload = response.json()
    assert 'data' not in payload
    assert payload['stateChanged'] is True
    assert payload['changedDomains'] == ['configs']
    assert payload['menuReloadRequired'] is False
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_applied_compiled_checksum == 'checksum-config-only'
    assert runtime.state.last_event_id == 0
    assert app.state.dev_menu_event_broker.last_event_id == 0
    assert len(app.state.dev_menu_event_broker.replay_events) == 0
    assert hasattr(app.state, 'capability_gate_service') is False
    reconcile.assert_awaited_once_with(
        trigger='manual',
        dry_run=False,
        previous_compiled_checksum='checksum-old',
    )
