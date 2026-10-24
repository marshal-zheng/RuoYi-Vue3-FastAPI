"""Generate a declaration-sourced baseline bundle scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

try:
    from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataDeclarationLoader
    from scripts.internal.db_workflow.managed_data_planner import (
        ManagedDataCurrentState,
        ManagedDataManagedScope,
        ManagedDataPlanner,
    )
    from scripts.internal.db_workflow.release_bundle_service import (
        ReleaseBundle,
        ReleaseBundleService,
        ReleaseSelectionMode,
        build_managed_data_payload,
        build_managed_object_snapshot,
        build_release_manifest_payload,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import sys

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataDeclarationLoader
    from scripts.internal.db_workflow.managed_data_planner import (
        ManagedDataCurrentState,
        ManagedDataManagedScope,
        ManagedDataPlanner,
    )
    from scripts.internal.db_workflow.release_bundle_service import (
        ReleaseBundle,
        ReleaseBundleService,
        ReleaseSelectionMode,
        build_managed_data_payload,
        build_managed_object_snapshot,
        build_release_manifest_payload,
    )


def generate_baseline_bundle(
    *,
    bundle_id: str,
    schema_revision: str,
    selection_mode: ReleaseSelectionMode = 'full-declarations',
    seed_data_dir: str | Path | None = None,
    output_root: str | Path | None = None,
    message: str = 'Baseline bundle scaffold generated from managed declarations',
) -> ReleaseBundle:
    loader = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir)
    declaration_bundle = loader.load()

    role_key_to_id = _load_bootstrap_role_ids(declaration_bundle.paths.bootstrap_roles)
    plan = ManagedDataPlanner().plan(
        current_state=_empty_current_state(),
        target_state=declaration_bundle.formal_candidate_state,
        role_key_to_id=role_key_to_id,
    )
    compiled_state = declaration_bundle.compiled_capability_state
    if compiled_state is None:
        raise ValueError('compiled capability state is required for baseline bundle generation')

    service = ReleaseBundleService(output_root=output_root)
    return service.write_bundle(
        bundle_id=bundle_id,
        bundle_kind='baseline',
        schema_revision=schema_revision,
        release_key=declaration_bundle.release_selection.release_key or bundle_id,
        managed_data_payload=build_managed_data_payload(
            bundle_id,
            plan,
            target_state=declaration_bundle.formal_candidate_state,
            release_selection=declaration_bundle.release_selection,
            managed_objects=build_managed_object_snapshot(
                compiled_state=compiled_state,
                enabled_modules=declaration_bundle.release_selection.enabled_modules,
            ),
        ),
        release_manifest_payload=build_release_manifest_payload(
            bundle_id,
            target_state=declaration_bundle.formal_candidate_state,
            release_selection=declaration_bundle.release_selection,
            selection_mode=selection_mode,
        ),
        message=message,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate a baseline managed-data bundle scaffold')
    parser.add_argument('--bundle-id', required=True, help='Bundle id, e.g. 20260402_001_datasource-baseline')
    parser.add_argument('--schema-revision', default='baseline', help='Schema revision recorded in bundle.yaml')
    parser.add_argument(
        '--selection-mode',
        default='full-declarations',
        choices=['full-declarations', 'release-plan'],
        help='Whether release.manifest.yaml includes all declarations or the current release-plan selection',
    )
    parser.add_argument('--seed-data-dir', default=None, help='Optional seed_data directory override')
    parser.add_argument('--output-root', default=None, help='Optional db_artifacts/releases root override')
    parser.add_argument('--message', default='Baseline bundle scaffold generated from managed declarations')
    args = parser.parse_args(argv)

    bundle = generate_baseline_bundle(
        bundle_id=args.bundle_id,
        schema_revision=args.schema_revision,
        selection_mode=args.selection_mode,
        seed_data_dir=args.seed_data_dir,
        output_root=args.output_root,
        message=args.message,
    )

    print(f'bundle_id={bundle.bundle_id}')
    print(f'bundle_dir={bundle.bundle_dir}')
    print(f'bundle_kind={bundle.bundle_kind}')
    print(f'schema_revision={bundle.schema_revision}')
    print(f'release_key={bundle.release_key}')
    print(f'idempotency_key={bundle.idempotency_key}')
    print(f'managed_object_count={bundle.managed_object_count}')
    print(f'bundle_checksum={bundle.file_by_type("bundle").checksum}')
    print(f'managed_data_checksum={bundle.file_by_type("managed-data").checksum}')
    print(f'release_manifest_checksum={bundle.file_by_type("release-manifest").checksum}')
    return 0


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


def _empty_current_state() -> ManagedDataCurrentState:
    return ManagedDataCurrentState(
        menus_by_id={},
        role_menu_pairs=set(),
        dict_types_by_id={},
        dict_type_ids_by_key={},
        dict_data_by_code={},
        dict_data_codes_by_business_key={},
        configs_by_id={},
        config_ids_by_key={},
        managed_scope=ManagedDataManagedScope(),
    )


if __name__ == '__main__':
    raise SystemExit(main())
