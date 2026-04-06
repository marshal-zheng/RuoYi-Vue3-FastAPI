from __future__ import annotations

from config.env import DataBaseSettings, DataBaseWorkflowSettings, get_database_workflow_status


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
