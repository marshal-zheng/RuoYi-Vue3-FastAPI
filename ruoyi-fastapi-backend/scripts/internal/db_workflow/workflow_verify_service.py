"""Workflow status/verify analysis for managed data, bundles, and bypass entrypoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.database import AsyncSessionLocal, Base
from module_admin.entity.do.config_do import ConfigDO  # noqa: F401
from module_admin.entity.do.db_workflow_do import DbWorkflowArtifactDO, DbWorkflowObjectDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO  # noqa: F401
from module_admin.entity.do.menu_do import MenuDO  # noqa: F401
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO  # noqa: F401

from .deploy_release_service import _execute_release_deploy_async, _load_role_maps
from .finalize_release_service import (
    _advance_managed_scope,
    _load_managed_data_plan,
    _release_manifest_snapshot,
)
from .managed_data_applier import ManagedDataApplier
from .managed_data_declaration_loader import ManagedDataDeclarationBundle, ManagedDataDeclarationLoader
from .managed_data_planner import ManagedDataManagedScope, ManagedDataPlanner
from .release_bundle_service import (
    BUNDLE_ID_PATTERN,
    RELEASE_MANIFEST_FILENAME,
    build_managed_object_snapshot,
    load_capability_payload,
    load_managed_object_snapshot,
    load_target_state_payload,
)

StepStatus = Literal['success', 'failed', 'skipped']
DriftStatus = Literal['clean', 'drift', 'invalid', 'unknown']
PendingReleaseBundleStatus = Literal['required', 'none', 'unknown']


@dataclass(frozen=True)
class WorkflowVerifyStepReport:
    """Structured verification step result."""

    step: str
    status: StepStatus
    result: str
    error: str | None = None
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowRepositoryInspection:
    """Release artifact and managed declaration inspection outcome."""

    declaration_validation: WorkflowVerifyStepReport
    artifact_validation: WorkflowVerifyStepReport
    bundle_chain: WorkflowVerifyStepReport
    bypass_entrypoints: WorkflowVerifyStepReport
    compiled_checksum: str
    release_plan_checksum: str
    managed_data_drift: DriftStatus
    managed_data_details: tuple[str, ...]
    visibility_drift: DriftStatus
    visibility_details: tuple[str, ...]
    pending_release_bundle: PendingReleaseBundleStatus
    last_successful_action: str


def inspect_release_workflow(
    *,
    project_root: Path,
    output_root: str | Path | None = None,
    seed_data_dir: str | Path | None = None,
    session_factory=AsyncSessionLocal,
) -> WorkflowRepositoryInspection:
    """Inspect declaration validity, bundle replay, visibility drift, and bypass entrypoints."""

    return asyncio.run(
        _inspect_release_workflow_async(
            project_root=project_root,
            output_root=Path(output_root) if output_root else project_root / 'db_artifacts' / 'releases',
            seed_data_dir=Path(seed_data_dir) if seed_data_dir else project_root / 'scripts' / 'seed_data',
            session_factory=session_factory,
        )
    )


async def _inspect_release_workflow_async(
    *,
    project_root: Path,
    output_root: Path,
    seed_data_dir: Path,
    session_factory,
) -> WorkflowRepositoryInspection:
    last_successful_action = await _load_last_successful_action_async(session_factory)
    bypass_entrypoints = _check_bypass_entrypoints(project_root)

    try:
        declaration_bundle = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).load()
    except Exception as exc:
        return WorkflowRepositoryInspection(
            declaration_validation=WorkflowVerifyStepReport(
                step='declaration-validation',
                status='failed',
                result='invalid',
                error=str(exc),
                details=(str(seed_data_dir),),
            ),
            artifact_validation=_skipped_step('artifact-validation'),
            bundle_chain=_skipped_step('bundle-chain'),
            bypass_entrypoints=bypass_entrypoints,
            compiled_checksum='',
            release_plan_checksum='',
            managed_data_drift='invalid',
            managed_data_details=(),
            visibility_drift='invalid',
            visibility_details=(),
            pending_release_bundle='unknown',
            last_successful_action=last_successful_action,
        )

    declaration_validation = WorkflowVerifyStepReport(
        step='declaration-validation',
        status='success',
        result='validated',
        details=_declaration_objects(declaration_bundle),
    )

    try:
        (
            artifact_validation,
            bundle_chain,
            managed_data_drift,
            managed_data_details,
            visibility_drift,
            visibility_details,
        ) = await _analyze_release_drift_async(
            output_root=output_root,
            declaration_bundle=declaration_bundle,
        )
    except Exception as exc:
        artifact_validation = WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='failed',
            error=str(exc),
            details=(str(output_root),),
        )
        bundle_chain = WorkflowVerifyStepReport(
            step='bundle-chain',
            status='failed',
            result='failed',
            error=str(exc),
            details=(str(output_root),),
        )
        managed_data_drift = 'invalid'
        managed_data_details = ()
        visibility_drift = 'invalid'
        visibility_details = ()

    pending_release_bundle = _derive_pending_release_bundle(
        managed_data_drift=managed_data_drift,
        visibility_drift=visibility_drift,
    )

    return WorkflowRepositoryInspection(
        declaration_validation=declaration_validation,
        artifact_validation=artifact_validation,
        bundle_chain=bundle_chain,
        bypass_entrypoints=bypass_entrypoints,
        compiled_checksum=declaration_bundle.release_selection.compiled_checksum,
        release_plan_checksum=declaration_bundle.release_selection.release_plan_checksum,
        managed_data_drift=managed_data_drift,
        managed_data_details=managed_data_details,
        visibility_drift=visibility_drift,
        visibility_details=visibility_details,
        pending_release_bundle=pending_release_bundle,
        last_successful_action=last_successful_action,
    )


async def _analyze_release_drift_async(
    *,
    output_root: Path,
    declaration_bundle: ManagedDataDeclarationBundle,
) -> tuple[
    WorkflowVerifyStepReport,
    WorkflowVerifyStepReport,
    DriftStatus,
    tuple[str, ...],
    DriftStatus,
    tuple[str, ...],
]:
    formal_target_state = declaration_bundle.formal_candidate_state
    desired_manifest_snapshot = _release_manifest_snapshot(
        formal_target_state,
        declaration_bundle.release_selection,
    )
    latest_manifest_snapshot, latest_manifest_path = _load_latest_release_manifest_snapshot_with_path(output_root)
    bundle_dirs = _list_bundle_dirs(output_root)
    artifact_validation = _validate_latest_bundle_payload(
        output_root=output_root,
        declaration_bundle=declaration_bundle,
        formal_target_state=formal_target_state,
        desired_manifest_snapshot=desired_manifest_snapshot,
    )

    with TemporaryDirectory(prefix='workflow-verify-') as temp_dir:
        database_path = Path(temp_dir) / 'release_bundle_replay.sqlite3'
        engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}', future=True)
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

            deploy_report = await _execute_release_deploy_async(
                output_root=output_root,
                session_factory=session_factory,
                actor='workflow_verify',
                bootstrap_roles_path=declaration_bundle.paths.bootstrap_roles,
            )
            if deploy_report.deploy_result != 'success':
                raise ValueError(
                    deploy_report.managed_data.error
                    or deploy_report.release_manifest.error
                    or 'release bundle replay failed'
                )

            async with session_factory() as session:
                role_key_to_id, _ = await _load_role_maps(
                    session,
                    bootstrap_roles_path=declaration_bundle.paths.bootstrap_roles,
                )
                current_state = await ManagedDataApplier(session).load_current_state(
                    _build_release_managed_scope(output_root)
                )
                plan = ManagedDataPlanner().plan(
                    current_state=current_state,
                    target_state=formal_target_state,
                    role_key_to_id=role_key_to_id,
                )
        finally:
            await engine.dispose()

    bundle_chain = WorkflowVerifyStepReport(
        step='bundle-chain',
        status='success',
        result='replayed' if bundle_dirs else 'no-op',
        details=tuple(bundle_dir.name for bundle_dir in bundle_dirs),
    )

    managed_data_drift: DriftStatus = 'drift' if plan.operation_count > 0 else 'clean'
    managed_data_details = tuple(operation.object_key for operation in plan.operations)

    visibility_drift: DriftStatus
    if latest_manifest_snapshot is None:
        visibility_drift = 'drift' if _has_release_visibility_content(formal_target_state) else 'clean'
    else:
        visibility_drift = 'drift' if latest_manifest_snapshot != desired_manifest_snapshot else 'clean'

    visibility_details: tuple[str, ...] = ()
    if visibility_drift == 'drift':
        visibility_details = (
            str(declaration_bundle.paths.release_plan),
            *((str(latest_manifest_path),) if latest_manifest_path else ()),
        )

    return (
        artifact_validation,
        bundle_chain,
        managed_data_drift,
        managed_data_details,
        visibility_drift,
        visibility_details,
    )


def _validate_latest_bundle_payload(  # noqa: PLR0911
    *,
    output_root: Path,
    declaration_bundle: ManagedDataDeclarationBundle,
    formal_target_state,
    desired_manifest_snapshot: dict,
) -> WorkflowVerifyStepReport:
    bundle_dirs = _list_bundle_dirs(output_root)
    if not bundle_dirs:
        return WorkflowVerifyStepReport(step='artifact-validation', status='success', result='no-op')

    latest_bundle_dir = bundle_dirs[-1]
    managed_data_path = latest_bundle_dir / 'managed-data.yaml'
    release_manifest_path = latest_bundle_dir / RELEASE_MANIFEST_FILENAME
    managed_data_payload = yaml.safe_load(managed_data_path.read_text(encoding='utf-8')) or {}
    release_manifest_payload = yaml.safe_load(release_manifest_path.read_text(encoding='utf-8')) or {}

    managed_capability = load_capability_payload(managed_data_payload, artifact_name=str(managed_data_path))
    manifest_capability = load_capability_payload(release_manifest_payload, artifact_name=str(release_manifest_path))
    if managed_capability != manifest_capability:
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='capability-mismatch',
            error='managed-data.yaml and release.manifest.yaml capability metadata differ',
            details=(str(managed_data_path), str(release_manifest_path)),
        )

    if managed_capability['compiled_checksum'] != declaration_bundle.release_selection.compiled_checksum:
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='compiled-checksum-drift',
            error='latest bundle compiled_checksum differs from current declarations',
            details=(str(managed_data_path), declaration_bundle.release_selection.compiled_checksum),
        )

    if managed_capability['release_plan_checksum'] != declaration_bundle.release_selection.release_plan_checksum:
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='release-plan-checksum-drift',
            error='latest bundle release_plan_checksum differs from current release-plan',
            details=(str(release_manifest_path), declaration_bundle.release_selection.release_plan_checksum),
        )

    target_state_payload = managed_data_payload.get('target_state')
    if (
        not isinstance(target_state_payload, dict)
        or load_target_state_payload(target_state_payload) != formal_target_state
    ):
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='target-state-drift',
            error='managed-data target_state snapshot differs from current formal candidate state',
            details=(str(managed_data_path),),
        )

    compiled_state = declaration_bundle.compiled_capability_state
    if compiled_state is None:
        raise ValueError('compiled capability state is required for workflow verify')
    expected_managed_objects = build_managed_object_snapshot(
        compiled_state=compiled_state,
        enabled_modules=declaration_bundle.release_selection.enabled_modules,
    )
    if (
        load_managed_object_snapshot(managed_data_payload, artifact_name=str(managed_data_path))
        != expected_managed_objects
    ):
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='managed-object-drift',
            error='managed-data managed_objects snapshot differs from current capability ownership',
            details=(str(managed_data_path),),
        )

    manifest_snapshot = dict(release_manifest_payload)
    manifest_snapshot.pop('bundle_id', None)
    if manifest_snapshot != desired_manifest_snapshot:
        return WorkflowVerifyStepReport(
            step='artifact-validation',
            status='failed',
            result='release-manifest-drift',
            error='latest release.manifest.yaml differs from current formal candidate state',
            details=(str(release_manifest_path),),
        )

    return WorkflowVerifyStepReport(
        step='artifact-validation',
        status='success',
        result='validated',
        details=(str(latest_bundle_dir),),
    )


def _build_release_managed_scope(output_root: Path) -> ManagedDataManagedScope:
    managed_scope = ManagedDataManagedScope()
    for bundle_dir in _list_bundle_dirs(output_root):
        managed_data_file = bundle_dir / 'managed-data.yaml'
        if not managed_data_file.exists():
            continue
        managed_scope = _advance_managed_scope(managed_scope, _load_managed_data_plan(managed_data_file))
    return managed_scope


def _load_latest_release_manifest_snapshot_with_path(output_root: Path) -> tuple[dict | None, Path | None]:
    for bundle_dir in reversed(_list_bundle_dirs(output_root)):
        manifest_path = bundle_dir / RELEASE_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        payload = yaml.safe_load(manifest_path.read_text(encoding='utf-8')) or {}
        if isinstance(payload, dict):
            payload.pop('bundle_id', None)
            return payload, manifest_path
    return None, None


def _list_bundle_dirs(output_root: Path) -> list[Path]:
    if not output_root.exists():
        return []
    return sorted(
        [path for path in output_root.iterdir() if path.is_dir() and BUNDLE_ID_PATTERN.match(path.name)],
        key=lambda path: path.name,
    )


def _has_release_visibility_content(target_state) -> bool:
    return bool(
        target_state.menus
        or target_state.role_grants
        or target_state.dict_types
        or target_state.dict_data
        or target_state.configs
    )


def _derive_pending_release_bundle(
    *,
    managed_data_drift: DriftStatus,
    visibility_drift: DriftStatus,
) -> PendingReleaseBundleStatus:
    if managed_data_drift == 'drift' or visibility_drift == 'drift':
        return 'required'
    if managed_data_drift == 'clean' and visibility_drift == 'clean':
        return 'none'
    return 'unknown'


async def _load_last_successful_action_async(session_factory) -> str:
    try:
        async with session_factory() as session:
            latest_deploy = (
                (
                    await session.execute(
                        select(DbWorkflowArtifactDO)
                        .where(DbWorkflowArtifactDO.apply_status == 'success')
                        .order_by(DbWorkflowArtifactDO.applied_at.desc(), DbWorkflowArtifactDO.artifact_id.desc())
                    )
                )
                .scalars()
                .first()
            )
            latest_dev_sync = (
                (
                    await session.execute(
                        select(DbWorkflowObjectDO)
                        .where(DbWorkflowObjectDO.last_bundle_id == 'dev-sync')
                        .order_by(DbWorkflowObjectDO.updated_at.desc(), DbWorkflowObjectDO.object_id.desc())
                    )
                )
                .scalars()
                .first()
            )
    except Exception:
        return 'unknown'

    deploy_time = latest_deploy.applied_at if latest_deploy else None
    dev_sync_time = latest_dev_sync.updated_at if latest_dev_sync else None

    if deploy_time is None and dev_sync_time is None:
        return 'unknown'
    if deploy_time is not None and (dev_sync_time is None or deploy_time >= dev_sync_time):
        return 'deploy'
    return 'dev-sync'


def _check_bypass_entrypoints(backend_root: Path) -> WorkflowVerifyStepReport:
    repository_root = backend_root.parent
    checks = (
        (
            repository_root / 'scripts' / 'start.sh',
            ('python scripts/db.py status', 'dev-sync', 'deploy'),
            ('apply_sql_updates',),
        ),
        (
            backend_root / 'docker-entrypoint.sh',
            ('python scripts/db.py deploy --revision head', 'python scripts/db.py bootstrap-seed'),
            (),
        ),
        (
            backend_root / 'server.py',
            ('app.state.dev_menu_sync_runtime = None',),
            ('DevMenuSyncRuntime(', 'trigger_sync('),
        ),
    )

    issues: list[str] = []
    for path, required_patterns, forbidden_patterns in checks:
        if not path.exists():
            issues.append(f'missing:{path}')
            continue
        content = path.read_text(encoding='utf-8')
        issues.extend(f'missing-pattern:{path}:{pattern}' for pattern in required_patterns if pattern not in content)
        issues.extend(f'forbidden-pattern:{path}:{pattern}' for pattern in forbidden_patterns if pattern in content)

    if issues:
        return WorkflowVerifyStepReport(
            step='bypass-entrypoints',
            status='failed',
            result='bypass-detected',
            error='workflow bypass entrypoints detected',
            details=tuple(issues),
        )

    return WorkflowVerifyStepReport(
        step='bypass-entrypoints',
        status='success',
        result='validated',
    )


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


def _skipped_step(step: str) -> WorkflowVerifyStepReport:
    return WorkflowVerifyStepReport(step=step, status='skipped', result='skipped')
