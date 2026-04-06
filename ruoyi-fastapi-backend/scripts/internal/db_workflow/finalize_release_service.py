"""Finalize managed data and release visibility artifacts."""

from __future__ import annotations

import asyncio
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

import yaml
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .managed_data_applier import ManagedDataApplier
from .managed_data_declaration_loader import (
    ManagedDataDeclarationLoader,
    ManagedDataTargetState,
    ReleasePlanSelection,
)
from .managed_data_planner import (
    ManagedDataManagedScope,
    ManagedDataOperation,
    ManagedDataPlan,
    ManagedDataPlanner,
)
from .release_bundle_service import (
    BUNDLE_ID_PATTERN,
    MANAGED_DATA_FILENAME,
    RELEASE_MANIFEST_FILENAME,
    ReleaseBundleService,
    build_managed_data_payload,
    build_managed_object_snapshot,
    build_release_manifest_payload,
)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class FinalizeReleaseResult:
    """Managed data / release visibility finalization outcome."""

    bundle_id: str | None
    bundle_dir: Path | None
    bundle_file: Path | None
    managed_data_file: Path | None
    release_manifest_file: Path | None
    managed_data_operation_count: int
    data_finalize: Literal['generated', 'no-op']
    visibility_finalize: Literal['generated', 'no-op']
    selection_mode: Literal['release-plan'] = 'release-plan'


def finalize_release_artifacts(
    *,
    project_root: Path,
    finalize_database_url: str,
    schema_revision: str,
    message: str,
) -> FinalizeReleaseResult:
    """Generate and validate managed-data / release-manifest artifacts for finalize."""

    return asyncio.run(
        _finalize_release_artifacts_async(
            project_root=project_root,
            finalize_database_url=finalize_database_url,
            schema_revision=schema_revision,
            message=message,
        )
    )


async def _finalize_release_artifacts_async(
    *,
    project_root: Path,
    finalize_database_url: str,
    schema_revision: str,
    message: str,
) -> FinalizeReleaseResult:
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    output_root = project_root / 'db_artifacts' / 'releases'
    declaration_bundle = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).load()
    formal_target_state = declaration_bundle.formal_candidate_state
    desired_manifest_snapshot = _release_manifest_snapshot(
        formal_target_state,
        declaration_bundle.release_selection,
    )
    latest_manifest_snapshot = _load_latest_release_manifest_snapshot(output_root)
    visibility_changed = latest_manifest_snapshot is not None and latest_manifest_snapshot != desired_manifest_snapshot
    compiled_state = declaration_bundle.compiled_capability_state
    if compiled_state is None:
        raise ValueError('compiled capability state is required for finalize')
    managed_object_snapshot = build_managed_object_snapshot(
        compiled_state=compiled_state,
        enabled_modules=declaration_bundle.release_selection.enabled_modules,
    )
    role_key_to_id = _load_bootstrap_role_ids(declaration_bundle.paths.bootstrap_roles)
    session_factory, engine = _build_session_factory(finalize_database_url)

    try:
        async with session_factory() as session:
            managed_scope = ManagedDataManagedScope()
            applier = ManagedDataApplier(session)
            async with session.begin():
                managed_scope = await _apply_existing_release_bundles(
                    session=session,
                    applier=applier,
                    output_root=output_root,
                )
                current_state = await applier.load_current_state(managed_scope)
                plan = ManagedDataPlanner().plan(
                    current_state=current_state,
                    target_state=formal_target_state,
                    role_key_to_id=role_key_to_id,
                )

                if plan.operation_count == 0 and not visibility_changed:
                    return FinalizeReleaseResult(
                        bundle_id=None,
                        bundle_dir=None,
                        bundle_file=None,
                        managed_data_file=None,
                        release_manifest_file=None,
                        managed_data_operation_count=0,
                        data_finalize='no-op',
                        visibility_finalize='no-op',
                    )

                bundle_id = _next_bundle_id(output_root, message, declaration_bundle.release_selection.release_key)
                service = ReleaseBundleService(output_root=output_root)
                bundle = None
                try:
                    bundle = service.write_bundle(
                        bundle_id=bundle_id,
                        bundle_kind='release',
                        schema_revision=schema_revision,
                        release_key=declaration_bundle.release_selection.release_key or bundle_id,
                        managed_data_payload=build_managed_data_payload(
                            bundle_id,
                            plan,
                            target_state=formal_target_state,
                            release_selection=declaration_bundle.release_selection,
                            managed_objects=managed_object_snapshot,
                        ),
                        release_manifest_payload=build_release_manifest_payload(
                            bundle_id,
                            target_state=formal_target_state,
                            release_selection=declaration_bundle.release_selection,
                            selection_mode='release-plan',
                        ),
                        message=message,
                    )
                    await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)
                    replay_scope = _advance_managed_scope(managed_scope, plan)
                    replay_report = await applier.apply_plan(plan, dry_run=False, managed_scope=replay_scope)
                    if replay_report.applied_operations != 0:
                        raise ValueError(
                            'generated managed-data bundle is not idempotent: replay applied operations '
                            f'({replay_report.applied_operations})'
                        )
                except Exception:
                    if bundle is not None and bundle.bundle_dir.exists():
                        shutil.rmtree(bundle.bundle_dir)
                    raise

                return FinalizeReleaseResult(
                    bundle_id=bundle.bundle_id,
                    bundle_dir=bundle.bundle_dir,
                    bundle_file=bundle.file_by_type('bundle').path,
                    managed_data_file=bundle.file_by_type('managed-data').path,
                    release_manifest_file=bundle.file_by_type('release-manifest').path,
                    managed_data_operation_count=plan.operation_count,
                    data_finalize='generated' if plan.operation_count > 0 else 'no-op',
                    visibility_finalize='generated',
                )
    finally:
        await engine.dispose()


