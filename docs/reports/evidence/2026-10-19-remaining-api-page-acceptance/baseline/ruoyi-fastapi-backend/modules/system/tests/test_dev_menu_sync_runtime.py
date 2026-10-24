from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from modules.system.runtime import dev_menu_sync_runtime as runtime_module
from modules.system.runtime.dev_menu_sync_runtime import (
    DEFAULT_MANAGED_DATA_MODULES_DIR,
    DevManagedDataHotReconcileRuntime,
    HotReconcileCallbackResult,
    ManifestSnapshot,
    ManifestSnapshotEntry,
)
from scripts.internal.db_workflow.managed_data_declaration_loader import DEFAULT_MODULE_MANIFEST_ROOT


def test_dev_managed_data_hot_reconcile_enabled_only_in_dev_development_mode(monkeypatch) -> None:
    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(
        runtime_module.DataBaseWorkflowConfig,
        'db_workflow_mode',
        'development',
        raising=False,
    )
    monkeypatch.setattr(
        runtime_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        True,
        raising=False,
    )
    assert runtime_module.is_dev_managed_data_hot_reconcile_enabled() is True
    assert runtime_module.is_dev_menu_sync_enabled() is True

    monkeypatch.setattr(runtime_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'migration', raising=False)
    assert runtime_module.is_dev_managed_data_hot_reconcile_enabled() is False

    monkeypatch.setattr(runtime_module.DataBaseWorkflowConfig, 'db_workflow_mode', 'development', raising=False)
    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'prod', raising=False)
    assert runtime_module.is_dev_managed_data_hot_reconcile_enabled() is False

    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(
        runtime_module.DevManagedDataHotReconcileConfig,
        'dev_managed_data_hot_reconcile_enabled',
        False,
        raising=False,
    )
    assert runtime_module.is_dev_managed_data_hot_reconcile_enabled() is False


def test_manifest_snapshot_detects_added_modified_and_removed_module_files(tmp_path) -> None:
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path, watch_interval_ms=10, debounce_ms=0)

    initial_snapshot = runtime.capture_snapshot()
    first_manifest = tmp_path / 'alpha.module.yaml'
    first_manifest.write_text('module: alpha\n', encoding='utf-8')
    added_snapshot = runtime.capture_snapshot()
    added_diff = added_snapshot.diff(initial_snapshot)
    assert added_diff.added == ('alpha.module.yaml',)
    assert added_diff.modified == ()
    assert added_diff.removed == ()

    first_manifest.write_text('module: alpha\nmenus: []\n', encoding='utf-8')
    modified_snapshot = runtime.capture_snapshot()
    modified_diff = modified_snapshot.diff(added_snapshot)
    assert modified_diff.added == ()
    assert modified_diff.modified == ('alpha.module.yaml',)
    assert modified_diff.removed == ()

    first_manifest.unlink()
    removed_snapshot = runtime.capture_snapshot()
    removed_diff = removed_snapshot.diff(modified_snapshot)
    assert removed_diff.added == ()
    assert removed_diff.modified == ()
    assert removed_diff.removed == ('alpha.module.yaml',)


@pytest.mark.asyncio
async def test_runtime_run_serialized_prevents_parallel_execution(tmp_path) -> None:
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path, watch_interval_ms=10, debounce_ms=0)
    events: list[str] = []

    async def operation(name: str) -> str:
        events.append(f'start-{name}')
        await asyncio.sleep(0.01)
        events.append(f'end-{name}')
        return name

    results = await asyncio.gather(
        runtime.run_serialized(lambda: operation('a')),
        runtime.run_serialized(lambda: operation('b')),
    )

    assert results == ['a', 'b']
    assert events in (['start-a', 'end-a', 'start-b', 'end-b'], ['start-b', 'end-b', 'start-a', 'end-a'])


def test_runtime_state_records_failure_and_success(tmp_path) -> None:
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path, watch_interval_ms=10, debounce_ms=0)

    runtime.record_sync_failure(trigger='file_change', error='boom')
    assert runtime.state.last_sync_success is False
    assert runtime.state.last_trigger == 'file_change'
    assert runtime.state.last_error == 'boom'

    runtime.record_sync_success(trigger='manual', compiled_checksum='checksum-1', event_id=7)
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_trigger == 'manual'
    assert runtime.state.last_error is None
    assert runtime.state.last_applied_compiled_checksum == 'checksum-1'
    assert runtime.state.last_event_id == 7
    assert runtime.state.pending_snapshot_checksum is None
    assert runtime.state.retry_count == 0
    assert runtime.state.next_retry_at is None


