#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""Unified database workflow entrypoint."""

from __future__ import annotations

import argparse
import json
import importlib
import importlib.util
import os
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve()


def _maybe_reexec_with_project_venv() -> None:
    """
    Prefer the backend virtualenv when the current interpreter lacks Alembic.
    This lets developers run `python scripts/db.py ...` without
    manually activating `venv` first.
    """
    venv_python = PROJECT_ROOT / 'venv' / 'bin' / 'python'
    if not venv_python.exists():
        return

    try:
        if Path(sys.executable).resolve() == venv_python.resolve():
            return
    except OSError:
        return

    try:
        if importlib.util.find_spec('alembic.command') is not None:
            return
    except ModuleNotFoundError:
        pass

    os.execv(str(venv_python), [str(venv_python), str(SCRIPT_PATH), *sys.argv[1:]])


_maybe_reexec_with_project_venv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from config.env import (
    DataBaseConfig,
    DataBaseWorkflowStatus,
    get_database_workflow_status,
)
from scripts.data_migrations import remark_document_v2 as remark_migration
from scripts.internal.db_workflow.deploy_release_service import ReleaseDeployReport, execute_release_deploy
from scripts.internal.db_workflow.dev_sync_service import DevSyncReport, execute_dev_sync
from scripts.internal.db_workflow.finalize_release_service import finalize_release_artifacts
from scripts.internal.db_workflow.workflow_verify_service import (
    WorkflowRepositoryInspection,
    WorkflowVerifyStepReport,
    inspect_release_workflow,
)

SchemaApplyRunner = Callable[..., str | None]


class WorkflowCommandError(RuntimeError):
    """Raised when a workflow command cannot proceed."""


def _bool_text(value: bool) -> str:
    return 'true' if value else 'false'


def _print_field(name: str, value: str) -> None:
    print(f'{name}={value}')


def _build_status_payload(status: DataBaseWorkflowStatus) -> dict[str, object]:
    return asdict(status)


def _shell_value(value: object) -> str:
    if isinstance(value, bool):
        return _bool_text(value)
    if isinstance(value, tuple):
        return ','.join(str(item) for item in value)
    return str(value)


def _print_status(status: DataBaseWorkflowStatus) -> None:
    for field_name, field_value in _build_status_payload(status).items():
        _print_field(field_name, _shell_value(field_value))


def _print_status_json(status: DataBaseWorkflowStatus) -> None:
    print(json.dumps(_build_status_payload(status), ensure_ascii=False, sort_keys=True))


def _print_csv_field(name: str, values: tuple[str, ...]) -> None:
    _print_field(name, ','.join(values))


def _print_verify_step(prefix: str, report: WorkflowVerifyStepReport) -> None:
    _print_field(f'{prefix}_status', report.status)
    _print_field(f'{prefix}_result', report.result)
    if report.details:
        _print_csv_field(f'{prefix}_details', report.details)
    if report.error:
        _print_field(f'{prefix}_error', report.error)