def build_release_candidate_state(
    target_state: ManagedDataTargetState,
    release_selection: ReleasePlanSelection,
) -> ManagedDataTargetState:
    """Project full declarations into the release-plan-scoped formal candidate state."""

    selected_menu_ids = _expand_menu_dependencies(target_state.menus, set(release_selection.menu_ids))
    selected_dict_types = set(release_selection.dict_types)
    selected_config_keys = set(release_selection.config_keys)

    return ManagedDataTargetState(
        menus={menu_id: target_state.menus[menu_id] for menu_id in sorted(selected_menu_ids)},
        role_grants={
            role_key: tuple(sorted(menu_ids))
            for role_key, menu_ids in sorted(release_selection.role_grants.items())
            if menu_ids
        },
        dict_types={
            dict_type: target_state.dict_types[dict_type]
            for dict_type in sorted(selected_dict_types)
            if dict_type in target_state.dict_types
        },
        dict_data={
            (dict_type, dict_value): row
            for (dict_type, dict_value), row in sorted(target_state.dict_data.items())
            if dict_type in selected_dict_types
        },
        configs={
            config_key: target_state.configs[config_key]
            for config_key in sorted(selected_config_keys)
            if config_key in target_state.configs
        },
    )


def _expand_menu_dependencies(
    menus: dict[int, dict[str, Any]],
    selected_menu_ids: set[int],
) -> set[int]:
    expanded = set(selected_menu_ids)
    for menu_id in tuple(selected_menu_ids):
        current_menu_id = menu_id
        while current_menu_id in menus:
            parent_id = int(menus[current_menu_id].get('parent_id', 0) or 0)
            if parent_id <= 0 or parent_id in expanded:
                break
            if parent_id not in menus:
                raise ValueError(f'release selection depends on missing parent menu_id={parent_id} for menu_id={menu_id}')
            expanded.add(parent_id)
            current_menu_id = parent_id
    return expanded


async def _apply_existing_release_bundles(
    *,
    session: AsyncSession,
    applier: ManagedDataApplier,
    output_root: Path,
) -> ManagedDataManagedScope:
    managed_scope = ManagedDataManagedScope()
    for bundle_dir in _list_bundle_dirs(output_root):
        managed_data_file = bundle_dir / MANAGED_DATA_FILENAME
        if not managed_data_file.exists():
            continue
        plan = _load_managed_data_plan(managed_data_file)
        await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)
        managed_scope = _advance_managed_scope(managed_scope, plan)
        await session.flush()
    return managed_scope


def _load_managed_data_plan(path: Path) -> ManagedDataPlan:
    payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    operations = []
    for raw_operation in payload.get('operations', []):
        if not isinstance(raw_operation, dict):
            raise ValueError(f'invalid managed-data operation in {path}')
        operations.append(
            ManagedDataOperation(
                op_type=str(raw_operation['op_type']),
                entity_type=str(raw_operation['entity_type']),
                object_key=str(raw_operation['object_key']),
                match_fields=dict(raw_operation.get('match_fields') or {}),
                values=dict(raw_operation.get('values') or {}),
            )
        )
    return ManagedDataPlan(operations=tuple(operations))


