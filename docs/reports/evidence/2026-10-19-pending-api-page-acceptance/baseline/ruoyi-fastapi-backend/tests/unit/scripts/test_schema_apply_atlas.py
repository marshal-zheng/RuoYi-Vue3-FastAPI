from __future__ import annotations

import subprocess
import sys
import types

from config.env import DataBaseWorkflowStatus
from scripts.internal.db_workflow import schema_apply_atlas


def _status() -> DataBaseWorkflowStatus:
    return DataBaseWorkflowStatus(
        workflow_mode='development',
        db_dev_sync_engine='atlas',
        db_target='mysql://127.0.0.1:3306/ruoyi-fastapi',
        startup_action='dev-sync',
        deploy_path='python scripts/db.py deploy --revision head',
    )


def test_print_schema_ddl_uses_provider_script_mode(monkeypatch) -> None:
    provider_calls: dict[str, object] = {}

    def fake_print_ddl(dialect: str, model_classes: list[type[object]]) -> None:
        provider_calls['dialect'] = dialect
        provider_calls['model_classes'] = model_classes

    ddl_module = types.ModuleType('atlas_provider_sqlalchemy.ddl')
    ddl_module.print_ddl = fake_print_ddl
    provider_module = types.ModuleType('atlas_provider_sqlalchemy')
    provider_module.ddl = ddl_module

    class FakeModel:
        pass

    monkeypatch.setitem(sys.modules, 'atlas_provider_sqlalchemy', provider_module)
    monkeypatch.setitem(sys.modules, 'atlas_provider_sqlalchemy.ddl', ddl_module)
    monkeypatch.setattr(schema_apply_atlas, '_atlas_dialect', lambda: 'mysql')
    monkeypatch.setattr(schema_apply_atlas, '_collect_model_classes', lambda: [FakeModel])

    exit_code = schema_apply_atlas.main(['schema'])

    assert exit_code == 0
    assert provider_calls == {'dialect': 'mysql', 'model_classes': [FakeModel]}


def test_run_schema_apply_invokes_atlas_and_cleans_shadow_database(monkeypatch, capsys) -> None:
    cleanup_calls: list[str] = []
    command_calls: list[list[str]] = []

    def fake_require_atlas_binary(_env: dict[str, str]) -> str:
        return '/tmp/bin/atlas'

    monkeypatch.setattr(schema_apply_atlas, '_atlas_env', lambda: {'PATH': '/tmp/bin'})
    monkeypatch.setattr(schema_apply_atlas, '_require_atlas_binary', fake_require_atlas_binary)
    monkeypatch.setattr(
        schema_apply_atlas,
        '_prepare_shadow_database',
        lambda: (
            'ruoyi_fastapi_atlas_123',
            'mysql://root:admin1234@127.0.0.1:3306/ruoyi_fastapi_atlas_123?charset=utf8mb4',
        ),
    )
    monkeypatch.setattr(schema_apply_atlas, '_cleanup_shadow_database', lambda database: cleanup_calls.append(database))

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        command_calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='atlas apply ok\n', stderr='')

    monkeypatch.setattr(schema_apply_atlas.subprocess, 'run', fake_run)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_type', 'mysql', raising=False)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_host', '127.0.0.1', raising=False)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_port', 3306, raising=False)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_username', 'root', raising=False)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_password', 'admin1234', raising=False)
    monkeypatch.setattr(schema_apply_atlas.DataBaseConfig, 'db_database', 'ruoyi-fastapi', raising=False)

    result = schema_apply_atlas.run_schema_apply(
        project_root=schema_apply_atlas.PROJECT_ROOT,
        workflow_status=_status(),
        invoked_by_startup=False,
    )

    captured = capsys.readouterr()
    assert result == 'atlas_apply_success:atlas'
    assert cleanup_calls == ['ruoyi_fastapi_atlas_123']
    assert command_calls == [
        [
            '/tmp/bin/atlas',
            'schema',
            'apply',
            '--config',
            f'file://{schema_apply_atlas.PROJECT_ROOT / "atlas.hcl"}',
            '--env',
            'sqlalchemy',
            '--url',
            'mysql://root:admin1234@127.0.0.1:3306/ruoyi-fastapi?charset=utf8mb4',
            '--dev-url',
            'mysql://root:admin1234@127.0.0.1:3306/ruoyi_fastapi_atlas_123?charset=utf8mb4',
            '--auto-approve',
        ]
    ]
    assert 'atlas_target_url=mysql://root:admin1234@127.0.0.1:3306/ruoyi-fastapi?charset=utf8mb4' in captured.out
    assert 'atlas_risk_note=atlas will apply destructive schema changes directly when they are planned' in captured.out
    assert 'atlas apply ok' in captured.out


def test_run_schema_apply_requires_atlas_binary(monkeypatch) -> None:
    def fake_require_atlas_binary(_env: dict[str, str]) -> str:
        raise RuntimeError('Atlas CLI is not installed')

    monkeypatch.setattr(schema_apply_atlas, '_atlas_env', lambda: {'PATH': '/tmp/bin'})
    monkeypatch.setattr(schema_apply_atlas, '_require_atlas_binary', fake_require_atlas_binary)

    try:
        schema_apply_atlas.run_schema_apply(
            project_root=schema_apply_atlas.PROJECT_ROOT,
            workflow_status=_status(),
            invoked_by_startup=True,
        )
    except RuntimeError as exc:
        assert str(exc) == 'Atlas CLI is not installed'
    else:  # pragma: no cover
        raise AssertionError('expected run_schema_apply to raise when atlas binary is missing')


def test_model_modules_include_db_workflow_metadata_models() -> None:
    assert 'module_admin.entity.do.db_workflow_do' in schema_apply_atlas.MODEL_MODULES
