"""Development database sync orchestration and structured reports."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import TYPE_CHECKING, Literal

from sqlalchemy import or_, select

from config.database import AsyncSessionLocal
from module_admin.entity.do.db_workflow_do import DbWorkflowObjectDO
from module_admin.entity.do.role_do import RoleDO

from .capability_models import (
    CAPABILITY_MANAGED_OBJECT_DOMAINS,
    LEGACY_MANAGED_OBJECT_SCOPES,
)
from .managed_data_applier import ManagedDataApplier
from .managed_data_declaration_loader import (
    ManagedDataDeclarationBundle,
    ManagedDataDeclarationLoader,
)
from .managed_data_planner import ManagedDataManagedScope, ManagedDataPlanner
from .release_bundle_service import compute_payload_checksum

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

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


@dataclass(frozen=True)
class _MetadataSyncCounts:
    updated_objects: int
    deactivated_objects: int


@dataclass(frozen=True)
class PostconditionVerificationResult:
    """Planner replay plus metadata drift check after dev-sync apply."""

    duration_ms: int
    pending_operation_objects: tuple[str, ...] = ()
    metadata_drift_objects: tuple[str, ...] = ()
    residual_objects: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.residual_objects


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


def _load_declaration_bundle() -> ManagedDataDeclarationBundle:
    return ManagedDataDeclarationLoader().load()


async def _reconcile_managed_data(
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
    session_factory,
):
    async with session_factory() as session:
        async with session.begin():
            applier = ManagedDataApplier(session)
            role_key_to_id = await _load_role_key_to_id(session)
            current_state_without_metadata = await applier.load_current_state()
            managed_scope = await _load_managed_scope_from_metadata(
                session,
                role_key_to_id=role_key_to_id,
                current_state=current_state_without_metadata,
            )
            current_state = await applier.load_current_state(managed_scope)
            plan = ManagedDataPlanner().plan(
                current_state=current_state,
                target_state=declaration_bundle.dev_target_state,
                role_key_to_id=role_key_to_id,
            )
            apply_started_at = perf_counter()
            apply_report = await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)
            metadata_counts = await _sync_workflow_object_metadata(
                session,
                declaration_bundle=declaration_bundle,
            )
            managed_sync_result = _ManagedDataSyncRuntimeResult(
                affected_objects=apply_report.affected_objects,
                applied_operations=apply_report.applied_operations,
                skipped_operations=apply_report.skipped_operations,
                metadata_updated_objects=metadata_counts.updated_objects,
                metadata_deactivated_objects=metadata_counts.deactivated_objects,
                apply_duration_ms=_elapsed_ms(apply_started_at),
            )
            postcondition_result = await PostconditionVerifier(session).verify(
                declaration_bundle=declaration_bundle,
                role_key_to_id=role_key_to_id,
            )
            if not postcondition_result.is_clean:
                await session.rollback()
                raise PostconditionVerificationError(
                    verification_result=postcondition_result,
                    managed_sync_result=managed_sync_result,
                )

        return _ManagedDataReconcileRuntimeResult(
            managed_sync_result=managed_sync_result,
            postcondition_result=postcondition_result,
        )


@dataclass(frozen=True)
class _ManagedDataSyncRuntimeResult:
    affected_objects: tuple[str, ...]
    applied_operations: int
    skipped_operations: int
    metadata_updated_objects: int
    metadata_deactivated_objects: int
    apply_duration_ms: int


@dataclass(frozen=True)
class _ManagedDataReconcileRuntimeResult:
    managed_sync_result: _ManagedDataSyncRuntimeResult
    postcondition_result: PostconditionVerificationResult


class PostconditionVerificationError(RuntimeError):
    """Raised when post-apply state still diverges from the target capability state."""

    def __init__(
        self,
        *,
        verification_result: PostconditionVerificationResult,
        managed_sync_result: _ManagedDataSyncRuntimeResult,
    ) -> None:
        self.verification_result = verification_result
        self.managed_sync_result = managed_sync_result

        drift_parts: list[str] = []
        if verification_result.pending_operation_objects:
            drift_parts.append(f'pending_operations={len(verification_result.pending_operation_objects)}')
        if verification_result.metadata_drift_objects:
            drift_parts.append(f'metadata_drift={len(verification_result.metadata_drift_objects)}')
        super().__init__(
            'postcondition verification failed'
            + (f': {", ".join(drift_parts)}' if drift_parts else '')
        )


class PostconditionVerifier:
    """Re-plan the current database state and validate workflow metadata after apply."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def verify(
        self,
        *,
        declaration_bundle: ManagedDataDeclarationBundle,
        role_key_to_id: dict[str, int],
    ) -> PostconditionVerificationResult:
        started_at = perf_counter()
        applier = ManagedDataApplier(self.session)
        current_state_without_metadata = await applier.load_current_state()
        managed_scope = await _load_managed_scope_from_metadata(
            self.session,
            role_key_to_id=role_key_to_id,
            current_state=current_state_without_metadata,
        )
        current_state = await applier.load_current_state(managed_scope)
        role_id_to_key = {role_id: role_key for role_key, role_id in role_key_to_id.items()}
        pending_operation_objects = tuple(
            _normalize_residual_object_key(
                operation=operation,
                current_state=current_state,
                role_id_to_key=role_id_to_key,
            )
            for operation in ManagedDataPlanner().plan(
                current_state=current_state,
                target_state=declaration_bundle.dev_target_state,
                role_key_to_id=role_key_to_id,
            ).operations
        )
        metadata_drift_objects = await _collect_metadata_drift_objects(
            self.session,
            desired_entries=_build_desired_object_entries(declaration_bundle=declaration_bundle),
        )
        residual_objects = tuple(sorted({*pending_operation_objects, *metadata_drift_objects}))
        return PostconditionVerificationResult(
            duration_ms=_elapsed_ms(started_at),
            pending_operation_objects=pending_operation_objects,
            metadata_drift_objects=metadata_drift_objects,
            residual_objects=residual_objects,
        )