def _advance_managed_scope(
    managed_scope: ManagedDataManagedScope,
    plan: ManagedDataPlan,
) -> ManagedDataManagedScope:
    menu_ids = set(managed_scope.menu_ids)
    role_menu_pairs = set(managed_scope.role_menu_pairs)
    dict_type_ids = set(managed_scope.dict_type_ids)
    dict_data_codes = set(managed_scope.dict_data_codes)
    config_ids = set(managed_scope.config_ids)

    for operation in plan.operations:
        scope_bucket, identity = _scope_target_for_operation(
            operation,
            menu_ids=menu_ids,
            role_menu_pairs=role_menu_pairs,
            dict_type_ids=dict_type_ids,
            dict_data_codes=dict_data_codes,
            config_ids=config_ids,
        )
        if scope_bucket is None or identity is None:
            continue
        if operation.op_type in {'delete-row', 'remove-link'}:
            scope_bucket.discard(identity)
        else:
            scope_bucket.add(identity)

    return ManagedDataManagedScope(
        menu_ids=frozenset(menu_ids),
        role_menu_pairs=frozenset(role_menu_pairs),
        dict_type_ids=frozenset(dict_type_ids),
        dict_data_codes=frozenset(dict_data_codes),
        config_ids=frozenset(config_ids),
    )


def _scope_target_for_operation(
    operation: ManagedDataOperation,
    *,
    menu_ids: set[int],
    role_menu_pairs: set[tuple[int, int]],
    dict_type_ids: set[int],
    dict_data_codes: set[int],
    config_ids: set[int],
) -> tuple[set[Any] | None, Any]:
    if operation.entity_type == 'sys_menu':
        return menu_ids, int(operation.match_fields['menu_id'])
    if operation.entity_type == 'sys_role_menu':
        return (
            role_menu_pairs,
            (int(operation.match_fields['role_id']), int(operation.match_fields['menu_id'])),
        )
    if operation.entity_type == 'sys_dict_type':
        return dict_type_ids, int(operation.match_fields['dict_id'])
    if operation.entity_type == 'sys_dict_data':
        return dict_data_codes, int(operation.match_fields['dict_code'])
    if operation.entity_type == 'sys_config':
        return config_ids, int(operation.match_fields['config_id'])
    return None, None


def _release_manifest_snapshot(
    target_state: ManagedDataTargetState,
    release_selection: ReleasePlanSelection,
) -> dict[str, Any]:
    payload = build_release_manifest_payload(
        'snapshot',
        target_state=target_state,
        release_selection=release_selection,
        selection_mode='release-plan',
    )
    payload.pop('bundle_id', None)
    return payload


def _load_latest_release_manifest_snapshot(output_root: Path) -> dict[str, Any] | None:
    for bundle_dir in reversed(_list_bundle_dirs(output_root)):
        manifest_path = bundle_dir / RELEASE_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        payload = yaml.safe_load(manifest_path.read_text(encoding='utf-8')) or {}
        if isinstance(payload, dict):
            payload.pop('bundle_id', None)
            return payload
    return None


def _list_bundle_dirs(output_root: Path) -> list[Path]:
    if not output_root.exists():
        return []
    return sorted(
        [path for path in output_root.iterdir() if path.is_dir() and BUNDLE_ID_PATTERN.match(path.name)],
        key=lambda path: path.name,
    )


def _next_bundle_id(output_root: Path, message: str, release_key: str) -> str:
    date_prefix = datetime.now().strftime('%Y%m%d')
    sequence = 1
    for bundle_dir in _list_bundle_dirs(output_root):
        if not bundle_dir.name.startswith(f'{date_prefix}_'):
            continue
        sequence = max(sequence, int(bundle_dir.name.split('_', 2)[1]) + 1)

    slug_source = message or release_key or 'release'
    slug = re.sub(r'[^a-z0-9]+', '-', slug_source.lower()).strip('-')
    if not slug:
        slug = 'release'
    return f'{date_prefix}_{sequence:03d}_{slug}'


def _load_bootstrap_role_ids(path: Path) -> dict[str, int]:
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


def _build_session_factory(finalize_database_url: str) -> tuple[async_sessionmaker[AsyncSession], Any]:
    async_database_url = _to_async_database_url(finalize_database_url)
    engine = create_async_engine(async_database_url, future=True)
    return async_sessionmaker(bind=engine, expire_on_commit=False), engine


def _to_async_database_url(database_url: str) -> str:
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', 'sqlite+aiosqlite:///', 1)
    if database_url.startswith('mysql+pymysql://'):
        return database_url.replace('mysql+pymysql://', 'mysql+asyncmy://', 1)
    if database_url.startswith('postgresql+psycopg2://'):
        return database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)
    return database_url
