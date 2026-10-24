"""Formal release bundle deployment orchestration."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from sqlalchemy import or_, select

from config.database import AsyncSessionLocal
from module_admin.entity.do.db_workflow_do import DbWorkflowArtifactDO, DbWorkflowObjectDO
from module_admin.entity.do.role_do import RoleDO

from .capability_models import CAPABILITY_MANAGED_OBJECT_DOMAINS, LEGACY_MANAGED_OBJECT_SCOPES
from .managed_data_applier import ManagedDataApplier
from .managed_data_planner import ManagedDataManagedScope, ManagedDataOperation, ManagedDataPlan, ManagedDataPlanner
from .release_bundle_service import (
    BUNDLE_ID_PATTERN,
    compute_payload_checksum,
    load_capability_payload,
    load_managed_object_snapshot,
    load_target_state_payload,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

StepStatus = Literal['success', 'failed', 'skipped']
ArtifactType = Literal['managed-data', 'release-manifest']
DEFAULT_BOOTSTRAP_ROLES_PATH = Path(__file__).resolve().parent / 'seed_data' / 'base' / 'roles.yaml'


@dataclass(frozen=True)
class ReleaseDeployStepReport:
    """Structured deploy step report."""

    step: str
    status: StepStatus
    result: str
    applied_bundles: tuple[str, ...] = ()
    skipped_bundles: tuple[str, ...] = ()
    artifact_updates: int = 0
    error: str | None = None


@dataclass(frozen=True)
class ReleaseDeployReport:
    """Structured managed-data / release-manifest deploy report."""

    managed_data: ReleaseDeployStepReport
    release_manifest: ReleaseDeployStepReport
    postcondition_verify: ReleaseDeployStepReport
    deploy_result: Literal['success', 'failed']
    failed_step: str
    applied_bundle_ids: tuple[str, ...]
    skipped_bundle_ids: tuple[str, ...]
    compiled_checksums: tuple[str, ...] = ()
    release_plan_checksums: tuple[str, ...] = ()
    residual_objects: tuple[str, ...] = ()
    recovery_hint: str | None = None


@dataclass
class _ManagedObjectLedger:
    menu_ids: set[int] = field(default_factory=set)
    role_menu_pairs: set[tuple[int, int]] = field(default_factory=set)
    dict_type_key_by_id: dict[int, str] = field(default_factory=dict)
    dict_data_key_by_code: dict[int, tuple[str, str]] = field(default_factory=dict)
    config_key_by_id: dict[int, str] = field(default_factory=dict)

    def managed_scope(self) -> ManagedDataManagedScope:
        return ManagedDataManagedScope(
            menu_ids=frozenset(self.menu_ids),
            role_menu_pairs=frozenset(self.role_menu_pairs),
            dict_type_ids=frozenset(self.dict_type_key_by_id.keys()),
            dict_data_codes=frozenset(self.dict_data_key_by_code.keys()),
            config_ids=frozenset(self.config_key_by_id.keys()),
        )

    def advance(self, plan: ManagedDataPlan, *, role_id_to_key: dict[int, str]) -> None:
        for operation in plan.operations:
            self._advance_operation(operation, role_id_to_key=role_id_to_key)

    def _advance_operation(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        handlers = {
            'sys_menu': self._advance_menu,
            'sys_role_menu': self._advance_role_menu,
            'sys_dict_type': self._advance_dict_type,
            'sys_dict_data': self._advance_dict_data,
            'sys_config': self._advance_config,
        }
        handler = handlers.get(operation.entity_type)
        if handler is not None:
            handler(operation, role_id_to_key=role_id_to_key)

    def _advance_menu(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        del role_id_to_key
        menu_id = int(operation.match_fields['menu_id'])
        if operation.op_type == 'delete-row':
            self.menu_ids.discard(menu_id)
            return
        self.menu_ids.add(menu_id)

    def _advance_role_menu(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        pair = (int(operation.match_fields['role_id']), int(operation.match_fields['menu_id']))
        if operation.op_type == 'remove-link':
            self.role_menu_pairs.discard(pair)
            return
        if pair[0] not in role_id_to_key:
            raise ValueError(f'role_id not found for release deploy metadata sync: {pair[0]}')
        self.role_menu_pairs.add(pair)

    def _advance_dict_type(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        del role_id_to_key
        dict_id = int(operation.match_fields['dict_id'])
        if operation.op_type == 'delete-row':
            self.dict_type_key_by_id.pop(dict_id, None)
            return
        self.dict_type_key_by_id[dict_id] = str(operation.values['dict_type']).strip()

    def _advance_dict_data(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        del role_id_to_key
        dict_code = int(operation.match_fields['dict_code'])
        if operation.op_type == 'delete-row':
            self.dict_data_key_by_code.pop(dict_code, None)
            return
        self.dict_data_key_by_code[dict_code] = (
            str(operation.values['dict_type']).strip(),
            str(operation.values['dict_value']).strip(),
        )

    def _advance_config(self, operation: ManagedDataOperation, *, role_id_to_key: dict[int, str]) -> None:
        del role_id_to_key
        config_id = int(operation.match_fields['config_id'])
        if operation.op_type == 'delete-row':
            self.config_key_by_id.pop(config_id, None)
            return
        self.config_key_by_id[config_id] = str(operation.values['config_key']).strip()


@dataclass(frozen=True)
class _BundleFiles:
    bundle_id: str
    bundle_dir: Path
    bundle_payload: dict[str, Any]
    managed_data_file: Path
    managed_data_payload: dict[str, Any]
    release_manifest_file: Path
    release_manifest_payload: dict[str, Any]


def execute_release_deploy(
    *,
    output_root: str | Path | None = None,
    session_factory=AsyncSessionLocal,
    actor: str = 'db_workflow',
    bootstrap_roles_path: str | Path | None = None,
) -> ReleaseDeployReport:
    return asyncio.run(
        _execute_release_deploy_async(
            output_root=Path(output_root) if output_root else Path(__file__).resolve().parents[3] / 'db_artifacts' / 'releases',
            session_factory=session_factory,
            actor=actor,
            bootstrap_roles_path=Path(bootstrap_roles_path) if bootstrap_roles_path else DEFAULT_BOOTSTRAP_ROLES_PATH,
        )
    )


async def _execute_release_deploy_async(
    *,
    output_root: Path,
    session_factory,
    actor: str,
    bootstrap_roles_path: Path = DEFAULT_BOOTSTRAP_ROLES_PATH,
) -> ReleaseDeployReport:
    bundle_files = _discover_bundle_files(output_root)
    if not bundle_files:
        return ReleaseDeployReport(
            managed_data=ReleaseDeployStepReport(step='managed-data', status='success', result='no-op'),
            release_manifest=ReleaseDeployStepReport(step='release-manifest', status='success', result='no-op'),
            postcondition_verify=ReleaseDeployStepReport(step='postcondition-verify', status='success', result='no-op'),
            deploy_result='success',
            failed_step='none',
            applied_bundle_ids=(),
            skipped_bundle_ids=(),
        )

    ledger = _ManagedObjectLedger()
    managed_applied_bundles: list[str] = []
    managed_skipped_bundles: list[str] = []
    manifest_applied_bundles: list[str] = []
    manifest_skipped_bundles: list[str] = []
    managed_artifact_updates = 0
    manifest_artifact_updates = 0
    compiled_checksums: set[str] = set()
    release_plan_checksums: set[str] = set()

    try:
        for bundle in bundle_files:
            plan = _plan_from_payload(bundle.managed_data_payload)
            bundle_capability = _bundle_capability_metadata(bundle)
            compiled_checksums.add(bundle_capability['compiled_checksum'])
            release_plan_checksums.add(bundle_capability['release_plan_checksum'])

            async with session_factory() as session:
                role_key_to_id, role_id_to_key = await _load_role_maps(
                    session,
                    bootstrap_roles_path=bootstrap_roles_path,
                )
                if await _artifact_already_applied(
                    session,
                    bundle_id=bundle.bundle_id,
                    artifact_type='managed-data',
                    checksum=_artifact_checksum(bundle.bundle_payload, 'managed-data'),
                ):
                    managed_skipped_bundles.append(bundle.bundle_id)
                else:
                    await _apply_managed_data_bundle(
                        session=session,
                        bundle=bundle,
                        plan=plan,
                        ledger=ledger,
                        actor=actor,
                        capability_metadata=bundle_capability,
                    )
                    managed_applied_bundles.append(bundle.bundle_id)
                    managed_artifact_updates += 1

            async with session_factory() as session:
                role_key_to_id, role_id_to_key = await _load_role_maps(
                    session,
                    bootstrap_roles_path=bootstrap_roles_path,
                )
                ledger.advance(plan, role_id_to_key=role_id_to_key)
                if await _artifact_already_applied(
                    session,
                    bundle_id=bundle.bundle_id,
                    artifact_type='release-manifest',
                    checksum=_artifact_checksum(bundle.bundle_payload, 'release-manifest'),
                ):
                    manifest_skipped_bundles.append(bundle.bundle_id)
                else:
                    await _apply_release_manifest(
                        session=session,
                        bundle=bundle,
                        ledger=ledger,
                        role_key_to_id=role_key_to_id,
                        actor=actor,
                        capability_metadata=bundle_capability,
                    )
                    manifest_applied_bundles.append(bundle.bundle_id)
                    manifest_artifact_updates += 1
    except Exception as exc:
        failed_step = 'managed-data'
        if (managed_applied_bundles or managed_skipped_bundles) and (
            len(manifest_applied_bundles) < len(managed_applied_bundles) + len(managed_skipped_bundles)
        ):
            failed_step = 'release-manifest'
        return ReleaseDeployReport(
            managed_data=ReleaseDeployStepReport(
                step='managed-data',
                status='success' if failed_step != 'managed-data' else 'failed',
                result='applied' if managed_applied_bundles else 'failed',
                applied_bundles=tuple(managed_applied_bundles),
                skipped_bundles=tuple(managed_skipped_bundles),
                artifact_updates=managed_artifact_updates,
                error=str(exc) if failed_step == 'managed-data' else None,
            ),
            release_manifest=ReleaseDeployStepReport(
                step='release-manifest',
                status='failed' if failed_step == 'release-manifest' else 'skipped',
                result='failed' if failed_step == 'release-manifest' else 'skipped',
                applied_bundles=tuple(manifest_applied_bundles),
                skipped_bundles=tuple(manifest_skipped_bundles),
                artifact_updates=manifest_artifact_updates,
                error=str(exc) if failed_step == 'release-manifest' else None,
            ),
            postcondition_verify=ReleaseDeployStepReport(step='postcondition-verify', status='skipped', result='skipped'),
            deploy_result='failed',
            failed_step=failed_step,
            applied_bundle_ids=tuple(sorted({*managed_applied_bundles, *manifest_applied_bundles})),
            skipped_bundle_ids=tuple(sorted({*managed_skipped_bundles, *manifest_skipped_bundles})),
            compiled_checksums=tuple(sorted(compiled_checksums)),
            release_plan_checksums=tuple(sorted(release_plan_checksums)),
            recovery_hint=(
                'fix the failed bundle or database state, then rerun `python scripts/db.py deploy --revision head`; '
                'already successful artifacts are idempotent and will be skipped on retry'
            ),
        )

    latest_bundle = bundle_files[-1]
    async with session_factory() as session:
        role_key_to_id, _ = await _load_role_maps(
            session,
            bootstrap_roles_path=bootstrap_roles_path,
        )
        residual_objects = await _verify_release_postcondition(
            session=session,
            bundle=latest_bundle,
            role_key_to_id=role_key_to_id,
        )

    postcondition_verify = ReleaseDeployStepReport(
        step='postcondition-verify',
        status='success' if not residual_objects else 'failed',
        result='clean' if not residual_objects else 'drift-detected',
        error='deployed state drifted from finalized capability target' if residual_objects else None,
    )

    async with session_factory() as session:
        await _update_postcondition_artifact_history(
            session=session,
            bundle=latest_bundle,
            actor=actor,
            residual_objects=residual_objects,
        )
        await session.commit()

    if residual_objects:
        return ReleaseDeployReport(
            managed_data=ReleaseDeployStepReport(
                step='managed-data',
                status='success',
                result='applied' if managed_applied_bundles else 'no-op',
                applied_bundles=tuple(managed_applied_bundles),
                skipped_bundles=tuple(managed_skipped_bundles),
                artifact_updates=managed_artifact_updates,
            ),
            release_manifest=ReleaseDeployStepReport(
                step='release-manifest',
                status='success',
                result='applied' if manifest_applied_bundles else 'no-op',
                applied_bundles=tuple(manifest_applied_bundles),
                skipped_bundles=tuple(manifest_skipped_bundles),
                artifact_updates=manifest_artifact_updates,
            ),
            postcondition_verify=postcondition_verify,
            deploy_result='failed',
            failed_step='postcondition-verify',
            applied_bundle_ids=tuple(sorted({*managed_applied_bundles, *manifest_applied_bundles})),
            skipped_bundle_ids=tuple(sorted({*managed_skipped_bundles, *manifest_skipped_bundles})),
            compiled_checksums=tuple(sorted(compiled_checksums)),
            release_plan_checksums=tuple(sorted(release_plan_checksums)),
            residual_objects=residual_objects,
            recovery_hint=(
                'rerun `python scripts/db.py deploy --revision head` after correcting the drift; '
                'the latest bundle artifacts were marked failed so the deploy can replay cleanly'
            ),
        )

    return ReleaseDeployReport(
        managed_data=ReleaseDeployStepReport(
            step='managed-data',
            status='success',
            result='applied' if managed_applied_bundles else 'no-op',
            applied_bundles=tuple(managed_applied_bundles),
            skipped_bundles=tuple(managed_skipped_bundles),
            artifact_updates=managed_artifact_updates,
        ),
        release_manifest=ReleaseDeployStepReport(
            step='release-manifest',
            status='success',
            result='applied' if manifest_applied_bundles else 'no-op',
            applied_bundles=tuple(manifest_applied_bundles),
            skipped_bundles=tuple(manifest_skipped_bundles),
            artifact_updates=manifest_artifact_updates,
        ),
        postcondition_verify=postcondition_verify,
        deploy_result='success',
        failed_step='none',
        applied_bundle_ids=tuple(sorted({*managed_applied_bundles, *manifest_applied_bundles})),
        skipped_bundle_ids=tuple(sorted({*managed_skipped_bundles, *manifest_skipped_bundles})),
        compiled_checksums=tuple(sorted(compiled_checksums)),
        release_plan_checksums=tuple(sorted(release_plan_checksums)),
    )


async def _apply_managed_data_bundle(
    *,
    session: AsyncSession,
    bundle: _BundleFiles,
    plan: ManagedDataPlan,
    ledger: _ManagedObjectLedger,
    actor: str,
    capability_metadata: dict[str, Any],
) -> None:
    applier = ManagedDataApplier(session, actor=actor)
    apply_report = await applier.apply_plan(plan, dry_run=False, managed_scope=ledger.managed_scope())
    await _sync_object_metadata(
        session=session,
        bundle_id=bundle.bundle_id,
        managed_objects=load_managed_object_snapshot(
            bundle.managed_data_payload,
            artifact_name=str(bundle.managed_data_file),
        ),
    )
    await _upsert_artifact_history(
        session,
        bundle_id=bundle.bundle_id,
        artifact_type='managed-data',
        artifact_checksum=_artifact_checksum(bundle.bundle_payload, 'managed-data'),
        apply_status='success',
        applied_by=actor,
        details={
            'applied_operations': apply_report.applied_operations,
            'skipped_operations': apply_report.skipped_operations,
            'affected_objects': list(apply_report.affected_objects),
            'compiled_checksum': capability_metadata['compiled_checksum'],
            'release_plan_checksum': capability_metadata['release_plan_checksum'],
            'enabled_modules': list(capability_metadata['enabled_modules']),
        },
    )
    await session.commit()


async def _apply_release_manifest(
    *,
    session: AsyncSession,
    bundle: _BundleFiles,
    ledger: _ManagedObjectLedger,
    role_key_to_id: dict[str, int],
    actor: str,
    capability_metadata: dict[str, Any],
) -> None:
    applier = ManagedDataApplier(session, actor=actor)
    current_state = await applier.load_current_state(ledger.managed_scope())
    manifest = bundle.release_manifest_payload.get('include', {})

    missing_menu_ids = [menu_id for menu_id in manifest.get('menu_ids', []) if int(menu_id) not in current_state.menus_by_id]
    if missing_menu_ids:
        raise ValueError(f'release.manifest references missing menu_ids: {missing_menu_ids}')

    missing_dict_types = [
        dict_type for dict_type in manifest.get('dict_types', []) if str(dict_type).strip() not in current_state.dict_type_ids_by_key
    ]
    if missing_dict_types:
        raise ValueError(f'release.manifest references missing dict_types: {missing_dict_types}')

    missing_config_keys = [
        config_key for config_key in manifest.get('config_keys', []) if str(config_key).strip() not in current_state.config_ids_by_key
    ]
    if missing_config_keys:
        raise ValueError(f'release.manifest references missing config_keys: {missing_config_keys}')

    for grant in manifest.get('role_grants', []):
        role_key = str(grant.get('role_key') or '').strip()
        if role_key not in role_key_to_id:
            raise ValueError(f'release.manifest references missing role_key: {role_key}')
        role_id = role_key_to_id[role_key]
        missing_pairs = [
            (role_key, int(menu_id))
            for menu_id in grant.get('menu_ids', [])
            if (role_id, int(menu_id)) not in current_state.role_menu_pairs
        ]
        if missing_pairs:
            raise ValueError(f'release.manifest references missing role_menu grants: {missing_pairs}')

    await _upsert_artifact_history(
        session,
        bundle_id=bundle.bundle_id,
        artifact_type='release-manifest',
        artifact_checksum=_artifact_checksum(bundle.bundle_payload, 'release-manifest'),
        apply_status='success',
        applied_by=actor,
        details={
            'menu_ids': list(manifest.get('menu_ids', [])),
            'dict_types': list(manifest.get('dict_types', [])),
            'config_keys': list(manifest.get('config_keys', [])),
            'role_grants': list(manifest.get('role_grants', [])),
            'compiled_checksum': capability_metadata['compiled_checksum'],
            'release_plan_checksum': capability_metadata['release_plan_checksum'],
            'enabled_modules': list(capability_metadata['enabled_modules']),
        },
    )
    await session.commit()


async def _sync_object_metadata(
    *,
    session: AsyncSession,
    bundle_id: str,
    managed_objects: list[dict[str, Any]],
) -> None:
    desired_entries = {
        (row['object_type'], row['object_key']): row
        for row in managed_objects
    }
    existing_rows = await _load_managed_workflow_object_rows(session)
    existing_by_identity = {(row.object_type, row.object_key): row for row in existing_rows}
    now = datetime.now()

    for identity, desired in desired_entries.items():
        existing = existing_by_identity.get(identity)
        if existing is None:
            session.add(
                DbWorkflowObjectDO(
                    object_type=desired['object_type'],
                    object_key=desired['object_key'],
                    module_key=desired['module_key'],
                    object_domain=desired['object_domain'],
                    owner_scope=desired['owner_scope'],
                    last_bundle_id=bundle_id,
                    last_source_path=desired['source_path'],
                    source_checksum=desired['source_checksum'],
                    checksum=desired['checksum'],
                    active_flag='Y',
                    updated_at=now,
                )
            )
            continue

        existing.module_key = desired['module_key']
        existing.object_domain = desired['object_domain']
        existing.owner_scope = desired['owner_scope']
        existing.last_bundle_id = bundle_id
        existing.last_source_path = desired['source_path']
        existing.source_checksum = desired['source_checksum']
        existing.checksum = desired['checksum']
        existing.active_flag = 'Y'
        existing.updated_at = now

    for identity, existing in existing_by_identity.items():
        if identity in desired_entries or existing.active_flag == 'N':
            continue
        existing.active_flag = 'N'
        existing.last_bundle_id = bundle_id
        existing.updated_at = now

    await session.flush()


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


def _bundle_capability_metadata(bundle: _BundleFiles) -> dict[str, Any]:
    managed_capability = load_capability_payload(
        bundle.managed_data_payload,
        artifact_name=str(bundle.managed_data_file),
    )
    manifest_capability = load_capability_payload(
        bundle.release_manifest_payload,
        artifact_name=str(bundle.release_manifest_file),
    )
    if managed_capability != manifest_capability:
        raise ValueError(f'capability metadata mismatch between managed-data and release.manifest for {bundle.bundle_id}')
    return managed_capability


async def _verify_release_postcondition(
    *,
    session: AsyncSession,
    bundle: _BundleFiles,
    role_key_to_id: dict[str, int],
) -> tuple[str, ...]:
    target_payload = bundle.managed_data_payload.get('target_state')
    if not isinstance(target_payload, dict):
        raise ValueError(f'managed-data payload missing target_state snapshot for {bundle.bundle_id}')

    target_state = load_target_state_payload(target_payload)
    applier = ManagedDataApplier(session)
    current_state_without_scope = await applier.load_current_state()
    managed_scope = await _load_release_managed_scope_from_metadata(
        session=session,
        role_key_to_id=role_key_to_id,
        current_state=current_state_without_scope,
    )
    current_state = await applier.load_current_state(managed_scope)
    plan = ManagedDataPlanner().plan(
        current_state=current_state,
        target_state=target_state,
        role_key_to_id=role_key_to_id,
    )
    metadata_drift = await _collect_metadata_drift_objects(
        session=session,
        managed_objects=load_managed_object_snapshot(
            bundle.managed_data_payload,
            artifact_name=str(bundle.managed_data_file),
        ),
    )
    return tuple(sorted({*tuple(operation.object_key for operation in plan.operations), *metadata_drift}))


async def _load_release_managed_scope_from_metadata(
    *,
    session: AsyncSession,
    role_key_to_id: dict[str, int],
    current_state,
) -> ManagedDataManagedScope:
    rows = await _load_managed_workflow_object_rows(session)
    menu_ids: set[int] = set()
    role_menu_pairs: set[tuple[int, int]] = set()
    dict_type_ids: set[int] = set()
    dict_data_codes: set[int] = set()
    config_ids: set[int] = set()

    for row in rows:
        if row.object_type == 'sys_menu' and row.object_key.isdigit():
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


async def _collect_metadata_drift_objects(
    *,
    session: AsyncSession,
    managed_objects: list[dict[str, Any]],
) -> tuple[str, ...]:
    desired_entries = {
        (row['object_type'], row['object_key']): row
        for row in managed_objects
    }
    existing_rows = await _load_managed_workflow_object_rows(session)
    existing_by_identity = {(row.object_type, row.object_key): row for row in existing_rows}
    residual_objects: set[str] = set()

    for identity, desired in desired_entries.items():
        existing = existing_by_identity.get(identity)
        if existing is None:
            residual_objects.add(f'{identity[0]}:{identity[1]}')
            continue
        if (
            existing.active_flag != 'Y'
            or existing.module_key != desired['module_key']
            or existing.object_domain != desired['object_domain']
            or existing.owner_scope != desired['owner_scope']
            or existing.last_source_path != desired['source_path']
            or existing.source_checksum != desired['source_checksum']
            or existing.checksum != desired['checksum']
        ):
            residual_objects.add(f'{identity[0]}:{identity[1]}')

    for identity, existing in existing_by_identity.items():
        if identity in desired_entries:
            continue
        if existing.active_flag != 'N':
            residual_objects.add(f'{identity[0]}:{identity[1]}')

    return tuple(sorted(residual_objects))


async def _update_postcondition_artifact_history(
    *,
    session: AsyncSession,
    bundle: _BundleFiles,
    actor: str,
    residual_objects: tuple[str, ...],
) -> None:
    capability_metadata = _bundle_capability_metadata(bundle)
    postcondition_details = {
        'compiled_checksum': capability_metadata['compiled_checksum'],
        'release_plan_checksum': capability_metadata['release_plan_checksum'],
        'enabled_modules': list(capability_metadata['enabled_modules']),
        'postcondition_verify': {
            'status': 'clean' if not residual_objects else 'drift',
            'residual_objects': list(residual_objects),
        },
    }
    apply_status = 'success' if not residual_objects else 'failed'
    for artifact_type in ('managed-data', 'release-manifest'):
        existing = (
            await session.execute(
                select(DbWorkflowArtifactDO).where(
                    DbWorkflowArtifactDO.bundle_id == bundle.bundle_id,
                    DbWorkflowArtifactDO.artifact_type == artifact_type,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            continue
        existing.apply_status = apply_status
        existing.applied_at = datetime.now()
        existing.applied_by = actor
        existing.details_json = json.dumps(
            _merge_artifact_details(existing.details_json, postcondition_details),
            ensure_ascii=False,
            sort_keys=True,
        )
    await session.flush()


def _merge_artifact_details(existing_details_json: str | None, updates: dict[str, Any]) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if existing_details_json:
        try:
            parsed = json.loads(existing_details_json)
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            details.update(parsed)
    details.update(updates)
    return details


async def _artifact_already_applied(
    session: AsyncSession,
    *,
    bundle_id: str,
    artifact_type: ArtifactType,
    checksum: str,
) -> bool:
    existing = (
        await session.execute(
            select(DbWorkflowArtifactDO).where(
                DbWorkflowArtifactDO.bundle_id == bundle_id,
                DbWorkflowArtifactDO.artifact_type == artifact_type,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        return False
    if existing.artifact_checksum != checksum:
        raise ValueError(
            f'artifact history checksum mismatch for bundle_id={bundle_id}, artifact_type={artifact_type}'
        )
    return existing.apply_status == 'success'


async def _upsert_artifact_history(
    session: AsyncSession,
    *,
    bundle_id: str,
    artifact_type: ArtifactType,
    artifact_checksum: str,
    apply_status: str,
    applied_by: str,
    details: dict[str, Any],
) -> None:
    existing = (
        await session.execute(
            select(DbWorkflowArtifactDO).where(
                DbWorkflowArtifactDO.bundle_id == bundle_id,
                DbWorkflowArtifactDO.artifact_type == artifact_type,
            )
        )
    ).scalar_one_or_none()
    details_json = json.dumps(details, ensure_ascii=False, sort_keys=True)
    if existing is None:
        session.add(
            DbWorkflowArtifactDO(
                bundle_id=bundle_id,
                artifact_type=artifact_type,
                artifact_checksum=artifact_checksum,
                apply_status=apply_status,
                applied_at=datetime.now(),
                applied_by=applied_by,
                details_json=details_json,
            )
        )
        await session.flush()
        return

    existing.artifact_checksum = artifact_checksum
    existing.apply_status = apply_status
    existing.applied_at = datetime.now()
    existing.applied_by = applied_by
    existing.details_json = details_json
    await session.flush()


async def _load_role_maps(
    session: AsyncSession,
    *,
    bootstrap_roles_path: Path,
) -> tuple[dict[str, int], dict[int, str]]:
    rows = (await session.execute(select(RoleDO.role_key, RoleDO.role_id).where(RoleDO.del_flag != '2'))).all()
    role_key_to_id = {str(row.role_key).strip(): int(row.role_id) for row in rows if str(row.role_key or '').strip()}
    for role_key, role_id in _load_bootstrap_role_ids(bootstrap_roles_path).items():
        role_key_to_id.setdefault(role_key, role_id)
    role_id_to_key: dict[int, str] = {}
    for role_key, role_id in role_key_to_id.items():
        existing_key = role_id_to_key.get(role_id)
        if existing_key is not None and existing_key != role_key:
            raise ValueError(f'conflicting role_id mapping for bootstrap role fallback: {role_id}')
        role_id_to_key[role_id] = role_key
    return role_key_to_id, role_id_to_key


def _load_bootstrap_role_ids(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}

    payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    role_rows = payload.get('roles', [])
    if not isinstance(role_rows, list):
        raise ValueError(f'roles must be a list in {path}')

    role_key_to_id: dict[str, int] = {}
    for index, role in enumerate(role_rows):
        if not isinstance(role, dict):
            raise ValueError(f'role item must be a mapping: roles[{index}]')
        role_key = str(role.get('role_key') or '').strip()
        role_id = role.get('role_id')
        if not role_key:
            raise ValueError(f'role_key must be non-empty: roles[{index}]')
        if not isinstance(role_id, int):
            raise ValueError(f'role_id must be an integer: roles[{index}]')
        if role_key in role_key_to_id:
            raise ValueError(f'duplicate role_key in bootstrap roles: {role_key}')
        role_key_to_id[role_key] = role_id
    return role_key_to_id


def _discover_bundle_files(output_root: Path) -> list[_BundleFiles]:
    if not output_root.exists():
        return []

    bundles: list[_BundleFiles] = []
    for bundle_dir in sorted(
        [path for path in output_root.iterdir() if path.is_dir() and BUNDLE_ID_PATTERN.match(path.name)],
        key=lambda path: path.name,
    ):
        bundle_file = bundle_dir / 'bundle.yaml'
        managed_data_file = bundle_dir / 'managed-data.yaml'
        release_manifest_file = bundle_dir / 'release.manifest.yaml'
        if not bundle_file.exists():
            raise ValueError(f'missing bundle.yaml for bundle {bundle_dir.name}')
        if not managed_data_file.exists():
            raise ValueError(f'missing managed-data.yaml for bundle {bundle_dir.name}')
        if not release_manifest_file.exists():
            raise ValueError(f'missing release.manifest.yaml for bundle {bundle_dir.name}')

        bundle_payload = yaml.safe_load(bundle_file.read_text(encoding='utf-8')) or {}
        managed_data_payload = yaml.safe_load(managed_data_file.read_text(encoding='utf-8')) or {}
        release_manifest_payload = yaml.safe_load(release_manifest_file.read_text(encoding='utf-8')) or {}

        if bundle_payload.get('bundle_id') != bundle_dir.name:
            raise ValueError(f'bundle.yaml bundle_id mismatch in {bundle_file}')
        if managed_data_payload.get('bundle_id') != bundle_dir.name:
            raise ValueError(f'managed-data.yaml bundle_id mismatch in {managed_data_file}')
        if release_manifest_payload.get('bundle_id') != bundle_dir.name:
            raise ValueError(f'release.manifest.yaml bundle_id mismatch in {release_manifest_file}')

        if _artifact_checksum(bundle_payload, 'managed-data') != compute_payload_checksum(managed_data_payload):
            raise ValueError(f'managed-data.yaml checksum mismatch in {managed_data_file}')
        if _artifact_checksum(bundle_payload, 'release-manifest') != compute_payload_checksum(release_manifest_payload):
            raise ValueError(f'release.manifest.yaml checksum mismatch in {release_manifest_file}')
        load_capability_payload(managed_data_payload, artifact_name=str(managed_data_file))
        load_capability_payload(release_manifest_payload, artifact_name=str(release_manifest_file))
        load_managed_object_snapshot(managed_data_payload, artifact_name=str(managed_data_file))
        target_state_payload = managed_data_payload.get('target_state')
        if not isinstance(target_state_payload, dict):
            raise ValueError(f'managed-data.yaml missing target_state snapshot in {managed_data_file}')
        load_target_state_payload(target_state_payload)

        bundles.append(
            _BundleFiles(
                bundle_id=bundle_dir.name,
                bundle_dir=bundle_dir,
                bundle_payload=bundle_payload,
                managed_data_file=managed_data_file,
                managed_data_payload=managed_data_payload,
                release_manifest_file=release_manifest_file,
                release_manifest_payload=release_manifest_payload,
            )
        )

    return bundles


def _artifact_checksum(bundle_payload: dict[str, Any], artifact_type: ArtifactType) -> str:
    for artifact in bundle_payload.get('artifacts', []):
        if artifact.get('artifact_type') == artifact_type:
            checksum = artifact.get('checksum')
            if isinstance(checksum, str) and checksum:
                return checksum
    raise ValueError(f'bundle.yaml missing checksum for artifact_type={artifact_type}')


def _plan_from_payload(payload: dict[str, Any]) -> ManagedDataPlan:
    return ManagedDataPlan(
        operations=tuple(
            ManagedDataOperation(
                op_type=str(operation['op_type']),
                entity_type=str(operation['entity_type']),
                object_key=str(operation['object_key']),
                match_fields=dict(operation.get('match_fields') or {}),
                values=dict(operation.get('values') or {}),
            )
            for operation in payload.get('operations', [])
        )
    )
