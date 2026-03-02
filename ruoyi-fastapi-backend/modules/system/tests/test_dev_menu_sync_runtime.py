from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_dev_menu_sync_enabled_only_in_dev_with_switch(monkeypatch) -> None:
    from modules.system.runtime import dev_menu_sync_runtime as runtime_module

    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(runtime_module.DevMenuSyncConfig, 'dev_menu_sync', True, raising=False)
    assert runtime_module.is_dev_menu_sync_enabled() is True

    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'prod', raising=False)
    assert runtime_module.is_dev_menu_sync_enabled() is False

    monkeypatch.setattr(runtime_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(runtime_module.DevMenuSyncConfig, 'dev_menu_sync', False, raising=False)
    assert runtime_module.is_dev_menu_sync_enabled() is False


@pytest.mark.asyncio
async def test_runtime_startup_sync_runs_once(monkeypatch) -> None:
    from modules.system.runtime.dev_menu_sync_runtime import DevMenuSyncRuntime

    service = SimpleNamespace(sync_once=AsyncMock(return_value=SimpleNamespace(success=True)))
    runtime = DevMenuSyncRuntime(
        service_factory=lambda: service,
        watch_paths=(),
        poll_interval_seconds=0.01,
        debounce_seconds=0.0,
    )

    await runtime.start()
    await asyncio.sleep(0.02)
    await runtime.stop()

    service.sync_once.assert_any_await(trigger='startup', dry_run=False)


@pytest.mark.asyncio
async def test_runtime_file_change_triggers_sync(tmp_path) -> None:
    from modules.system.runtime.dev_menu_sync_runtime import DevMenuSyncRuntime

    registry_file = tmp_path / 'menus.registry.yaml'
    registry_file.write_text('version: \"1\"\\nmenus: []\\nrole_grants: []\\n', encoding='utf-8')

    service = SimpleNamespace(sync_once=AsyncMock(return_value=SimpleNamespace(success=True)))
    runtime = DevMenuSyncRuntime(
        service_factory=lambda: service,
        watch_paths=(registry_file,),
        poll_interval_seconds=0.01,
        debounce_seconds=0.0,
    )

    await runtime.start()
    await asyncio.sleep(0.03)
    registry_file.write_text('version: \"1\"\\nmenus:\\n  - menu_id: 1\\nrole_grants: []\\n', encoding='utf-8')
    await asyncio.sleep(0.05)
    await runtime.stop()

    called_triggers = [kwargs.get('trigger') for _args, kwargs in service.sync_once.await_args_list]
    assert 'startup' in called_triggers
    assert 'file_change' in called_triggers


@pytest.mark.asyncio
async def test_runtime_sync_failure_updates_state_and_can_recover() -> None:
    from modules.system.runtime.dev_menu_sync_runtime import DevMenuSyncRuntime

    query_db = SimpleNamespace(close=AsyncMock(return_value=None))
    service = SimpleNamespace(
        sync_once=AsyncMock(side_effect=[RuntimeError('boom'), SimpleNamespace(success=True)]),
        query_db=query_db,
    )
    runtime = DevMenuSyncRuntime(
        service_factory=lambda: service,
        watch_paths=(),
        poll_interval_seconds=1.0,
        debounce_seconds=0.0,
    )

    await runtime.trigger_sync('manual-failed')
    assert runtime.state.last_sync_success is False
    assert runtime.state.last_trigger == 'manual-failed'
    assert runtime.state.last_error is not None
    assert 'boom' in runtime.state.last_error

    await runtime.trigger_sync('manual-success')
    assert runtime.state.last_sync_success is True
    assert runtime.state.last_trigger == 'manual-success'
    assert runtime.state.last_error is None
