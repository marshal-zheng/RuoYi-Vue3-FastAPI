"""Reusable managed-data fast reconcile service for development hot path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, Literal

from sqlalchemy import or_, select

from config.database import AsyncSessionLocal
from config.enums import RedisInitKeyConfig
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.db_workflow_do import DbWorkflowObjectDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.do.role_do import RoleDO
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.query_cache import get_query_cache

from .capability_models import (
    CAPABILITY_MANAGED_OBJECT_DOMAINS,
    LEGACY_MANAGED_OBJECT_SCOPES,
    capability_domain_for_entity,
)
from .managed_data_applier import ManagedDataApplier
from .managed_data_declaration_loader import ManagedDataDeclarationBundle, ManagedDataDeclarationLoader
from .managed_data_planner import ManagedDataManagedScope, ManagedDataPlanner
from .release_bundle_service import compute_payload_checksum

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from .capability_models import CapabilityObjectDomain

PostconditionStatus = Literal['clean', 'drift-detected', 'skipped']
MENU_RELOAD_TRIGGER_DOMAINS = frozenset({'menus', 'role_grants'})


@dataclass(frozen=True)
class PostconditionVerificationResult:
    """Planner replay plus metadata drift check after apply."""

    duration_ms: int
    pending_operation_objects: tuple[str, ...] = ()
    metadata_drift_objects: tuple[str, ...] = ()
    residual_objects: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.residual_objects


@dataclass(frozen=True)
class ManagedDataFastReconcileReport:
    """Structured managed-data fast reconcile result."""

    success: bool
    trigger: str
    compiled_checksum: str
    duration_ms: int
    affected_objects: tuple[str, ...] = ()
    residual_objects: tuple[str, ...] = ()
    applied_operations: int = 0
    skipped_operations: int = 0
    metadata_updated_objects: int = 0
    metadata_deactivated_objects: int = 0
    changed_domains: tuple[CapabilityObjectDomain, ...] = ()
    postcondition_status: PostconditionStatus = 'skipped'
    dry_run: bool = False
    state_changed: bool = False
    skipped_reason: str | None = None
    error: str | None = None
    synced_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            'changed_domains',
            normalize_changed_domains(self.changed_domains or changed_domains_for_affected_objects(self.affected_objects)),
        )

    @property
    def menu_reload_required(self) -> bool:
        return bool(MENU_RELOAD_TRIGGER_DOMAINS.intersection(self.changed_domains))


@dataclass(frozen=True)
class _MetadataSyncCounts:
    updated_objects: int
    deactivated_objects: int


@dataclass(frozen=True)
class ManagedDataSyncRuntimeResult:
    affected_objects: tuple[str, ...]
    applied_operations: int
    skipped_operations: int
    metadata_updated_objects: int
    metadata_deactivated_objects: int
    apply_duration_ms: int


@dataclass(frozen=True)
class ManagedDataReconcileRuntimeResult:
    managed_sync_result: ManagedDataSyncRuntimeResult
    postcondition_result: PostconditionVerificationResult


class PostconditionVerificationError(RuntimeError):
    """Raised when post-apply state still diverges from the target capability state."""

    def __init__(
        self,
        *,
        verification_result: PostconditionVerificationResult,
        managed_sync_result: ManagedDataSyncRuntimeResult,
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
        managed_scope = await load_managed_scope_from_metadata(
            self.session,
            role_key_to_id=role_key_to_id,
            current_state=current_state_without_metadata,
        )
        current_state = await applier.load_current_state(managed_scope)
        role_id_to_key = {role_id: role_key for role_key, role_id in role_key_to_id.items()}
        pending_operation_objects = tuple(
            normalize_residual_object_key(
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
        metadata_drift_objects = await collect_metadata_drift_objects(
            self.session,
            desired_entries=build_desired_object_entries(declaration_bundle=declaration_bundle),
        )
        residual_objects = tuple(sorted({*pending_operation_objects, *metadata_drift_objects}))
        return PostconditionVerificationResult(
            duration_ms=elapsed_ms(started_at),
            pending_operation_objects=pending_operation_objects,
            metadata_drift_objects=metadata_drift_objects,
            residual_objects=residual_objects,
        )


def normalize_changed_domains(domains: tuple[CapabilityObjectDomain, ...]) -> tuple[CapabilityObjectDomain, ...]:
    domain_set = {domain for domain in domains if domain in CAPABILITY_MANAGED_OBJECT_DOMAINS}
    return tuple(domain for domain in CAPABILITY_MANAGED_OBJECT_DOMAINS if domain in domain_set)


def changed_domains_for_affected_objects(affected_objects: tuple[str, ...]) -> tuple[CapabilityObjectDomain, ...]:
    resolved_domains: set[CapabilityObjectDomain] = set()
    for object_key in affected_objects:
        entity_type, _, _ = str(object_key or '').partition(':')
        if not entity_type:
            continue
        try:
            resolved_domains.add(capability_domain_for_entity(entity_type))
        except ValueError:
            continue
    return normalize_changed_domains(tuple(resolved_domains))


class ManagedDataFastReconcileService:
    """Compile capability declarations and apply managed-data fast reconcile only."""

    def __init__(
        self,
        *,
        session_factory=AsyncSessionLocal,
        declaration_loader_factory: Callable[[], Any] | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._declaration_loader_factory = declaration_loader_factory or ManagedDataDeclarationLoader
        self._redis_client = redis_client

    def load_declaration_bundle(self) -> ManagedDataDeclarationBundle:
        loader = self._declaration_loader_factory()
        return loader.load()

    async def reconcile(
        self,
        *,
        trigger: str,
        dry_run: bool = False,
        previous_compiled_checksum: str | None = None,
    ) -> ManagedDataFastReconcileReport:
        started_at = perf_counter()
        synced_at = datetime.now()
        compiled_checksum = ''

        try:
            declaration_bundle = self.load_declaration_bundle()
            compiled_checksum = compiled_checksum_for_bundle(declaration_bundle)

            if previous_compiled_checksum and compiled_checksum == previous_compiled_checksum:
                report = ManagedDataFastReconcileReport(
                    success=True,
                    trigger=trigger,
                    compiled_checksum=compiled_checksum,
                    duration_ms=elapsed_ms(started_at),
                    postcondition_status='skipped',
                    dry_run=dry_run,
                    state_changed=False,
                    skipped_reason='compiled_checksum_unchanged',
                    synced_at=synced_at,
                )
                logger.debug(
                    'Managed-data fast reconcile skipped: trigger={}, reason={}, compiled_checksum={}',
                    trigger,
                    report.skipped_reason,
                    compiled_checksum,
                )
                return report

            if dry_run:
                report = await self._dry_run_reconcile(
                    declaration_bundle=declaration_bundle,
                    trigger=trigger,
                    compiled_checksum=compiled_checksum,
                    started_at=started_at,
                    synced_at=synced_at,
                )
                logger.debug(
                    'Managed-data fast reconcile dry-run: trigger={}, affected_objects={}, duration_ms={}, compiled_checksum={}',
                    trigger,
                    report.affected_objects,
                    report.duration_ms,
                    compiled_checksum,
                )
                return report

            reconcile_result = await reconcile_managed_data(
                declaration_bundle=declaration_bundle,
                session_factory=self._session_factory,
            )
            await invalidate_managed_data_query_caches()
            await refresh_managed_data_redis_caches(self._session_factory, redis_client=self._redis_client)

            managed_result = reconcile_result.managed_sync_result
            state_changed = bool(
                managed_result.applied_operations
                or managed_result.metadata_updated_objects
                or managed_result.metadata_deactivated_objects
            )
            report = ManagedDataFastReconcileReport(
                success=True,
                trigger=trigger,
                compiled_checksum=compiled_checksum,
                duration_ms=elapsed_ms(started_at),
                affected_objects=managed_result.affected_objects,
                applied_operations=managed_result.applied_operations,
                skipped_operations=managed_result.skipped_operations,
                metadata_updated_objects=managed_result.metadata_updated_objects,
                metadata_deactivated_objects=managed_result.metadata_deactivated_objects,
                postcondition_status='clean',
                dry_run=False,
                state_changed=state_changed,
                synced_at=synced_at,
            )
            logger.debug(
                'Managed-data fast reconcile detail: trigger={}, success={}, state_changed={}, affected_objects={}, '
                'changed_domains={}, applied_operations={}, skipped_operations={}, metadata_updated_objects={}, '
                'metadata_deactivated_objects={}, compiled_checksum={}, duration_ms={}',
                trigger,
                report.success,
                report.state_changed,
                report.affected_objects,
                report.changed_domains,
                report.applied_operations,
                report.skipped_operations,
                report.metadata_updated_objects,
                report.metadata_deactivated_objects,
                report.compiled_checksum,
                report.duration_ms,
            )
            return report
        except PostconditionVerificationError as exc:
            report = ManagedDataFastReconcileReport(
                success=False,
                trigger=trigger,
                compiled_checksum=compiled_checksum,
                duration_ms=elapsed_ms(started_at),
                affected_objects=exc.managed_sync_result.affected_objects,
                residual_objects=exc.verification_result.residual_objects,
                applied_operations=exc.managed_sync_result.applied_operations,
                skipped_operations=exc.managed_sync_result.skipped_operations,
                metadata_updated_objects=exc.managed_sync_result.metadata_updated_objects,
                metadata_deactivated_objects=exc.managed_sync_result.metadata_deactivated_objects,
                postcondition_status='drift-detected',
                dry_run=dry_run,
                error=str(exc),
                synced_at=synced_at,
            )
            logger.debug(
                'Managed-data fast reconcile failed detail: trigger={}, reason={}, residual_objects={}, '
                'affected_objects={}, compiled_checksum={}, duration_ms={}',
                trigger,
                report.error,
                report.residual_objects,
                report.affected_objects,
                report.compiled_checksum,
                report.duration_ms,
            )
            return report
        except Exception as exc:
            report = ManagedDataFastReconcileReport(
                success=False,
                trigger=trigger,
                compiled_checksum=compiled_checksum,
                duration_ms=elapsed_ms(started_at),
                postcondition_status='skipped',
                dry_run=dry_run,
                error=str(exc),
                synced_at=synced_at,
            )
            logger.debug(
                'Managed-data fast reconcile failed detail: trigger={}, error={}, compiled_checksum={}, duration_ms={}',
                trigger,
                exc,
                report.compiled_checksum,
                report.duration_ms,
            )
            return report

    async def _dry_run_reconcile(
        self,
        *,
        declaration_bundle: ManagedDataDeclarationBundle,
        trigger: str,
        compiled_checksum: str,
        started_at: float,
        synced_at: datetime,
    ) -> ManagedDataFastReconcileReport:
        async with self._session_factory() as session:
            applier = ManagedDataApplier(session)
            role_key_to_id = await load_role_key_to_id(session)
            current_state_without_metadata = await applier.load_current_state()
            managed_scope = await load_managed_scope_from_metadata(
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
            apply_report = await applier.apply_plan(plan, dry_run=True, managed_scope=managed_scope)

        return ManagedDataFastReconcileReport(
            success=True,
            trigger=trigger,
            compiled_checksum=compiled_checksum,
            duration_ms=elapsed_ms(started_at),
            affected_objects=apply_report.affected_objects,
            applied_operations=apply_report.applied_operations,
            skipped_operations=apply_report.skipped_operations,
            postcondition_status='skipped',
            dry_run=True,
            state_changed=False,
            synced_at=synced_at,
        )


def load_managed_data_declaration_bundle() -> ManagedDataDeclarationBundle:
    return ManagedDataDeclarationLoader().load()


async def reconcile_managed_data(
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
    session_factory,
) -> ManagedDataReconcileRuntimeResult:
    async with session_factory() as session:
        async with session.begin():
            applier = ManagedDataApplier(session)
            role_key_to_id = await load_role_key_to_id(session)
            current_state_without_metadata = await applier.load_current_state()
            managed_scope = await load_managed_scope_from_metadata(
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
            metadata_counts = await sync_workflow_object_metadata(
                session,
                declaration_bundle=declaration_bundle,
            )
            managed_sync_result = ManagedDataSyncRuntimeResult(
                affected_objects=apply_report.affected_objects,
                applied_operations=apply_report.applied_operations,
                skipped_operations=apply_report.skipped_operations,
                metadata_updated_objects=metadata_counts.updated_objects,
                metadata_deactivated_objects=metadata_counts.deactivated_objects,
                apply_duration_ms=elapsed_ms(apply_started_at),
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

        return ManagedDataReconcileRuntimeResult(
            managed_sync_result=managed_sync_result,
            postcondition_result=postcondition_result,
        )


async def load_role_key_to_id(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(select(RoleDO.role_key, RoleDO.role_id).where(RoleDO.del_flag != '2'))
    return {
        str(row.role_key).strip(): int(row.role_id)
        for row in rows.all()
        if str(row.role_key or '').strip()
    }


async def load_managed_scope_from_metadata(
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


async def sync_workflow_object_metadata(
    session: AsyncSession,
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
) -> _MetadataSyncCounts:
    desired_entries = build_desired_object_entries(declaration_bundle=declaration_bundle)
    existing_rows = await load_managed_workflow_object_rows(session)
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


def build_desired_object_entries(
    *,
    declaration_bundle: ManagedDataDeclarationBundle,
) -> dict[tuple[str, str], dict[str, str]]:
    entries: dict[tuple[str, str], dict[str, str]] = {}
    compiled_state = require_compiled_capability_state(declaration_bundle)

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


def compiled_checksum_for_bundle(bundle: ManagedDataDeclarationBundle) -> str:
    compiled_state = require_compiled_capability_state(bundle)
    if compiled_state.checksums is None:
        return ''
    return compiled_state.checksums.compiled_checksum


def require_compiled_capability_state(bundle: ManagedDataDeclarationBundle):
    compiled_state = bundle.compiled_capability_state
    if compiled_state is None:
        raise ValueError('compiled capability state is required for dev-sync')
    return compiled_state


async def load_managed_workflow_object_rows(session: AsyncSession) -> list[DbWorkflowObjectDO]:
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


async def collect_metadata_drift_objects(
    session: AsyncSession,
    *,
    desired_entries: dict[tuple[str, str], dict[str, str]],
) -> tuple[str, ...]:
    existing_rows = await load_managed_workflow_object_rows(session)
    existing_by_identity = {(row.object_type, row.object_key): row for row in existing_rows}
    drift_objects: set[str] = set()

    for identity, desired in desired_entries.items():
        existing = existing_by_identity.get(identity)
        if existing is None:
            drift_objects.add(format_metadata_identity(identity))
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
            drift_objects.add(format_metadata_identity(identity))

    for identity, existing in existing_by_identity.items():
        if identity in desired_entries:
            continue
        if existing.active_flag != 'N':
            drift_objects.add(format_metadata_identity(identity))

    return tuple(sorted(drift_objects))


def format_metadata_identity(identity: tuple[str, str]) -> str:
    return f'{identity[0]}:{identity[1]}'


def normalize_residual_object_key(
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


def declaration_objects(bundle: ManagedDataDeclarationBundle) -> tuple[str, ...]:
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


async def invalidate_managed_data_query_caches() -> None:
    cache = get_query_cache()
    patterns = (
        f'{cache.key_prefix}:menu:*',
        f'{cache.key_prefix}:role:*',
        f'{cache.key_prefix}:menu:role_tree:*',
        f'{cache.key_prefix}:menu:tree:*',
        f'{cache.key_prefix}:menu:list:*',
    )
    for pattern in patterns:
        await cache.delete_pattern(pattern)


async def refresh_managed_data_redis_caches(session_factory, *, redis_client: Any | None) -> None:
    if redis_client is None:
        return

    async with session_factory() as session:
        await refresh_sys_config_cache(session, redis_client)
        await refresh_sys_dict_cache(session, redis_client)


async def refresh_sys_config_cache(session: AsyncSession, redis_client: Any) -> None:
    keys = await redis_client.keys(f'{RedisInitKeyConfig.SYS_CONFIG.key}:*')
    if keys:
        await redis_client.delete(*keys)

    config_rows = (await session.execute(select(ConfigDO))).scalars().all()
    for row in config_rows:
        await redis_client.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{row.config_key}', row.config_value)


async def refresh_sys_dict_cache(session: AsyncSession, redis_client: Any) -> None:
    keys = await redis_client.keys(f'{RedisInitKeyConfig.SYS_DICT.key}:*')
    if keys:
        await redis_client.delete(*keys)

    dict_type_rows = (
        await session.execute(select(DictTypeDO).where(DictTypeDO.status == StatusEnum.NORMAL.value))
    ).scalars().all()
    for dict_type_row in dict_type_rows:
        dict_data_rows = (
            await session.execute(select(DictDataDO).where(DictDataDO.dict_type == dict_type_row.dict_type))
        ).scalars().all()
        dict_data = [CamelCaseUtil.transform_result(row) for row in dict_data_rows if row]
        await redis_client.set(
            f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type_row.dict_type}',
            json.dumps(dict_data, ensure_ascii=False, default=str),
        )


def elapsed_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)
