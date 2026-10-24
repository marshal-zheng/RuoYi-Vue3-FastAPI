"""Development database sync orchestration and structured reports."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Literal

from config.database import AsyncSessionLocal
from .managed_data_fast_reconcile_service import (
    PostconditionVerificationError,
    PostconditionVerificationResult,
    PostconditionVerifier,
    compiled_checksum_for_bundle as _compiled_checksum_for_bundle,
    declaration_objects as _declaration_objects,
    elapsed_ms as _elapsed_ms,
    load_managed_data_declaration_bundle as _load_declaration_bundle,
    reconcile_managed_data as _reconcile_managed_data,
)

if TYPE_CHECKING:
    from pathlib import Path

    from config.env import DataBaseWorkflowStatus

StepStatus = Literal['success', 'failed', 'skipped']


@dataclass(frozen=True)
class DevSyncStepReport:
    """Per-step structured result."""

    step: str
    status: StepStatus
    result: str
    duration_ms: int
    error: str | None = None
    affected_objects: tuple[str, ...] = ()


@dataclass(frozen=True)
class DevSyncReport:
    """Structured development sync report."""

    workflow_mode: str
    db_target: str
    trigger: str
    risk_boundary: str
    visibility_policy: str
    compiled_checksum: str
    declaration_validation: DevSyncStepReport
    schema_sync: DevSyncStepReport
    managed_data: DevSyncStepReport
    postcondition_verify: DevSyncStepReport
    dev_sync_result: Literal['success', 'failed']
    failed_step: str
    duration_ms: int
    affected_objects: tuple[str, ...]
    residual_objects: tuple[str, ...]
    managed_data_applied_operations: int = 0
    managed_data_skipped_operations: int = 0
    metadata_updated_objects: int = 0
    metadata_deactivated_objects: int = 0

def execute_dev_sync(  # noqa: PLR0915
    *,
    project_root: Path,
    workflow_status: DataBaseWorkflowStatus,
    invoked_by_startup: bool,
    schema_apply_runner_loader,
    session_factory=AsyncSessionLocal,
) -> DevSyncReport:
    """Run declaration validation, schema sync, and managed data apply."""

    trigger = 'startup' if invoked_by_startup else 'manual'
    risk_boundary = (
        'destructive schema changes will be applied directly to the current database '
        'when dev-sync runs in development mode'
    )
    started_at = perf_counter()
    declaration_validation = _skipped_step('declaration-validation')
    schema_sync = _skipped_step('schema-sync')
    managed_data = _skipped_step('managed-data-apply')
    postcondition_verify = _skipped_step('postcondition-verify')
    compiled_checksum = ''
    managed_data_applied_operations = 0
    managed_data_skipped_operations = 0
    metadata_updated_objects = 0
    metadata_deactivated_objects = 0
    failed_step = 'none'
    affected_objects: tuple[str, ...] = ()
    residual_objects: tuple[str, ...] = ()

    try:
        declaration_started_at = perf_counter()
        declaration_bundle = _load_declaration_bundle()
        compiled_checksum = _compiled_checksum_for_bundle(declaration_bundle)
        declaration_validation = DevSyncStepReport(
            step='declaration-validation',
            status='success',
            result='validated',
            duration_ms=_elapsed_ms(declaration_started_at),
            affected_objects=_declaration_objects(declaration_bundle),
        )

        schema_started_at = perf_counter()
        runner = schema_apply_runner_loader(workflow_status.db_dev_sync_engine)
        schema_result = runner(
            project_root=project_root,
            workflow_status=workflow_status,
            invoked_by_startup=invoked_by_startup,
        )
        schema_sync = DevSyncStepReport(
            step='schema-sync',
            status='success',
            result=schema_result or 'success',
            duration_ms=_elapsed_ms(schema_started_at),
        )

        reconcile_result = asyncio.run(
            _reconcile_managed_data(
                declaration_bundle=declaration_bundle,
                session_factory=session_factory,
            )
        )
        managed_sync_result = reconcile_result.managed_sync_result
        managed_data = DevSyncStepReport(
            step='managed-data-apply',
            status='success',
            result='applied',
            duration_ms=managed_sync_result.apply_duration_ms,
            affected_objects=managed_sync_result.affected_objects,
        )
        postcondition_verify = DevSyncStepReport(
            step='postcondition-verify',
            status='success',
            result='clean',
            duration_ms=reconcile_result.postcondition_result.duration_ms,
        )
        affected_objects = managed_sync_result.affected_objects
        managed_data_applied_operations = managed_sync_result.applied_operations
        managed_data_skipped_operations = managed_sync_result.skipped_operations
        metadata_updated_objects = managed_sync_result.metadata_updated_objects
        metadata_deactivated_objects = managed_sync_result.metadata_deactivated_objects
    except PostconditionVerificationError as exc:
        managed_sync_result = exc.managed_sync_result
        managed_data = DevSyncStepReport(
            step='managed-data-apply',
            status='success',
            result='applied',
            duration_ms=managed_sync_result.apply_duration_ms,
            affected_objects=managed_sync_result.affected_objects,
        )
        postcondition_verify = DevSyncStepReport(
            step='postcondition-verify',
            status='failed',
            result='drift-detected',
            duration_ms=exc.verification_result.duration_ms,
            error=str(exc),
            affected_objects=exc.verification_result.residual_objects,
        )
        affected_objects = managed_sync_result.affected_objects
        residual_objects = exc.verification_result.residual_objects
        managed_data_applied_operations = managed_sync_result.applied_operations
        managed_data_skipped_operations = managed_sync_result.skipped_operations
        metadata_updated_objects = managed_sync_result.metadata_updated_objects
        metadata_deactivated_objects = managed_sync_result.metadata_deactivated_objects

        return DevSyncReport(
            workflow_mode=workflow_status.workflow_mode,
            db_target=workflow_status.db_target,
            trigger=trigger,
            risk_boundary=risk_boundary,
            visibility_policy='dev-full',
            compiled_checksum=compiled_checksum,
            declaration_validation=declaration_validation,
            schema_sync=schema_sync,
            managed_data=managed_data,
            postcondition_verify=postcondition_verify,
            dev_sync_result='failed',
            failed_step='postcondition-verify',
            duration_ms=_elapsed_ms(started_at),
            affected_objects=affected_objects,
            residual_objects=residual_objects,
            managed_data_applied_operations=managed_data_applied_operations,
            managed_data_skipped_operations=managed_data_skipped_operations,
            metadata_updated_objects=metadata_updated_objects,
            metadata_deactivated_objects=metadata_deactivated_objects,
        )
    except Exception as exc:
        failed_step = _resolve_failed_step(
            declaration_validation=declaration_validation,
            schema_sync=schema_sync,
            managed_data=managed_data,
            postcondition_verify=postcondition_verify,
        )
        if declaration_validation.status == 'skipped':
            declaration_validation = DevSyncStepReport(
                step='declaration-validation',
                status='failed',
                result='failed',
                duration_ms=0,
                error=str(exc),
            )
            failed_step = 'declaration-validation'
        elif schema_sync.status == 'skipped':
            schema_sync = DevSyncStepReport(
                step='schema-sync',
                status='failed',
                result='failed',
                duration_ms=0,
                error=str(exc),
            )
            failed_step = 'schema-sync'
        elif managed_data.status == 'skipped':
            managed_data = DevSyncStepReport(
                step='managed-data-apply',
                status='failed',
                result='failed',
                duration_ms=0,
                error=str(exc),
            )
            failed_step = 'managed-data-apply'
        elif postcondition_verify.status == 'skipped':
            postcondition_verify = DevSyncStepReport(
                step='postcondition-verify',
                status='failed',
                result='failed',
                duration_ms=0,
                error=str(exc),
            )
            failed_step = 'postcondition-verify'

        if not affected_objects:
            affected_objects = (
                declaration_validation.affected_objects
                or schema_sync.affected_objects
                or managed_data.affected_objects
            )
        if not residual_objects:
            residual_objects = postcondition_verify.affected_objects

        return DevSyncReport(
            workflow_mode=workflow_status.workflow_mode,
            db_target=workflow_status.db_target,
            trigger=trigger,
            risk_boundary=risk_boundary,
            visibility_policy='dev-full',
            compiled_checksum=compiled_checksum,
            declaration_validation=declaration_validation,
            schema_sync=schema_sync,
            managed_data=managed_data,
            postcondition_verify=postcondition_verify,
            dev_sync_result='failed',
            failed_step=failed_step,
            duration_ms=_elapsed_ms(started_at),
            affected_objects=affected_objects,
            residual_objects=residual_objects,
            managed_data_applied_operations=managed_data_applied_operations,
            managed_data_skipped_operations=managed_data_skipped_operations,
            metadata_updated_objects=metadata_updated_objects,
            metadata_deactivated_objects=metadata_deactivated_objects,
        )

    return DevSyncReport(
        workflow_mode=workflow_status.workflow_mode,
        db_target=workflow_status.db_target,
        trigger=trigger,
        risk_boundary=risk_boundary,
        visibility_policy='dev-full',
        compiled_checksum=compiled_checksum,
        declaration_validation=declaration_validation,
        schema_sync=schema_sync,
        managed_data=managed_data,
        postcondition_verify=postcondition_verify,
        dev_sync_result='success',
        failed_step='none',
        duration_ms=_elapsed_ms(started_at),
        affected_objects=affected_objects,
        residual_objects=residual_objects,
        managed_data_applied_operations=managed_data_applied_operations,
        managed_data_skipped_operations=managed_data_skipped_operations,
        metadata_updated_objects=metadata_updated_objects,
        metadata_deactivated_objects=metadata_deactivated_objects,
    )
def _skipped_step(step: str) -> DevSyncStepReport:
    return DevSyncStepReport(step=step, status='skipped', result='skipped', duration_ms=0)


def _resolve_failed_step(
    *,
    declaration_validation: DevSyncStepReport,
    schema_sync: DevSyncStepReport,
    managed_data: DevSyncStepReport,
    postcondition_verify: DevSyncStepReport,
) -> str:
    if declaration_validation.status == 'failed':
        return 'declaration-validation'
    if schema_sync.status == 'failed':
        return 'schema-sync'
    if managed_data.status == 'failed':
        return 'managed-data-apply'
    if postcondition_verify.status == 'failed':
        return 'postcondition-verify'
    return 'none'
