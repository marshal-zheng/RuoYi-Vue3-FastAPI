# ruff: noqa: ARG005, I001
from __future__ import annotations

import pytest
import json
import os
import sqlite3
import textwrap
from pathlib import Path
from types import SimpleNamespace

from alembic import util as alembic_util
from alembic.config import Config

from config.env import DataBaseWorkflowStatus
from scripts import db as db_workflow
from scripts.internal.db_workflow import dev_sync_service
from scripts.internal.db_workflow.deploy_release_service import ReleaseDeployReport, ReleaseDeployStepReport
from scripts.internal.db_workflow.finalize_release_service import FinalizeReleaseResult
from scripts.internal.db_workflow.workflow_verify_service import WorkflowRepositoryInspection, WorkflowVerifyStepReport


@pytest.fixture(autouse=True)
def isolated_remark_checks(monkeypatch):
    # These CLI adapter tests mock Alembic/schema and use fake workflow states.
    # Real conversion and gates are covered by the separate MySQL rehearsal.
    monkeypatch.setattr('scripts.data_migrations.remark_document_v2.verify_configured_database', lambda: {})


def _parse_shell_fields(output: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        fields[key] = value
    return fields


def _status(
    *,
    workflow_mode: str = 'migration',
    db_dev_sync_engine: str = 'atlas',
    db_target: str = 'mysql://127.0.0.1:3306/ruoyi-fastapi',
    startup_action: str = 'deploy',
    deploy_path: str = 'python scripts/db.py deploy --revision head',
) -> DataBaseWorkflowStatus:
    return DataBaseWorkflowStatus(
        workflow_mode=workflow_mode,
        db_dev_sync_engine=db_dev_sync_engine,
        db_target=db_target,
        startup_action=startup_action,
        deploy_path=deploy_path,
    )


def _dev_sync_report(
    *,
    result: str = 'success',
    schema_sync_result: str = 'atlas_apply_invoked',
    managed_data_result: str = 'applied',
    failed_step: str = 'none',
) -> db_workflow.DevSyncReport:
    return db_workflow.DevSyncReport(
        workflow_mode='development',
        db_target='mysql://127.0.0.1:3306/ruoyi-fastapi',
        trigger='manual',
        risk_boundary='destructive schema changes will be applied directly to the current database when dev-sync runs in development mode',
        visibility_policy='dev-full',
        compiled_checksum='compiled-sha',
        declaration_validation=dev_sync_service.DevSyncStepReport(
            step='declaration-validation',
            status='success',
            result='validated',
            duration_ms=1,
            affected_objects=('sys_menu:10',),
        ),
        schema_sync=dev_sync_service.DevSyncStepReport(
            step='schema-sync',
            status='success' if result == 'success' else 'failed',
            result=schema_sync_result,
            duration_ms=2,
            error=None if result == 'success' else 'schema failed',
        ),
        managed_data=dev_sync_service.DevSyncStepReport(
            step='managed-data-apply',
            status='success' if result == 'success' else 'skipped',
            result=managed_data_result,
            duration_ms=3 if result == 'success' else 0,
            affected_objects=('sys_menu:10', 'sys_role_menu:2:10') if result == 'success' else (),
        ),
        postcondition_verify=dev_sync_service.DevSyncStepReport(
            step='postcondition-verify',
            status='success' if result == 'success' else 'skipped',
            result='clean' if result == 'success' else 'skipped',
            duration_ms=1 if result == 'success' else 0,
        ),
        dev_sync_result=result,
        failed_step=failed_step,
        duration_ms=6,
        affected_objects=('sys_menu:10', 'sys_role_menu:2:10') if result == 'success' else (),
        residual_objects=(),
        managed_data_applied_operations=2 if result == 'success' else 0,
        managed_data_skipped_operations=0,
        metadata_updated_objects=2 if result == 'success' else 0,
        metadata_deactivated_objects=0,
    )


def _finalize_release_result(
    *,
    bundle_id: str | None = None,
    managed_data_operation_count: int = 0,
    data_finalize: str = 'no-op',
    visibility_finalize: str = 'no-op',
) -> FinalizeReleaseResult:
    bundle_dir = Path('/tmp/finalize-bundle') if bundle_id else None
    return FinalizeReleaseResult(
        bundle_id=bundle_id,
        bundle_dir=bundle_dir,
        bundle_file=bundle_dir / 'bundle.yaml' if bundle_dir else None,
        managed_data_file=bundle_dir / 'managed-data.yaml' if bundle_dir else None,
        release_manifest_file=bundle_dir / 'release.manifest.yaml' if bundle_dir else None,
        managed_data_operation_count=managed_data_operation_count,
        data_finalize=data_finalize,  # type: ignore[arg-type]
        visibility_finalize=visibility_finalize,  # type: ignore[arg-type]
    )


def _deploy_release_report(
    *,
    result: str = 'success',
    failed_step: str = 'none',
) -> ReleaseDeployReport:
    managed_status = 'success'
    manifest_status = 'success' if result == 'success' else 'failed'
    return ReleaseDeployReport(
        managed_data=ReleaseDeployStepReport(
            step='managed-data',
            status=managed_status,
            result='applied',
            applied_bundles=('20260402_001_release',),
            artifact_updates=1,
        ),
        release_manifest=ReleaseDeployStepReport(
            step='release-manifest',
            status=manifest_status if result == 'success' else 'failed',
            result='applied' if result == 'success' else 'failed',
            applied_bundles=('20260402_001_release',) if result == 'success' else (),
            artifact_updates=1 if result == 'success' else 0,
            error=None if result == 'success' else 'manifest failed',
        ),
        postcondition_verify=ReleaseDeployStepReport(
            step='postcondition-verify',
            status='success' if result == 'success' else 'skipped',
            result='clean' if result == 'success' else 'skipped',
        ),
        deploy_result=result,  # type: ignore[arg-type]
        failed_step=failed_step,
        applied_bundle_ids=('20260402_001_release',),
        skipped_bundle_ids=(),
        compiled_checksums=('compiled-sha',),
        release_plan_checksums=('release-plan-sha',),
        residual_objects=(),
        recovery_hint=None if result == 'success' else 'retry deploy after fixing manifest',
    )


def _repository_inspection(
    *,
    managed_data_drift: str = 'clean',
    visibility_drift: str = 'clean',
    pending_release_bundle: str = 'none',
    last_successful_action: str = 'deploy',
    declaration_status: str = 'success',
    bundle_status: str = 'success',
    bypass_status: str = 'success',
) -> WorkflowRepositoryInspection:
    return WorkflowRepositoryInspection(
        declaration_validation=WorkflowVerifyStepReport(
            step='declaration-validation',
            status=declaration_status,  # type: ignore[arg-type]
            result='validated' if declaration_status == 'success' else 'invalid',
            error=None if declaration_status == 'success' else 'invalid declarations',
            details=('scripts/seed_data/release-plan.yaml',),
        ),
        artifact_validation=WorkflowVerifyStepReport(
            step='artifact-validation',
            status='success' if declaration_status == 'success' else 'skipped',  # type: ignore[arg-type]
            result='validated' if declaration_status == 'success' else 'skipped',
            details=('db_artifacts/releases/20260402_001_release',) if declaration_status == 'success' else (),
        ),
        bundle_chain=WorkflowVerifyStepReport(
            step='bundle-chain',
            status=bundle_status,  # type: ignore[arg-type]
            result='replayed' if bundle_status == 'success' else 'failed',
            error=None if bundle_status == 'success' else 'bundle replay failed',
            details=('20260402_001_release',) if bundle_status == 'success' else ('db_artifacts/releases',),
        ),
        bypass_entrypoints=WorkflowVerifyStepReport(
            step='bypass-entrypoints',
            status=bypass_status,  # type: ignore[arg-type]
            result='validated' if bypass_status == 'success' else 'bypass-detected',
            error=None if bypass_status == 'success' else 'workflow bypass entrypoints detected',
            details=('scripts/start.sh',) if bypass_status == 'failed' else (),
        ),
        compiled_checksum='compiled-sha',
        release_plan_checksum='release-plan-sha',
        managed_data_drift=managed_data_drift,  # type: ignore[arg-type]
        managed_data_details=('sys_menu:100', 'sys_config:1') if managed_data_drift == 'drift' else (),
        visibility_drift=visibility_drift,  # type: ignore[arg-type]
        visibility_details=(
            'scripts/seed_data/release-plan.yaml',
            'db_artifacts/releases/20260402_001_release/release.manifest.yaml',
        )
        if visibility_drift == 'drift'
        else (),
        pending_release_bundle=pending_release_bundle,  # type: ignore[arg-type]
        last_successful_action=last_successful_action,
    )


def _write_finalize_test_project(project_root: Path) -> None:
    versions_dir = project_root / 'alembic' / 'versions'
    versions_dir.mkdir(parents=True)
    app_dir = project_root / 'app'
    app_dir.mkdir()

    (app_dir / '__init__.py').write_text('', encoding='utf-8')
    (app_dir / 'models.py').write_text(
        textwrap.dedent(
            """
            from sqlalchemy import Column, Integer, String
            from sqlalchemy.orm import declarative_base

            Base = declarative_base()


            class Example(Base):
                __tablename__ = 'example'

                id = Column(Integer, primary_key=True)
                name = Column(String(50), nullable=False)
                description = Column(String(100), nullable=True)
            """
        ),
        encoding='utf-8',
    )

    (project_root / 'alembic.ini').write_text(
        textwrap.dedent(
            f"""
            [alembic]
            script_location = {project_root / 'alembic'}
            prepend_sys_path = {project_root}
            sqlalchemy.url = sqlite:///{project_root / 'placeholder.db'}

            [loggers]
            keys = root

            [handlers]
            keys =

            [formatters]
            keys =

            [logger_root]
            level = WARN
            handlers =
            """
        ),
        encoding='utf-8',
    )

    (project_root / 'alembic' / 'env.py').write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            import os
            from logging.config import fileConfig

            from alembic import context
            from sqlalchemy import engine_from_config, pool

            from app.models import Base

            config = context.config
            if config.config_file_name is not None:
                fileConfig(config.config_file_name)

            target_metadata = Base.metadata


            def get_url() -> str:
                return os.getenv('ALEMBIC_DATABASE_URL') or config.get_main_option('sqlalchemy.url')


            def run_migrations_offline() -> None:
                context.configure(
                    url=get_url(),
                    target_metadata=target_metadata,
                    literal_binds=True,
                    compare_type=True,
                )
                with context.begin_transaction():
                    context.run_migrations()


            def run_migrations_online() -> None:
                configuration = config.get_section(config.config_ini_section) or {}
                configuration['sqlalchemy.url'] = get_url()
                connectable = engine_from_config(
                    configuration,
                    prefix='sqlalchemy.',
                    poolclass=pool.NullPool,
                )

                with connectable.connect() as connection:
                    context.configure(
                        connection=connection,
                        target_metadata=target_metadata,
                        compare_type=True,
                    )
                    with context.begin_transaction():
                        context.run_migrations()


            if context.is_offline_mode():
                run_migrations_offline()
            else:
                run_migrations_online()
            """
        ),
        encoding='utf-8',
    )

    (project_root / 'alembic' / 'script.py.mako').write_text(
        textwrap.dedent(
            '''
            """${message}"""

            revision = ${repr(up_revision)}
            down_revision = ${repr(down_revision)}
            branch_labels = ${repr(branch_labels)}
            depends_on = ${repr(depends_on)}

            from alembic import op
            import sqlalchemy as sa


            def upgrade() -> None:
                ${upgrades if upgrades else "pass"}


            def downgrade() -> None:
                ${downgrades if downgrades else "pass"}
            '''
        ),
        encoding='utf-8',
    )

    (versions_dir / '0001_initial.py').write_text(
        textwrap.dedent(
            '''
            """initial schema"""

            from alembic import op
            import sqlalchemy as sa

            revision = '0001_initial'
            down_revision = None
            branch_labels = None
            depends_on = None


            def upgrade() -> None:
                op.create_table(
                    'example',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                )


            def downgrade() -> None:
                op.drop_table('example')
            '''
        ),
        encoding='utf-8',
    )

    seed_data_dir = project_root / 'scripts' / 'seed_data'
    (seed_data_dir / 'base').mkdir(parents=True, exist_ok=True)
    (seed_data_dir / 'menus.registry.yaml').write_text(
        textwrap.dedent(
            """
            version: '1'
            menus: []
            role_grants: []
            """
        ).strip()
        + '\n',
        encoding='utf-8',
    )
    (seed_data_dir / 'release-plan.yaml').write_text(
        textwrap.dedent(
            """
            version: '1'
            release_key: finalize-test
            include:
              menu_ids: []
              role_grants: []
              dict_types: []
              config_keys: []
            """
        ).strip()
        + '\n',
        encoding='utf-8',
    )
    (seed_data_dir / 'base' / 'roles.yaml').write_text('roles: []\n', encoding='utf-8')
    (seed_data_dir / 'base' / 'dict_types.yaml').write_text('dict_types: []\n', encoding='utf-8')
    (seed_data_dir / 'base' / 'dict_data.yaml').write_text('dict_data: []\n', encoding='utf-8')
    (seed_data_dir / 'base' / 'configs.yaml').write_text('configs: []\n', encoding='utf-8')


def test_status_command_prints_workflow_snapshot(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: (_ for _ in ()).throw(AssertionError('status should not inspect schema drift')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('status should remain lightweight')),
    )

    exit_code = db_workflow.main(['status'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'workflow_mode=migration' in captured.out
    assert 'workflow_stage=deployment' in captured.out
    assert 'db_target=mysql://127.0.0.1:3306/ruoyi-fastapi' in captured.out
    assert 'startup_action=deploy' in captured.out
    assert 'allowed_actions=status,finalize,deploy,verify' in captured.out
    assert 'managed_scope=schema,menus,role_menus,dict_types,dict_data,configs,release_visibility' in captured.out
    assert 'schema_drift=unknown' in captured.out
    assert 'managed_data_drift=unknown' in captured.out
    assert 'visibility_drift=unknown' in captured.out
    assert 'pending_release_bundle=unknown' in captured.out
    assert 'last_successful_action=unknown' in captured.out
    assert 'status_path=python scripts/db.py status' in captured.out
    assert 'dev_sync_path=python scripts/db.py dev-sync' in captured.out
    assert 'verify_path=python scripts/db.py verify --ci' in captured.out


def test_status_command_supports_json_format(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: (_ for _ in ()).throw(AssertionError('status should not inspect schema drift')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('status should remain lightweight')),
    )

    exit_code = db_workflow.main(['status', '--format', 'json'])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload['workflow_mode'] == 'migration'
    assert payload['workflow_stage'] == 'deployment'
    assert payload['allowed_actions'] == ['status', 'finalize', 'deploy', 'verify']
    assert payload['schema_drift'] == 'unknown'
    assert payload['managed_data_drift'] == 'unknown'
    assert payload['visibility_drift'] == 'unknown'
    assert payload['pending_release_bundle'] == 'unknown'
    assert payload['last_successful_action'] == 'unknown'
    assert payload['managed_scope'] == [
        'schema',
        'menus',
        'role_menus',
        'dict_types',
        'dict_data',
        'configs',
        'release_visibility',
    ]


def test_status_command_json_contract_keys_are_stable(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: (_ for _ in ()).throw(AssertionError('status should not inspect schema drift')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('status should remain lightweight')),
    )

    exit_code = db_workflow.main(['status', '--format', 'json'])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert list(payload) == [
        'allowed_actions',
        'db_dev_sync_engine',
        'db_target',
        'deploy_path',
        'dev_sync_path',
        'finalize_path',
        'last_successful_action',
        'managed_data_drift',
        'managed_scope',
        'pending_release_bundle',
        'schema_drift',
        'startup_action',
        'status_path',
        'verify_path',
        'visibility_drift',
        'workflow_mode',
        'workflow_stage',
    ]


def test_reexecs_into_project_venv_when_current_python_lacks_alembic(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    venv_bin = project_root / 'venv' / 'bin'
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / 'python'
    venv_python.write_text('', encoding='utf-8')
    other_python = tmp_path / 'python3'
    other_python.write_text('', encoding='utf-8')

    execv_call: dict[str, object] = {}

    monkeypatch.setattr(db_workflow, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(db_workflow, 'SCRIPT_PATH', project_root / 'scripts' / 'db.py')
    monkeypatch.setattr(db_workflow.sys, 'executable', str(other_python))
    monkeypatch.setattr(db_workflow.sys, 'argv', ['scripts/db.py', 'dev-sync'])
    monkeypatch.setattr(db_workflow.importlib.util, 'find_spec', lambda name: None)
    monkeypatch.setattr(
        db_workflow.os,
        'execv',
        lambda executable, argv: execv_call.update({'executable': executable, 'argv': argv}),
    )

    db_workflow._maybe_reexec_with_project_venv()

    assert execv_call == {
        'executable': str(venv_python),
        'argv': [str(venv_python), str(project_root / 'scripts' / 'db.py'), 'dev-sync'],
    }


def test_skips_reexec_when_current_python_already_has_alembic(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    venv_bin = project_root / 'venv' / 'bin'
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / 'python'
    venv_python.write_text('', encoding='utf-8')
    current_python = tmp_path / 'python3'
    current_python.write_text('', encoding='utf-8')

    monkeypatch.setattr(db_workflow, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(db_workflow.sys, 'executable', str(current_python))
    monkeypatch.setattr(db_workflow.importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setattr(
        db_workflow.os,
        'execv',
        lambda executable, argv: (_ for _ in ()).throw(AssertionError('execv should not be called')),
    )

    db_workflow._maybe_reexec_with_project_venv()


def test_reexecs_when_namespace_alembic_exists_but_alembic_command_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    project_root = tmp_path / 'backend'
    venv_bin = project_root / 'venv' / 'bin'
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / 'python'
    venv_python.write_text('', encoding='utf-8')
    current_python = tmp_path / 'python3'
    current_python.write_text('', encoding='utf-8')

    execv_call: dict[str, object] = {}

    def fake_find_spec(name: str):
        if name == 'alembic.command':
            return None
        raise AssertionError(f'unexpected spec lookup: {name}')

    monkeypatch.setattr(db_workflow, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(db_workflow, 'SCRIPT_PATH', project_root / 'scripts' / 'db.py')
    monkeypatch.setattr(db_workflow.sys, 'executable', str(current_python))
    monkeypatch.setattr(db_workflow.sys, 'argv', ['scripts/db.py', 'status'])
    monkeypatch.setattr(db_workflow.importlib.util, 'find_spec', fake_find_spec)
    monkeypatch.setattr(
        db_workflow.os,
        'execv',
        lambda executable, argv: execv_call.update({'executable': executable, 'argv': argv}),
    )

    db_workflow._maybe_reexec_with_project_venv()

    assert execv_call == {
        'executable': str(venv_python),
        'argv': [str(venv_python), str(project_root / 'scripts' / 'db.py'), 'status'],
    }


def test_reexecs_when_find_spec_raises_module_not_found(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    venv_bin = project_root / 'venv' / 'bin'
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / 'python'
    venv_python.write_text('', encoding='utf-8')
    current_python = tmp_path / 'python3'
    current_python.write_text('', encoding='utf-8')

    execv_call: dict[str, object] = {}

    monkeypatch.setattr(db_workflow, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(db_workflow, 'SCRIPT_PATH', project_root / 'scripts' / 'db.py')
    monkeypatch.setattr(db_workflow.sys, 'executable', str(current_python))
    monkeypatch.setattr(db_workflow.sys, 'argv', ['scripts/db.py', 'dev-sync'])
    monkeypatch.setattr(
        db_workflow.importlib.util,
        'find_spec',
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError("No module named 'alembic'")),
    )
    monkeypatch.setattr(
        db_workflow.os,
        'execv',
        lambda executable, argv: execv_call.update({'executable': executable, 'argv': argv}),
    )

    db_workflow._maybe_reexec_with_project_venv()

    assert execv_call == {
        'executable': str(venv_python),
        'argv': [str(venv_python), str(project_root / 'scripts' / 'db.py'), 'dev-sync'],
    }


def test_dev_sync_command_fails_when_mode_is_not_development(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())

    exit_code = db_workflow.main(['dev-sync'])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert 'risk_boundary=destructive schema changes will be applied directly' in captured.out
    assert 'error=dev-sync command is disabled because DB_WORKFLOW_MODE is not "development"' in captured.out


def test_dev_sync_command_calls_configured_runner(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        db_workflow,
        'get_database_workflow_status',
        lambda: _status(workflow_mode='development', startup_action='dev-sync'),
    )
    monkeypatch.setattr(
        db_workflow,
        'execute_dev_sync',
        lambda **kwargs: _dev_sync_report(),
    )

    exit_code = db_workflow.main(['dev-sync'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'workflow_command=dev-sync' in captured.out
    assert 'compiled_checksum=compiled-sha' in captured.out
    assert 'declaration_validation_status=success' in captured.out
    assert 'schema_sync_result=atlas_apply_invoked' in captured.out
    assert 'managed_data_result=applied' in captured.out
    assert 'managed_data_applied_operations=2' in captured.out
    assert 'metadata_updated_objects=2' in captured.out
    assert 'postcondition_verify_result=clean' in captured.out
    assert 'visibility_policy=dev-full' in captured.out
    assert 'dev_sync_result=success' in captured.out
    assert 'failed_step=none' in captured.out


def test_dev_sync_command_uses_startup_trigger(monkeypatch, capsys) -> None:
    run_kwargs: dict[str, object] = {}

    monkeypatch.setattr(
        db_workflow,
        'get_database_workflow_status',
        lambda: _status(workflow_mode='development', startup_action='dev-sync'),
    )
    monkeypatch.setattr(
        db_workflow,
        'execute_dev_sync',
        lambda **kwargs: run_kwargs.update(kwargs) or _dev_sync_report(),
    )

    exit_code = db_workflow.main(['dev-sync', '--invoked-by-startup'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'schema_sync_result=atlas_apply_invoked' in captured.out
    assert 'managed_data_result=applied' in captured.out
    assert 'dev_sync_result=success' in captured.out
    assert run_kwargs['invoked_by_startup'] is True


def test_dev_sync_command_returns_structured_failure_report(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        db_workflow,
        'get_database_workflow_status',
        lambda: _status(workflow_mode='development', startup_action='dev-sync'),
    )
    monkeypatch.setattr(
        db_workflow,
        'execute_dev_sync',
        lambda **kwargs: _dev_sync_report(
            result='failed',
            schema_sync_result='failed',
            managed_data_result='skipped',
            failed_step='schema-sync',
        ),
    )

    exit_code = db_workflow.main(['dev-sync'])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert 'schema_sync_status=failed' in captured.out
    assert 'schema_sync_error=schema failed' in captured.out
    assert 'managed_data_status=skipped' in captured.out
    assert 'dev_sync_result=failed' in captured.out
    assert 'failed_step=schema-sync' in captured.out


def test_deploy_command_wraps_alembic_upgrade(monkeypatch, capsys) -> None:
    calls: list[tuple[Config, str]] = []
    alembic_config = Config()

    def fake_upgrade(config: Config, revision: str) -> None:
        calls.append((config, revision))

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow.command, 'upgrade', fake_upgrade)
    monkeypatch.setattr(db_workflow, 'execute_release_deploy', lambda **kwargs: _deploy_release_report())

    exit_code = db_workflow.main(['deploy', '--revision', 'head'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [(alembic_config, 'head')]
    assert 'workflow_command=deploy' in captured.out
    assert 'deploy_revision=head' in captured.out
    assert 'schema_deploy_result=success' in captured.out
    assert 'compiled_checksums=compiled-sha' in captured.out
    assert 'release_plan_checksums=release-plan-sha' in captured.out
    assert 'managed_data_deploy_result=applied' in captured.out
    assert 'release_manifest_deploy_result=applied' in captured.out
    assert 'postcondition_verify_result=clean' in captured.out
    assert 'applied_bundle_ids=20260402_001_release' in captured.out
    assert 'deploy_result=success' in captured.out


def test_deploy_command_returns_failure_when_release_deploy_fails(monkeypatch, capsys) -> None:
    alembic_config = Config()

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(
        db_workflow,
        'execute_release_deploy',
        lambda **kwargs: _deploy_release_report(result='failed', failed_step='release-manifest'),
    )

    exit_code = db_workflow.main(['deploy', '--revision', 'head'])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert 'schema_deploy_result=success' in captured.out
    assert 'compiled_checksums=compiled-sha' in captured.out
    assert 'release_manifest_deploy_status=failed' in captured.out
    assert 'release_manifest_deploy_error=manifest failed' in captured.out
    assert 'failed_step=release-manifest' in captured.out
    assert 'recovery_hint=retry deploy after fixing manifest' in captured.out
    assert 'deploy_result=failed' in captured.out


def test_deploy_command_keeps_no_bundle_path_idempotent(monkeypatch, capsys) -> None:
    alembic_config = Config()

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(
        db_workflow,
        'execute_release_deploy',
        lambda **kwargs: ReleaseDeployReport(
            managed_data=ReleaseDeployStepReport(step='managed-data', status='success', result='no-op'),
            release_manifest=ReleaseDeployStepReport(step='release-manifest', status='success', result='no-op'),
            postcondition_verify=ReleaseDeployStepReport(step='postcondition-verify', status='success', result='no-op'),
            deploy_result='success',
            failed_step='none',
            applied_bundle_ids=(),
            skipped_bundle_ids=(),
        ),
    )

    exit_code = db_workflow.main(['deploy', '--revision', 'head'])

    captured = capsys.readouterr()
    fields = _parse_shell_fields(captured.out)

    assert exit_code == 0
    assert fields['managed_data_deploy_result'] == 'no-op'
    assert fields['release_manifest_deploy_result'] == 'no-op'
    assert fields['postcondition_verify_result'] == 'no-op'
    assert fields['deploy_result'] == 'success'


def test_finalize_command_creates_revision_and_validates_against_real_temp_database(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    project_root = tmp_path / 'finalize_fixture'
    project_root.mkdir()
    _write_finalize_test_project(project_root)
    finalize_database_path = project_root / 'finalize.sqlite3'
    cleanup_calls: list[str] = []
    previous_cwd = Path.cwd()

    monkeypatch.setattr(db_workflow, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_prepare_finalize_database',
        lambda: ('sqlite_finalize_db', f'sqlite:///{finalize_database_path}'),
    )
    monkeypatch.setattr(db_workflow, '_cleanup_finalize_database', lambda database: cleanup_calls.append(database))
    monkeypatch.setattr(
        db_workflow,
        'finalize_release_artifacts',
        lambda **kwargs: _finalize_release_result(),
    )
    monkeypatch.setenv('ALEMBIC_DATABASE_URL', 'sqlite:////tmp/original.db')

    try:
        exit_code = db_workflow.main(['finalize', '--message', 'add description column'])
    finally:
        os.chdir(previous_cwd)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert cleanup_calls == ['sqlite_finalize_db']
    assert 'workflow_command=finalize' in captured.out
    assert 'formal_head_before=0001_initial' in captured.out
    assert 'finalize_temp_database=sqlite_finalize_db' in captured.out
    assert 'schema_revision=' in captured.out
    assert 'data_finalize=no-op' in captured.out
    assert 'visibility_finalize=no-op' in captured.out
    assert 'finalize_validation=passed' in captured.out
    assert 'finalize_cleanup=done' in captured.out
    assert os.environ.get('ALEMBIC_DATABASE_URL') == 'sqlite:////tmp/original.db'

    generated_revisions = sorted((project_root / 'alembic' / 'versions').glob('*add_description_column.py'))
    assert len(generated_revisions) == 1
    generated_revision = generated_revisions[0]
    generated_revision_content = generated_revision.read_text(encoding='utf-8')
    assert "op.add_column('example'" in generated_revision_content
    assert "'description'" in generated_revision_content
    assert f'revision_file={generated_revision}' in captured.out

    with sqlite3.connect(finalize_database_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info('example')").fetchall()]

    assert columns == ['id', 'name', 'description']


def test_finalize_command_fails_when_no_drift(monkeypatch, capsys) -> None:
    alembic_config = Config()
    cleanup_calls: list[str] = []

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow, '_get_formal_revision_heads', lambda config: 'head_before_finalize')
    monkeypatch.setattr(
        db_workflow,
        '_prepare_finalize_database',
        lambda: ('ruoyi_fastapi_finalize_456', 'mysql+pymysql://root:pwd@127.0.0.1:3306/ruoyi_fastapi_finalize_456'),
    )
    monkeypatch.setattr(db_workflow, '_cleanup_finalize_database', lambda database: cleanup_calls.append(database))
    monkeypatch.setattr(db_workflow.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(db_workflow.command, 'check', lambda config: None)
    monkeypatch.setattr(
        db_workflow,
        'finalize_release_artifacts',
        lambda **kwargs: _finalize_release_result(),
    )

    exit_code = db_workflow.main(['finalize', '--message', 'no changes'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert cleanup_calls == ['ruoyi_fastapi_finalize_456']
    assert 'schema_finalize=no-op' in captured.out
    assert 'data_finalize=no-op' in captured.out
    assert 'visibility_finalize=no-op' in captured.out


def test_finalize_command_prints_bundle_outputs(monkeypatch, capsys) -> None:
    alembic_config = Config()
    head_calls = {'count': 0}

    def fake_heads(config: Config) -> str:
        head_calls['count'] += 1
        return 'head_before_finalize' if head_calls['count'] == 1 else 'head_after_finalize'

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow, '_get_formal_revision_heads', fake_heads)
    monkeypatch.setattr(
        db_workflow,
        '_prepare_finalize_database',
        lambda: ('ruoyi_fastapi_finalize_999', 'mysql+pymysql://root:pwd@127.0.0.1:3306/ruoyi_fastapi_finalize_999'),
    )
    monkeypatch.setattr(db_workflow, '_cleanup_finalize_database', lambda database: None)
    monkeypatch.setattr(db_workflow.command, 'upgrade', lambda config, revision: None)

    def fake_check(config: Config) -> None:
        raise alembic_util.exc.CommandError('drift detected')

    monkeypatch.setattr(db_workflow.command, 'check', fake_check)
    monkeypatch.setattr(
        db_workflow.command,
        'revision',
        lambda config, message, autogenerate: SimpleNamespace(path='/tmp/generated_revision.py'),
    )
    monkeypatch.setattr(db_workflow, '_normalize_revision_script', lambda result: Path('/tmp/generated_revision.py'))
    monkeypatch.setattr(db_workflow, '_validate_generated_revision', lambda config: None)
    monkeypatch.setattr(
        db_workflow,
        'finalize_release_artifacts',
        lambda **kwargs: _finalize_release_result(
            bundle_id='20260402_001_release',
            managed_data_operation_count=6,
            data_finalize='generated',
            visibility_finalize='generated',
        ),
    )

    exit_code = db_workflow.main(['finalize', '--message', 'bundle release'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'revision_file=/tmp/generated_revision.py' in captured.out
    assert 'schema_revision=head_after_finalize' in captured.out
    assert 'bundle_id=20260402_001_release' in captured.out
    assert 'managed_data_operation_count=6' in captured.out
    assert 'managed_data_file=/tmp/finalize-bundle/managed-data.yaml' in captured.out
    assert 'release_manifest_file=/tmp/finalize-bundle/release.manifest.yaml' in captured.out


def test_finalize_command_removes_generated_revision_when_validation_fails(monkeypatch, capsys) -> None:
    alembic_config = Config()
    removed_paths: list[Path] = []

    def fake_check(config: Config) -> None:
        if not hasattr(fake_check, 'called'):
            fake_check.called = True
            raise alembic_util.exc.CommandError('drift detected')
        raise alembic_util.exc.CommandError('drift still present')

    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(db_workflow, '_build_alembic_config', lambda: alembic_config)
    monkeypatch.setattr(db_workflow, '_get_formal_revision_heads', lambda config: 'head_before_finalize')
    monkeypatch.setattr(
        db_workflow,
        '_prepare_finalize_database',
        lambda: ('ruoyi_fastapi_finalize_789', 'mysql+pymysql://root:pwd@127.0.0.1:3306/ruoyi_fastapi_finalize_789'),
    )
    monkeypatch.setattr(db_workflow, '_cleanup_finalize_database', lambda database: None)
    monkeypatch.setattr(db_workflow.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(db_workflow.command, 'check', fake_check)
    monkeypatch.setattr(
        db_workflow.command,
        'revision',
        lambda config, message, autogenerate: SimpleNamespace(path='/tmp/failed_generated_revision.py'),
    )
    monkeypatch.setattr(db_workflow, '_remove_generated_revision_file', lambda path: removed_paths.append(path))

    exit_code = db_workflow.main(['finalize', '--message', 'broken finalize'])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert removed_paths == [Path('/tmp/failed_generated_revision.py')]
    assert 'error=drift still present' in captured.out


def test_verify_command_runs_full_workflow_checks(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: ('clean', WorkflowVerifyStepReport(step='schema', status='success', result='passed')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: _repository_inspection(),
    )

    exit_code = db_workflow.main(['verify', '--ci'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'workflow_command=verify' in captured.out
    assert 'verify_ci=true' in captured.out
    assert 'verify_scope=full' in captured.out
    assert 'declaration_verify_result=validated' in captured.out
    assert 'compiled_checksum=compiled-sha' in captured.out
    assert 'release_plan_checksum=release-plan-sha' in captured.out
    assert 'artifact_validation_result=validated' in captured.out
    assert 'schema_verify_result=passed' in captured.out
    assert 'bundle_chain_verify_result=replayed' in captured.out
    assert 'bypass_verify_result=validated' in captured.out
    assert 'managed_data_verify_result=passed' in captured.out
    assert 'visibility_verify_result=passed' in captured.out
    assert 'verify_result=passed' in captured.out
    assert 'failed_step=none' in captured.out


def test_verify_command_ci_output_contract_is_stable(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: ('clean', WorkflowVerifyStepReport(step='schema', status='success', result='passed')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: _repository_inspection(),
    )

    exit_code = db_workflow.main(['verify', '--ci'])

    captured = capsys.readouterr()
    fields = _parse_shell_fields(captured.out)

    assert exit_code == 0
    assert set(fields) >= {
        'workflow_mode',
        'db_dev_sync_engine',
        'db_target',
        'startup_action',
        'deploy_path',
        'workflow_stage',
        'allowed_actions',
        'managed_scope',
        'status_path',
        'dev_sync_path',
        'finalize_path',
        'verify_path',
        'schema_drift',
        'managed_data_drift',
        'visibility_drift',
        'pending_release_bundle',
        'last_successful_action',
        'workflow_command',
        'verify_ci',
        'verify_scope',
        'declaration_verify_status',
        'declaration_verify_result',
        'declaration_verify_details',
        'compiled_checksum',
        'release_plan_checksum',
        'artifact_validation_status',
        'artifact_validation_result',
        'artifact_validation_details',
        'schema_verify_status',
        'schema_verify_result',
        'bundle_chain_verify_status',
        'bundle_chain_verify_result',
        'bundle_chain_verify_details',
        'bypass_verify_status',
        'bypass_verify_result',
        'managed_data_verify_status',
        'managed_data_verify_result',
        'visibility_verify_status',
        'visibility_verify_result',
        'failed_step',
        'verify_result',
    }
    assert fields['verify_ci'] == 'true'
    assert fields['verify_scope'] == 'full'
    assert fields['verify_result'] == 'passed'


def test_verify_command_fails_on_managed_data_drift(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: ('clean', WorkflowVerifyStepReport(step='schema', status='success', result='passed')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: _repository_inspection(
            managed_data_drift='drift',
            visibility_drift='drift',
            pending_release_bundle='required',
        ),
    )

    exit_code = db_workflow.main(['verify'])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert 'verify_scope=full' in captured.out
    assert 'managed_data_verify_result=drift-detected' in captured.out
    assert 'managed_data_verify_details=sys_menu:100,sys_config:1' in captured.out
    assert 'artifact_validation_result=validated' in captured.out
    assert 'visibility_verify_result=drift-detected' in captured.out
    assert 'pending_release_bundle=required' in captured.out
    assert 'failed_step=managed-data' in captured.out
    assert 'verify_result=failed' in captured.out


def test_verify_command_supports_schema_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: ('clean', WorkflowVerifyStepReport(step='schema', status='success', result='passed')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('managed data inspection should be skipped')),
    )

    exit_code = db_workflow.main(['verify', '--schema-only'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'verify_scope=schema-only' in captured.out
    assert 'schema_verify_result=passed' in captured.out
    assert 'declaration_verify_result=skipped' in captured.out
    assert 'managed_data_verify_result=skipped' in captured.out
    assert 'visibility_verify_result=skipped' in captured.out


def test_verify_command_supports_managed_data_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(db_workflow, 'get_database_workflow_status', lambda: _status())
    monkeypatch.setattr(
        db_workflow,
        '_inspect_schema_drift',
        lambda: (_ for _ in ()).throw(AssertionError('schema inspection should be skipped')),
    )
    monkeypatch.setattr(
        db_workflow,
        'inspect_release_workflow',
        lambda **kwargs: _repository_inspection(last_successful_action='dev-sync'),
    )

    exit_code = db_workflow.main(['verify', '--managed-data-only'])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'verify_scope=managed-data-only' in captured.out
    assert 'schema_verify_result=skipped' in captured.out
    assert 'declaration_verify_result=validated' in captured.out
    assert 'managed_data_verify_result=passed' in captured.out
    assert 'last_successful_action=dev-sync' in captured.out