def _print_dev_sync_report(report: DevSyncReport) -> None:
    _print_field('workflow_command', 'dev-sync')
    _print_field('trigger', report.trigger)

    _print_field('risk_boundary', report.risk_boundary)
    _print_field('compiled_checksum', report.compiled_checksum)
    _print_field('declaration_validation_status', report.declaration_validation.status)
    _print_field('declaration_validation_result', report.declaration_validation.result)
    _print_field('declaration_validation_duration_ms', str(report.declaration_validation.duration_ms))
    if report.declaration_validation.affected_objects:
        _print_csv_field('declaration_validation_affected_objects', report.declaration_validation.affected_objects)
    if report.declaration_validation.error:
        _print_field('declaration_validation_error', report.declaration_validation.error)

    _print_field('schema_sync_status', report.schema_sync.status)
    _print_field('schema_sync_result', report.schema_sync.result)
    _print_field('schema_sync_duration_ms', str(report.schema_sync.duration_ms))
    if report.schema_sync.affected_objects:
        _print_csv_field('schema_sync_affected_objects', report.schema_sync.affected_objects)
    if report.schema_sync.error:
        _print_field('schema_sync_error', report.schema_sync.error)

    _print_field('managed_data_status', report.managed_data.status)
    _print_field('managed_data_result', report.managed_data.result)
    _print_field('managed_data_duration_ms', str(report.managed_data.duration_ms))
    _print_field('managed_data_applied_operations', str(report.managed_data_applied_operations))
    _print_field('managed_data_skipped_operations', str(report.managed_data_skipped_operations))
    _print_field('metadata_updated_objects', str(report.metadata_updated_objects))
    _print_field('metadata_deactivated_objects', str(report.metadata_deactivated_objects))
    if report.managed_data.affected_objects:
        _print_csv_field('managed_data_affected_objects', report.managed_data.affected_objects)
    if report.managed_data.error:
        _print_field('managed_data_error', report.managed_data.error)

    _print_field('postcondition_verify_status', report.postcondition_verify.status)
    _print_field('postcondition_verify_result', report.postcondition_verify.result)
    _print_field('postcondition_verify_duration_ms', str(report.postcondition_verify.duration_ms))
    if report.postcondition_verify.affected_objects:
        _print_csv_field('postcondition_verify_residual_objects', report.postcondition_verify.affected_objects)
    if report.postcondition_verify.error:
        _print_field('postcondition_verify_error', report.postcondition_verify.error)

    _print_field('visibility_policy', report.visibility_policy)
    _print_field('dev_sync_result', report.dev_sync_result)
    _print_field('failed_step', report.failed_step)
    _print_field('duration_ms', str(report.duration_ms))
    if report.affected_objects:
        _print_csv_field('affected_objects', report.affected_objects)
    if report.residual_objects:
        _print_csv_field('residual_objects', report.residual_objects)


def _print_release_deploy_report(report: ReleaseDeployReport) -> None:  # noqa: PLR0912
    if report.compiled_checksums:
        _print_csv_field('compiled_checksums', report.compiled_checksums)
    if report.release_plan_checksums:
        _print_csv_field('release_plan_checksums', report.release_plan_checksums)

    _print_field('managed_data_deploy_status', report.managed_data.status)
    _print_field('managed_data_deploy_result', report.managed_data.result)
    _print_field('managed_data_artifact_updates', str(report.managed_data.artifact_updates))
    if report.managed_data.applied_bundles:
        _print_csv_field('managed_data_applied_bundles', report.managed_data.applied_bundles)
    if report.managed_data.skipped_bundles:
        _print_csv_field('managed_data_skipped_bundles', report.managed_data.skipped_bundles)
    if report.managed_data.error:
        _print_field('managed_data_deploy_error', report.managed_data.error)

    _print_field('release_manifest_deploy_status', report.release_manifest.status)
    _print_field('release_manifest_deploy_result', report.release_manifest.result)
    _print_field('release_manifest_artifact_updates', str(report.release_manifest.artifact_updates))
    if report.release_manifest.applied_bundles:
        _print_csv_field('release_manifest_applied_bundles', report.release_manifest.applied_bundles)
    if report.release_manifest.skipped_bundles:
        _print_csv_field('release_manifest_skipped_bundles', report.release_manifest.skipped_bundles)
    if report.release_manifest.error:
        _print_field('release_manifest_deploy_error', report.release_manifest.error)

    _print_field('postcondition_verify_status', report.postcondition_verify.status)
    _print_field('postcondition_verify_result', report.postcondition_verify.result)
    if report.postcondition_verify.error:
        _print_field('postcondition_verify_error', report.postcondition_verify.error)
    if report.residual_objects:
        _print_csv_field('residual_objects', report.residual_objects)

    if report.applied_bundle_ids:
        _print_csv_field('applied_bundle_ids', report.applied_bundle_ids)
    if report.skipped_bundle_ids:
        _print_csv_field('skipped_bundle_ids', report.skipped_bundle_ids)
    _print_field('failed_step', report.failed_step)
    if report.recovery_hint:
        _print_field('recovery_hint', report.recovery_hint)
    _print_field('deploy_result', report.deploy_result)


def _build_alembic_config() -> Config:
    return Config(str(PROJECT_ROOT / 'alembic.ini'))


def _database_type() -> str:
    return DataBaseConfig.db_type.lower()


