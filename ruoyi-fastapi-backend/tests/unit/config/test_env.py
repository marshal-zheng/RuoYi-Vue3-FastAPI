from __future__ import annotations

import pytest

from config.env import (
    DataBaseSettings,
    DataBaseWorkflowSettings,
    DevManagedDataHotReconcileSettings,
    get_database_workflow_status,
)


def test_database_workflow_status_defaults_to_dev_sync_in_development_mode() -> None:
    status = get_database_workflow_status(
        database_config=DataBaseSettings(
            db_type='mysql',
            db_host='127.0.0.1',
            db_port=3306,
            db_username='root',
            db_password='admin1234',
            db_database='ruoyi-fastapi',
        ),
        workflow_config=DataBaseWorkflowSettings(
            db_workflow_mode='development',
            db_dev_sync_engine='atlas',
        ),
    )

    assert status.workflow_mode == 'development'
    assert status.workflow_stage == 'development'
    assert status.startup_action == 'dev-sync'
    assert status.allowed_actions == ('status', 'dev-sync', 'finalize', 'verify')
    assert status.dev_sync_path == 'python scripts/db.py dev-sync'


def test_dev_managed_data_hot_reconcile_settings_defaults() -> None:
    settings = DevManagedDataHotReconcileSettings()

    assert settings.dev_managed_data_hot_reconcile_enabled is True
    assert settings.dev_managed_data_watch_interval_ms == 200
    assert settings.dev_managed_data_debounce_ms == 250
    assert settings.dev_managed_data_retry_backoff_ms == 1000
    assert settings.dev_managed_data_retry_max_backoff_ms == 30000
    assert settings.dev_managed_data_sse_heartbeat_seconds == 15
    assert settings.dev_managed_data_sse_replay_buffer_size == 1


def test_dev_managed_data_hot_reconcile_settings_support_legacy_dev_menu_sync_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DEV_MENU_SYNC', '0')

    settings = DevManagedDataHotReconcileSettings()

    assert settings.dev_managed_data_hot_reconcile_enabled is False
    assert settings.dev_menu_sync is False


def test_dev_managed_data_hot_reconcile_settings_prefer_new_env_over_legacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('DEV_MANAGED_DATA_HOT_RECONCILE_ENABLED', '1')
    monkeypatch.setenv('DEV_MENU_SYNC', '0')

    settings = DevManagedDataHotReconcileSettings()

    assert settings.dev_managed_data_hot_reconcile_enabled is True