async def _load_role_key_to_id(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(select(RoleDO.role_key, RoleDO.role_id).where(RoleDO.del_flag != '2'))
    return {
        str(row.role_key).strip(): int(row.role_id)
        for row in rows.all()
        if str(row.role_key or '').strip()
    }


async def _load_managed_scope_from_metadata(
    session: AsyncSession,
    *,
    role_key_to_id: dict[str, int],
    current_state,
) -> ManagedDataManagedScope:
    rows = (
        await session.execute(
            select(DbWorkflowObjectDO).where(
                DbWorkflowObjectDO.active_flag == 'Y',
                or_(
                    DbWorkflowObjectDO.object_domain.in_(CAPABILITY_MANAGED_OBJECT_DOMAINS),
                    DbWorkflowObjectDO.owner_scope.in_(LEGACY_MANAGED_OBJECT_SCOPES),
                ),
            )
        )
    ).scalars().all()

    menu_ids: set[int] = set()
    role_menu_pairs: set[tuple[int, int]] = set()
    dict_type_ids: set[int] = set()
    dict_data_codes: set[int] = set()
    config_ids: set[int] = set()

    for row in rows:
        if row.object_type == 'sys_menu':
            if row.object_key.isdigit():
                menu_ids.add(int(row.object_key))
        elif row.object_type == 'sys_role_menu':
            role_key, _, menu_id_text = row.object_key.partition(':')
            if role_key in role_key_to_id and menu_id_text.isdigit():
                role_menu_pairs.add((role_key_to_id[role_key], int(menu_id_text)))
        elif row.object_type == 'sys_dict_type':
            dict_id = current_state.dict_type_ids_by_key.get(row.object_key)
            if dict_id is not None:
                dict_type_ids.add(int(dict_id))
        elif row.object_type == 'sys_dict_data':
            dict_type, _, dict_value = row.object_key.partition(':')
            dict_code = current_state.dict_data_codes_by_business_key.get((dict_type, dict_value))
            if dict_code is not None:
                dict_data_codes.add(int(dict_code))
        elif row.object_type == 'sys_config':
            config_id = current_state.config_ids_by_key.get(row.object_key)
            if config_id is not None:
                config_ids.add(int(config_id))
    return ManagedDataManagedScope(
        menu_ids=frozenset(menu_ids),
        role_menu_pairs=frozenset(role_menu_pairs),
        dict_type_ids=frozenset(dict_type_ids),
        dict_data_codes=frozenset(dict_data_codes),
        config_ids=frozenset(config_ids),
    )


async def _sync_workflow_object_metadata(
    session: AsyncSession,
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
) -> _MetadataSyncCounts:
    desired_entries = _build_desired_object_entries(declaration_bundle=declaration_bundle)
    existing_rows = await _load_managed_workflow_object_rows(session)
    existing_by_identity = {(row.object_type, row.object_key): row for row in existing_rows}
    now = datetime.now()
    updated_objects = 0
    deactivated_objects = 0

    for identity, desired in desired_entries.items():
        existing = existing_by_identity.get(identity)
        if existing is None:
            session.add(
                DbWorkflowObjectDO(
                    object_type=identity[0],
                    object_key=identity[1],
                    module_key=desired['module_key'],
                    object_domain=desired['object_domain'],
                    owner_scope=desired['owner_scope'],
                    last_bundle_id='dev-sync',
                    last_source_path=desired['last_source_path'],
                    source_checksum=desired['source_checksum'],
                    checksum=desired['checksum'],
                    active_flag='Y',
                    updated_at=now,
                )
            )
            updated_objects += 1
            continue

        changed = (
            existing.module_key != desired['module_key']
            or existing.object_domain != desired['object_domain']
            or existing.owner_scope != desired['owner_scope']
            or existing.last_bundle_id != 'dev-sync'
            or existing.last_source_path != desired['last_source_path']
            or existing.source_checksum != desired['source_checksum']
            or existing.checksum != desired['checksum']
            or existing.active_flag != 'Y'
        )
        if changed:
            existing.module_key = desired['module_key']
            existing.object_domain = desired['object_domain']
            existing.owner_scope = desired['owner_scope']
            existing.last_bundle_id = 'dev-sync'
            existing.last_source_path = desired['last_source_path']
            existing.source_checksum = desired['source_checksum']
            existing.checksum = desired['checksum']
            existing.active_flag = 'Y'
            existing.updated_at = now
            updated_objects += 1

    for identity, existing in existing_by_identity.items():
        if identity in desired_entries or existing.active_flag == 'N':
            continue
        existing.active_flag = 'N'
        existing.last_bundle_id = 'dev-sync'
        existing.updated_at = now
        deactivated_objects += 1

    await session.flush()
    return _MetadataSyncCounts(updated_objects=updated_objects, deactivated_objects=deactivated_objects)


def _build_desired_object_entries(
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
) -> dict[tuple[str, str], dict[str, str]]:
    entries: dict[tuple[str, str], dict[str, str]] = {}
    compiled_state = _require_compiled_capability_state(declaration_bundle)

    for module_key, declaration in compiled_state.modules.items():
        source_path = str(declaration.source_path)
        for menu_id, row in declaration.resources.menus.items():
            checksum = compute_payload_checksum(row)
            entries[('sys_menu', str(menu_id))] = {
                'module_key': module_key,
                'object_domain': 'menus',
                'owner_scope': 'menus',
                'last_source_path': source_path,
                'source_checksum': checksum,
                'checksum': checksum,
            }

        for role_key, menu_ids in declaration.resources.role_grants.items():
            for menu_id in menu_ids:
                payload = {'role_key': role_key, 'menu_id': menu_id}
                checksum = compute_payload_checksum(payload)
                entries[('sys_role_menu', f'{role_key}:{menu_id}')] = {
                    'module_key': module_key,
                    'object_domain': 'role_grants',
                    'owner_scope': 'role_grants',
                    'last_source_path': source_path,
                    'source_checksum': checksum,
                    'checksum': checksum,
                }

        for dict_type, row in declaration.resources.dict_types.items():
            checksum = compute_payload_checksum(row)
            entries[('sys_dict_type', dict_type)] = {
                'module_key': module_key,
                'object_domain': 'dict_types',
                'owner_scope': 'dict_types',
                'last_source_path': source_path,
                'source_checksum': checksum,
                'checksum': checksum,
            }

        for (dict_type, dict_value), row in declaration.resources.dict_data.items():
            checksum = compute_payload_checksum(row)
            entries[('sys_dict_data', f'{dict_type}:{dict_value}')] = {
                'module_key': module_key,
                'object_domain': 'dict_data',
                'owner_scope': 'dict_data',
                'last_source_path': source_path,
                'source_checksum': checksum,
                'checksum': checksum,
            }

        for config_key, row in declaration.resources.configs.items():
            checksum = compute_payload_checksum(row)
            entries[('sys_config', config_key)] = {
                'module_key': module_key,
                'object_domain': 'configs',
                'owner_scope': 'configs',
                'last_source_path': source_path,
                'source_checksum': checksum,
                'checksum': checksum,
            }

    return entries


def _compiled_checksum_for_bundle(bundle: ManagedDataDeclarationBundle) -> str:
    compiled_state = _require_compiled_capability_state(bundle)
    if compiled_state.checksums is None:
        return ''
    return compiled_state.checksums.compiled_checksum


def _require_compiled_capability_state(bundle: ManagedDataDeclarationBundle):
    compiled_state = bundle.compiled_capability_state
    if compiled_state is None:
        raise ValueError('compiled capability state is required for dev-sync')
    return compiled_state


async def _load_managed_workflow_object_rows(session: AsyncSession) -> list[DbWorkflowObjectDO]:
    return (
        await session.execute(
            select(DbWorkflowObjectDO).where(
                or_(
                    DbWorkflowObjectDO.object_domain.in_(CAPABILITY_MANAGED_OBJECT_DOMAINS),
                    DbWorkflowObjectDO.owner_scope.in_(LEGACY_MANAGED_OBJECT_SCOPES),
                )
            )
        )
    ).scalars().all()


async def _collect_metadata_drift_objects(
    session: AsyncSession,
    *,
    desired_entries: dict[tuple[str, str], dict[str, str]],
) -> tuple[str, ...]:
    existing_rows = await _load_managed_workflow_object_rows(session)
    existing_by_identity = {(row.object_type, row.object_key): row for row in existing_rows}
    drift_objects: set[str] = set()

    for identity, desired in desired_entries.items():
        existing = existing_by_identity.get(identity)
        if existing is None:
            drift_objects.add(_format_metadata_identity(identity))
            continue

        if (
            existing.active_flag != 'Y'
            or existing.module_key != desired['module_key']
            or existing.object_domain != desired['object_domain']
            or existing.owner_scope != desired['owner_scope']
            or existing.last_bundle_id != 'dev-sync'
            or existing.last_source_path != desired['last_source_path']
            or existing.source_checksum != desired['source_checksum']
            or existing.checksum != desired['checksum']
        ):
            drift_objects.add(_format_metadata_identity(identity))

    for identity, existing in existing_by_identity.items():
        if identity in desired_entries:
            continue
        if existing.active_flag != 'N':
            drift_objects.add(_format_metadata_identity(identity))

    return tuple(sorted(drift_objects))


def _format_metadata_identity(identity: tuple[str, str]) -> str:
    return f'{identity[0]}:{identity[1]}'


def _normalize_residual_object_key(
    *,
    operation,
    current_state,
    role_id_to_key: dict[int, str],
) -> str:
    entity_type = operation.entity_type
    if entity_type == 'sys_menu':
        menu_id = int(operation.values.get('menu_id') or operation.match_fields['menu_id'])
        return f'sys_menu:{menu_id}'
    if entity_type == 'sys_role_menu':
        role_id = int(operation.values.get('role_id') or operation.match_fields['role_id'])
        menu_id = int(operation.values.get('menu_id') or operation.match_fields['menu_id'])
        role_key = role_id_to_key.get(role_id, str(role_id))
        return f'sys_role_menu:{role_key}:{menu_id}'
    if entity_type == 'sys_dict_type':
        dict_type = str(
            operation.values.get('dict_type')
            or current_state.dict_types_by_id.get(int(operation.match_fields['dict_id']), {}).get('dict_type')
            or operation.match_fields['dict_id']
        )
        return f'sys_dict_type:{dict_type}'
    if entity_type == 'sys_dict_data':
        dict_type = str(
            operation.values.get('dict_type')
            or current_state.dict_data_by_code.get(int(operation.match_fields['dict_code']), {}).get('dict_type')
            or operation.match_fields['dict_code']
        )
        dict_value = str(
            operation.values.get('dict_value')
            or current_state.dict_data_by_code.get(int(operation.match_fields['dict_code']), {}).get('dict_value')
            or operation.match_fields['dict_code']
        )
        return f'sys_dict_data:{dict_type}:{dict_value}'
    if entity_type == 'sys_config':
        config_key = str(
            operation.values.get('config_key')
            or current_state.configs_by_id.get(int(operation.match_fields['config_id']), {}).get('config_key')
            or operation.match_fields['config_id']
        )
        return f'sys_config:{config_key}'
    return operation.object_key


def _declaration_objects(bundle: ManagedDataDeclarationBundle) -> tuple[str, ...]:
    target_state = bundle.dev_target_state
    return tuple(
        sorted(
            [
                *[f'sys_menu:{menu_id}' for menu_id in target_state.menus],
                *[
                    f'sys_role_menu:{role_key}:{menu_id}'
                    for role_key, menu_ids in sorted(target_state.role_grants.items())
                    for menu_id in menu_ids
                ],
                *[f'sys_dict_type:{dict_type}' for dict_type in sorted(target_state.dict_types)],
                *[
                    f'sys_dict_data:{dict_type}:{dict_value}'
                    for dict_type, dict_value in sorted(target_state.dict_data)
                ],
                *[f'sys_config:{config_key}' for config_key in sorted(target_state.configs)],
            ]
        )
    )


def _skipped_step(step: str) -> DevSyncStepReport:
    return DevSyncStepReport(step=step, status='skipped', result='skipped', duration_ms=0)


def _elapsed_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)


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