def _build_admin_database_url() -> str:
    username = DataBaseConfig.db_username
    password = quote_plus(DataBaseConfig.db_password)

    if _database_type() == 'postgresql':
        return f'postgresql+psycopg2://{username}:{password}@{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/postgres'
    if _database_type() == 'mysql':
        return (
            f'mysql+pymysql://{username}:{password}@'
            f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/mysql?charset=utf8mb4'
        )
    raise WorkflowCommandError(f'unsupported DB_TYPE for finalize workflow: {_database_type()}')


def _build_database_url(database: str) -> str:
    username = DataBaseConfig.db_username
    password = quote_plus(DataBaseConfig.db_password)

    if _database_type() == 'postgresql':
        return (
            f'postgresql+psycopg2://{username}:{password}@{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{database}'
        )
    return (
        f'mysql+pymysql://{username}:{password}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{database}?charset=utf8mb4'
    )


def _build_finalize_database_name() -> str:
    database = DataBaseConfig.db_database
    suffix = f'_finalize_{int(time.time())}_{os.getpid()}'
    max_length = 63 if _database_type() == 'postgresql' else 64
    return f'{database}{suffix}'[:max_length]


def _wait_for_database_ready(admin_url: str, timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        engine = create_engine(admin_url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(1)
        finally:
            engine.dispose()

    raise WorkflowCommandError(f'database is not ready in {timeout_seconds}s') from last_error


def _drop_database(admin_url: str, database: str) -> None:
    engine = create_engine(admin_url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if _database_type() == 'mysql':
                connection.execute(text(f'DROP DATABASE IF EXISTS `{database}`'))
                return

            connection.execute(
                text(
                    'SELECT pg_terminate_backend(pid) '
                    'FROM pg_stat_activity '
                    'WHERE datname = :name AND pid <> pg_backend_pid()'
                ),
                {'name': database},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))
    finally:
        engine.dispose()


def _create_database(admin_url: str, database: str) -> None:
    engine = create_engine(admin_url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if _database_type() == 'mysql':
                connection.execute(
                    text(f'CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
                )
                return

            connection.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        engine.dispose()


def _prepare_finalize_database() -> tuple[str, str]:
    admin_url = _build_admin_database_url()
    finalize_database = _build_finalize_database_name()

    _wait_for_database_ready(admin_url)
    _drop_database(admin_url, finalize_database)
    _create_database(admin_url, finalize_database)
    return finalize_database, _build_database_url(finalize_database)


def _cleanup_finalize_database(finalize_database: str) -> None:
    _drop_database(_build_admin_database_url(), finalize_database)


@contextmanager
def _override_alembic_database_url(database_url: str) -> Iterator[None]:
    previous = os.environ.get('ALEMBIC_DATABASE_URL')
    os.environ['ALEMBIC_DATABASE_URL'] = database_url
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop('ALEMBIC_DATABASE_URL', None)
        else:
            os.environ['ALEMBIC_DATABASE_URL'] = previous


def _get_formal_revision_heads(alembic_config: Config) -> str:
    script_directory = ScriptDirectory.from_config(alembic_config)
    return ','.join(script_directory.get_heads())


def _normalize_revision_script(revision_result: object) -> Path:
    if revision_result is None:
        raise WorkflowCommandError('alembic revision did not return a generated script')

    if isinstance(revision_result, list):
        if len(revision_result) != 1 or revision_result[0] is None:
            raise WorkflowCommandError('unexpected multiple revision results generated during finalize')
        revision_result = revision_result[0]

    revision_path = getattr(revision_result, 'path', None)
    if not revision_path:
        raise WorkflowCommandError('generated Alembic revision does not expose a path')

    return Path(revision_path)


def _remove_generated_revision_file(revision_path: Path) -> None:
    revision_path.unlink(missing_ok=True)


def _assert_finalize_has_drift(alembic_config: Config) -> None:
    try:
        command.check(alembic_config)
    except CommandError:
        return

    raise WorkflowCommandError('no schema drift detected; finalize did not generate a migration')


def _has_schema_drift(alembic_config: Config) -> bool:
    try:
        command.check(alembic_config)
    except CommandError:
        return True
    return False


def _validate_generated_revision(alembic_config: Config) -> None:
    command.upgrade(alembic_config, 'head')
    command.check(alembic_config)


def _load_schema_apply_runner(engine: str) -> SchemaApplyRunner:
    module_name = f'scripts.internal.db_workflow.schema_apply_{engine}'
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via command path
        if exc.name == module_name:
            raise WorkflowCommandError(
                f'dev-sync engine "{engine}" is not available yet. Expected module: {module_name}.py'
            ) from exc
        raise

    runner = getattr(module, 'run_schema_apply', None)
    if runner is None or not callable(runner):
        raise WorkflowCommandError(
            f'dev-sync engine "{engine}" must expose callable run_schema_apply(**kwargs) in {module_name}.py'
        )
    return runner


def _inspect_schema_drift() -> tuple[str, WorkflowVerifyStepReport]:
    alembic_config = _build_alembic_config()
    finalize_database: str | None = None

    try:
        finalize_database, finalize_database_url = _prepare_finalize_database()
        with _override_alembic_database_url(finalize_database_url):
            command.upgrade(alembic_config, 'head')
            try:
                command.check(alembic_config)
            except CommandError as exc:
                return (
                    'drift',
                    WorkflowVerifyStepReport(
                        step='schema',
                        status='failed',
                        result='drift-detected',
                        error=str(exc),
                    ),
                )
    except Exception as exc:
        return (
            'unknown',
            WorkflowVerifyStepReport(
                step='schema',
                status='failed',
                result='failed',
                error=str(exc),
            ),
        )
    finally:
        if finalize_database is not None:
            _cleanup_finalize_database(finalize_database)

    return (
        'clean',
        WorkflowVerifyStepReport(
            step='schema',
            status='success',
            result='passed',
        ),
    )


def _merge_pending_release_bundle(
    *,
    schema_drift: str,
    repository_inspection: WorkflowRepositoryInspection | None,
) -> str:
    if schema_drift == 'drift':
        return 'required'
    if repository_inspection is None:
        return 'unknown' if schema_drift == 'unknown' else 'none'
    if repository_inspection.pending_release_bundle == 'required':
        return 'required'
    if schema_drift == 'clean' and repository_inspection.pending_release_bundle == 'none':
        return 'none'
    return 'unknown'


def run_remark_check_command(*, report):
    engine = remark_migration.configured_engine()
    try:
        with engine.connect() as connection:
            remark_migration.inspect_database_to_report(connection, report)
            _print_field('remark_report', str(report))
            return 0
    finally:
        engine.dispose()


def run_status_command(*, output_format: str) -> int:
    status = get_database_workflow_status()
    if output_format == 'json':
        _print_status_json(status)
        return 0

    _print_status(status)
    return 0


def run_dev_sync_command(*, invoked_by_startup: bool, remark_backup_manifest=None, remark_writers_stopped=False) -> int:
    status = get_database_workflow_status()
    _print_status(status)

    if status.workflow_mode != 'development':
        _print_field('workflow_command', 'dev-sync')
        _print_field('trigger', 'startup' if invoked_by_startup else 'manual')
        _print_field(
            'risk_boundary',
            'destructive schema changes will be applied directly to the current database when dev-sync runs in development mode',
        )
        raise WorkflowCommandError(
            'dev-sync command is disabled because DB_WORKFLOW_MODE is not "development". '
            'Set DB_WORKFLOW_MODE=development explicitly before running this development-only command.'
        )

    report = execute_dev_sync(
        project_root=PROJECT_ROOT,
        workflow_status=status,
        invoked_by_startup=invoked_by_startup,
        schema_apply_runner_loader=_load_schema_apply_runner,
        remark_backup_manifest=remark_backup_manifest,
        remark_writers_stopped=remark_writers_stopped,
    )
    _print_dev_sync_report(report)
    return 0 if report.dev_sync_result == 'success' else 1


def run_wait_db_command(*, max_retries: int, delay: int) -> int:
    wait_for_db_module = importlib.import_module('scripts.internal.wait_for_db')
    return wait_for_db_module.main(
        ['--max-retries', str(max_retries), '--delay', str(delay)],
    )


def run_bootstrap_seed_command(*, env: str, reset: bool) -> int:
    remark_migration.verify_configured_database()
    os.environ['APP_ENV'] = env
    bootstrap_seed_module = importlib.import_module('scripts.internal.bootstrap_seed')
    bootstrap_seed_module = importlib.reload(bootstrap_seed_module)
    argv = ['--env', env, '--bootstrap-only']
    if reset:
        argv.append('--reset')
    return bootstrap_seed_module.main(argv)


def run_deploy_command(*, revision: str, remark_backup_manifest=None, remark_writers_stopped=False) -> int:
    status = get_database_workflow_status()
    _print_status(status)
    _print_field('workflow_command', 'deploy')
    _print_field('deploy_revision', revision)
    alembic_config = _build_alembic_config()
    alembic_config.attributes['upgrade_revision_table'] = True
    alembic_config.attributes['remark_migration'] = {
        'backup_manifest': remark_backup_manifest,
        'writers_stopped': remark_writers_stopped,
    }
    command.upgrade(alembic_config, revision)
    remark_migration.verify_configured_database()
    _print_field('schema_deploy_result', 'success')
    report = execute_release_deploy(output_root=PROJECT_ROOT / 'db_artifacts' / 'releases')
    _print_release_deploy_report(report)
    return 0 if report.deploy_result == 'success' else 1


def run_finalize_command(*, message: str) -> int:
    status = get_database_workflow_status()
    _print_status(status)
    _print_field('workflow_command', 'finalize')
    _print_field('finalize_message', message)

    alembic_config = _build_alembic_config()
    alembic_config.attributes['upgrade_revision_table'] = True
    formal_heads = _get_formal_revision_heads(alembic_config)
    finalize_database, finalize_database_url = _prepare_finalize_database()
    revision_path: Path | None = None

    _print_field('formal_head_before', formal_heads or 'base')
    _print_field('finalize_temp_database', finalize_database)

    try:
        with _override_alembic_database_url(finalize_database_url):
            command.upgrade(alembic_config, 'head')
            schema_revision = formal_heads or 'base'

            if _has_schema_drift(alembic_config):
                revision_result = command.revision(alembic_config, message=message, autogenerate=True)
                revision_path = _normalize_revision_script(revision_result)
                _print_field('revision_file', str(revision_path))

                _validate_generated_revision(alembic_config)
                schema_revision = _get_formal_revision_heads(alembic_config) or schema_revision
            else:
                _print_field('schema_finalize', 'no-op')

            release_result = finalize_release_artifacts(
                project_root=PROJECT_ROOT,
                finalize_database_url=finalize_database_url,
                schema_revision=schema_revision,
                message=message,
            )
            _print_field('schema_revision', schema_revision or 'base')
            _print_field('release_selection_mode', release_result.selection_mode)
            _print_field('managed_data_operation_count', str(release_result.managed_data_operation_count))
            if release_result.bundle_id is None:
                _print_field('data_finalize', release_result.data_finalize)
                _print_field('visibility_finalize', release_result.visibility_finalize)
            else:
                _print_field('bundle_id', release_result.bundle_id)
                _print_field('bundle_dir', str(release_result.bundle_dir))
                _print_field('bundle_file', str(release_result.bundle_file))
                _print_field('managed_data_file', str(release_result.managed_data_file))
                if release_result.data_finalize == 'no-op':
                    _print_field('data_finalize', release_result.data_finalize)
                _print_field('release_manifest_file', str(release_result.release_manifest_file))
    except Exception:
        if revision_path is not None:
            _remove_generated_revision_file(revision_path)
        raise
    finally:
        _cleanup_finalize_database(finalize_database)

    _print_field('finalize_validation', 'passed')
    _print_field('finalize_cleanup', 'done')
    return 0


def run_verify_command(*, ci: bool, schema_only: bool, managed_data_only: bool) -> int:  # noqa: PLR0912, PLR0915
    status = get_database_workflow_status()
    repository_inspection: WorkflowRepositoryInspection | None = None

    remark_report = remark_migration.verify_configured_database()
    _print_field('remark_verification', 'complete')
    _print_field('remark_schema_fingerprint', remark_report.get('schemaFingerprint', 'test-adapter'))
    if not managed_data_only:
        schema_drift, schema_verify = _inspect_schema_drift()
    else:
        schema_drift = 'unknown'
        schema_verify = WorkflowVerifyStepReport(step='schema', status='skipped', result='skipped')

    if not schema_only:
        repository_inspection = inspect_release_workflow(project_root=PROJECT_ROOT)

    status = replace(
        status,
        schema_drift=schema_drift,
        managed_data_drift=repository_inspection.managed_data_drift if repository_inspection else 'unknown',
        visibility_drift=repository_inspection.visibility_drift if repository_inspection else 'unknown',
        pending_release_bundle=_merge_pending_release_bundle(
            schema_drift=schema_drift,
            repository_inspection=repository_inspection,
        ),
        last_successful_action=repository_inspection.last_successful_action if repository_inspection else 'unknown',
    )

    _print_status(status)
    _print_field('workflow_command', 'verify')
    _print_field('verify_ci', _bool_text(ci))
    verify_scope = 'full'
    if schema_only:
        verify_scope = 'schema-only'
    elif managed_data_only:
        verify_scope = 'managed-data-only'
    _print_field('verify_scope', verify_scope)

    declaration_verify = (
        repository_inspection.declaration_validation
        if repository_inspection
        else WorkflowVerifyStepReport(step='declaration-validation', status='skipped', result='skipped')
    )
    artifact_validation = (
        repository_inspection.artifact_validation
        if repository_inspection
        else WorkflowVerifyStepReport(step='artifact-validation', status='skipped', result='skipped')
    )
    bundle_chain_verify = (
        repository_inspection.bundle_chain
        if repository_inspection
        else WorkflowVerifyStepReport(step='bundle-chain', status='skipped', result='skipped')
    )
    bypass_verify = (
        repository_inspection.bypass_entrypoints
        if repository_inspection
        else WorkflowVerifyStepReport(step='bypass-entrypoints', status='skipped', result='skipped')
    )

    if repository_inspection is None:
        managed_data_verify = WorkflowVerifyStepReport(step='managed-data', status='skipped', result='skipped')
        visibility_verify = WorkflowVerifyStepReport(step='visibility', status='skipped', result='skipped')
    else:
        if repository_inspection.managed_data_drift == 'clean':
            managed_data_verify = WorkflowVerifyStepReport(
                step='managed-data',
                status='success',
                result='passed',
            )
        elif repository_inspection.managed_data_drift == 'drift':
            managed_data_verify = WorkflowVerifyStepReport(
                step='managed-data',
                status='failed',
                result='drift-detected',
                error='managed data declarations are not finalized into release bundles',
                details=repository_inspection.managed_data_details,
            )
        else:
            managed_data_verify = WorkflowVerifyStepReport(
                step='managed-data',
                status='failed',
                result=repository_inspection.managed_data_drift,
                error='managed data drift could not be determined',
            )

        if repository_inspection.visibility_drift == 'clean':
            visibility_verify = WorkflowVerifyStepReport(
                step='visibility',
                status='success',
                result='passed',
            )
        elif repository_inspection.visibility_drift == 'drift':
            visibility_verify = WorkflowVerifyStepReport(
                step='visibility',
                status='failed',
                result='drift-detected',
                error='release visibility differs from the latest finalized release manifest',
                details=repository_inspection.visibility_details,
            )
        else:
            visibility_verify = WorkflowVerifyStepReport(
                step='visibility',
                status='failed',
                result=repository_inspection.visibility_drift,
                error='release visibility drift could not be determined',
            )

    _print_verify_step('declaration_verify', declaration_verify)
    if repository_inspection:
        _print_field('compiled_checksum', repository_inspection.compiled_checksum)
        _print_field('release_plan_checksum', repository_inspection.release_plan_checksum)
    _print_verify_step('artifact_validation', artifact_validation)
    _print_verify_step('schema_verify', schema_verify)
    _print_verify_step('bundle_chain_verify', bundle_chain_verify)
    _print_verify_step('bypass_verify', bypass_verify)
    _print_verify_step('managed_data_verify', managed_data_verify)
    _print_verify_step('visibility_verify', visibility_verify)

    ordered_steps = (
        declaration_verify,
        artifact_validation,
        schema_verify,
        bundle_chain_verify,
        bypass_verify,
        managed_data_verify,
        visibility_verify,
    )
    failed_step = next((report.step for report in ordered_steps if report.status == 'failed'), 'none')
    verify_result = 'failed' if failed_step != 'none' else 'passed'
    _print_field('failed_step', failed_step)
    _print_field('verify_result', verify_result)
    return 0 if verify_result == 'passed' else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Unified database workflow entrypoint')
    subparsers = parser.add_subparsers(dest='command', required=True)

    status_parser = subparsers.add_parser('status', help='Show workflow mode and target database')
    status_parser.add_argument('--format', choices=('shell', 'json'), default='shell', help='Output format')
    status_parser.set_defaults(handler=lambda args: run_status_command(output_format=args.format))

    dev_sync_parser = subparsers.add_parser('dev-sync', help='Run development sync in explicit development mode')
    dev_sync_parser.add_argument(
        '--invoked-by-startup',
        action='store_true',
        help=argparse.SUPPRESS,
    )
    dev_sync_parser.set_defaults(
        handler=lambda args: run_dev_sync_command(
            invoked_by_startup=args.invoked_by_startup,
            remark_backup_manifest=args.remark_backup_manifest,
            remark_writers_stopped=args.remark_writers_stopped,
        )
    )

    finalize_parser = subparsers.add_parser('finalize', help='Generate formal migration from current models')
    finalize_parser.add_argument('--message', required=True, help='Formal migration message')
    finalize_parser.set_defaults(handler=lambda args: run_finalize_command(message=args.message))

    deploy_parser = subparsers.add_parser('deploy', help='Apply formal Alembic migrations')
    deploy_parser.add_argument('--revision', default='head', help='Target Alembic revision')
    deploy_parser.set_defaults(
        handler=lambda args: run_deploy_command(
            revision=args.revision,
            remark_backup_manifest=args.remark_backup_manifest,
            remark_writers_stopped=args.remark_writers_stopped,
        )
    )

    for migration_parser in (dev_sync_parser, deploy_parser):
        migration_parser.add_argument(
            '--remark-backup-manifest', help='Target-bound verified backup manifest; does not create a backup'
        )
        migration_parser.add_argument(
            '--remark-writers-stopped',
            action='store_true',
            help='Operator confirms all old application/import/managed writers are stopped; does not stop them',
        )
    check_parser = subparsers.add_parser(
        'remark-migration-check', help='Read-only remark preflight and physical recovery state'
    )
    check_parser.add_argument('--report', required=True)
    check_parser.set_defaults(handler=lambda args: run_remark_check_command(report=args.report))

    verify_parser = subparsers.add_parser('verify', help='Run unified workflow verification checks')
    verify_parser.add_argument('--ci', action='store_true', help='Enable CI-oriented verification output')
    verify_scope_group = verify_parser.add_mutually_exclusive_group()
    verify_scope_group.add_argument('--schema-only', action='store_true', help='Verify schema drift only')
    verify_scope_group.add_argument(
        '--managed-data-only',
        action='store_true',
        help='Verify managed data, release visibility, bundle chain, and bypass entrypoints only',
    )
    verify_parser.set_defaults(
        handler=lambda args: run_verify_command(
            ci=args.ci,
            schema_only=args.schema_only,
            managed_data_only=args.managed_data_only,
        )
    )

    wait_db_parser = subparsers.add_parser('wait-db', help='Wait for the database to become reachable')
    wait_db_parser.add_argument(
        '--max-retries',
        type=int,
        default=int(os.environ.get('DB_WAIT_MAX_RETRIES') or '30'),
        help='Maximum number of connection attempts',
    )
    wait_db_parser.add_argument(
        '--delay',
        type=int,
        default=int(os.environ.get('DB_WAIT_DELAY') or '2'),
        help='Seconds to wait between retries',
    )
    wait_db_parser.set_defaults(
        handler=lambda args: run_wait_db_command(max_retries=args.max_retries, delay=args.delay)
    )

    bootstrap_seed_parser = subparsers.add_parser('bootstrap-seed', help='Apply bootstrap-only seed data')
    bootstrap_seed_parser.add_argument(
        '--env',
        default=os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')),
        choices=('dev', 'prod'),
        help='Bootstrap seed environment',
    )
    bootstrap_seed_parser.add_argument('--reset', action='store_true', help='Clear bootstrap data before seeding')
    bootstrap_seed_parser.set_defaults(handler=lambda args: run_bootstrap_seed_command(env=args.env, reset=args.reset))

    return parser


def main(argv: list[str] | None = None) -> int:
    os.chdir(PROJECT_ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.handler(args)
    except WorkflowCommandError as exc:
        print(f'error={exc}')
        return 1
    except CommandError as exc:
        print(f'error={exc}')
        return 1
    except (RuntimeError, ValueError) as exc:
        print(f'error={exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