@pytest.mark.asyncio
async def test_runtime_watch_loop_debounces_multiple_saves_into_single_reconcile(tmp_path) -> None:
    first_manifest = tmp_path / 'alpha.module.yaml'
    first_manifest.write_text('module: alpha\n', encoding='utf-8')
    callback_calls: list[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = []

    async def on_manifest_change(trigger, snapshot, diff):
        callback_calls.append((trigger, diff.added, diff.modified, diff.removed))
        return HotReconcileCallbackResult(
            success=True,
            compiled_checksum=f'compiled-{len(callback_calls)}',
            synced_at=datetime(2026, 4, 6, 12, 0, len(callback_calls), tzinfo=UTC),
        )

    runtime = DevManagedDataHotReconcileRuntime(
        modules_root=tmp_path,
        watch_interval_ms=10,
        debounce_ms=30,
        on_manifest_change=on_manifest_change,
    )

    await runtime.start()
    try:
        await asyncio.sleep(0.02)
        first_manifest.write_text('module: alpha\nmenus: []\n', encoding='utf-8')
        await asyncio.sleep(0.01)
        second_manifest = tmp_path / 'beta.module.yaml'
        second_manifest.write_text('module: beta\n', encoding='utf-8')

        await asyncio.sleep(0.12)
    finally:
        await runtime.stop()

    assert len(callback_calls) == 1
    trigger, added, modified, removed = callback_calls[0]
    assert trigger == 'file_change'
    assert added == ('beta.module.yaml',)
    assert modified == ('alpha.module.yaml',)
    assert removed == ()
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_applied_compiled_checksum == 'compiled-1'


@pytest.mark.asyncio
async def test_runtime_watch_loop_retries_failed_snapshot_until_success(tmp_path) -> None:
    first_manifest = tmp_path / 'alpha.module.yaml'
    first_manifest.write_text('module: alpha\n', encoding='utf-8')
    callback_calls: list[tuple[str, str]] = []

    async def on_manifest_change(trigger, snapshot, _diff):
        callback_calls.append((trigger, snapshot.checksum))
        if len(callback_calls) == 1:
            return HotReconcileCallbackResult(
                success=False,
                error='transient_failure',
                synced_at=datetime(2026, 4, 7, 8, 0, 0, tzinfo=UTC),
            )
        return HotReconcileCallbackResult(
            success=True,
            compiled_checksum='compiled-2',
            synced_at=datetime(2026, 4, 7, 8, 0, 1, tzinfo=UTC),
        )

    runtime = DevManagedDataHotReconcileRuntime(
        modules_root=tmp_path,
        watch_interval_ms=5,
        debounce_ms=0,
        retry_backoff_ms=10,
        retry_max_backoff_ms=10,
        on_manifest_change=on_manifest_change,
    )

    await runtime.start()
    try:
        await asyncio.sleep(0.02)
        first_manifest.write_text('module: alpha\nmenus: []\n', encoding='utf-8')
        await asyncio.sleep(0.08)
    finally:
        await runtime.stop()

    assert len(callback_calls) >= 2
    assert callback_calls[0][0] == 'file_change'
    assert callback_calls[1][0] == 'file_change'
    assert callback_calls[0][1] == callback_calls[1][1]
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_applied_snapshot_checksum == callback_calls[0][1]
    assert runtime.state.last_applied_compiled_checksum == 'compiled-2'
    assert runtime.state.pending_snapshot_checksum is None
    assert runtime.state.retry_count == 0
    assert runtime.state.next_retry_at is None


@pytest.mark.asyncio
async def test_runtime_watch_loop_skips_callback_when_change_reverts_during_debounce(tmp_path, monkeypatch) -> None:
    runtime = DevManagedDataHotReconcileRuntime(
        modules_root=tmp_path,
        watch_interval_ms=5,
        debounce_ms=20,
        on_manifest_change=lambda *_args: HotReconcileCallbackResult(success=True),
    )
    initial_snapshot = runtime.capture_snapshot()
    changed_snapshot = ManifestSnapshot(
        root=tmp_path,
        entries=(
            ManifestSnapshotEntry(
                relative_path='alpha.module.yaml',
                mtime_ns=1,
                size=16,
            ),
        ),
        checksum='changed-checksum',
        captured_at=initial_snapshot.captured_at,
    )
    async def on_manifest_change(*_args, **_kwargs):
        pytest.fail('callback should not be invoked when debounce settles back to original state')

    runtime._latest_snapshot = initial_snapshot
    runtime._on_manifest_change = on_manifest_change
    snapshots = [changed_snapshot, initial_snapshot]

    def fake_capture_snapshot():
        if snapshots:
            return snapshots.pop(0)
        return initial_snapshot

    monkeypatch.setattr(runtime, 'capture_snapshot', fake_capture_snapshot)

    watch_task = asyncio.create_task(runtime._watch_loop())
    try:
        await asyncio.sleep(0.04)
    finally:
        runtime._stop_event.set()
        await watch_task

    assert runtime.latest_snapshot == initial_snapshot
    assert runtime.state.last_seen_snapshot_checksum == initial_snapshot.checksum


def test_runtime_manifest_root_constant_is_aligned_with_declaration_loader() -> None:
    assert DEFAULT_MANAGED_DATA_MODULES_DIR == DEFAULT_MODULE_MANIFEST_ROOT


@pytest.mark.asyncio
async def test_runtime_start_fails_fast_when_manifest_root_is_missing(tmp_path) -> None:
    runtime = DevManagedDataHotReconcileRuntime(modules_root=tmp_path / 'missing-dir')
    with pytest.raises(RuntimeError, match='modules root does not exist'):
        await runtime.start()
