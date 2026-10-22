"""Release bundle file conventions, checksums, and scaffold helpers."""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml

from .remark_inputs import release_row

if TYPE_CHECKING:
    from .managed_data_declaration_loader import ManagedDataTargetState, ReleasePlanSelection
    from .managed_data_planner import ManagedDataPlan

BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RELEASES_DIR = BACKEND_ROOT / 'db_artifacts' / 'releases'
BUNDLE_FILENAME = 'bundle.yaml'
MANAGED_DATA_FILENAME = 'managed-data.yaml'
RELEASE_MANIFEST_FILENAME = 'release.manifest.yaml'
BUNDLE_ID_PATTERN = re.compile(r'^\d{8}_\d{3}_[a-z0-9][a-z0-9-]*$')

BundleArtifactType = Literal['bundle', 'managed-data', 'release-manifest']
ReleaseSelectionMode = Literal['full-declarations', 'release-plan']


@dataclass(frozen=True)
class ReleaseBundleFile:
    """A physical bundle file with checksum metadata."""

    artifact_type: BundleArtifactType
    filename: str
    path: Path
    checksum: str
    size_bytes: int


@dataclass(frozen=True)
class ReleaseBundle:
    """Materialized release bundle descriptor."""

    bundle_id: str
    bundle_dir: Path
    bundle_kind: str
    schema_revision: str
    release_key: str
    idempotency_key: str
    files: tuple[ReleaseBundleFile, ...]
    managed_object_count: int

    def file_by_type(self, artifact_type: BundleArtifactType) -> ReleaseBundleFile:
        for bundle_file in self.files:
            if bundle_file.artifact_type == artifact_type:
                return bundle_file
        raise KeyError(f'file not found for artifact_type={artifact_type}')


class ReleaseBundleService:
    """Persist immutable bundle artifacts under db_artifacts/releases/."""

    def __init__(self, output_root: str | Path | None = None) -> None:
        self.output_root = Path(output_root) if output_root else DEFAULT_RELEASES_DIR

    def write_bundle(
        self,
        *,
        bundle_id: str,
        bundle_kind: str,
        schema_revision: str,
        release_key: str,
        managed_data_payload: dict[str, Any],
        release_manifest_payload: dict[str, Any],
        generated_at: datetime | None = None,
        message: str = '',
    ) -> ReleaseBundle:
        self._validate_bundle_id(bundle_id)
        bundle_dir = self.output_root / bundle_id

        managed_data_checksum = compute_payload_checksum(managed_data_payload)
        release_manifest_checksum = compute_payload_checksum(release_manifest_payload)
        normalized_generated_at = _format_timestamp(generated_at or datetime.now(UTC))
        idempotency_key = compute_text_checksum(
            '\n'.join(
                (
                    bundle_id,
                    bundle_kind,
                    schema_revision,
                    release_key,
                    managed_data_checksum,
                    release_manifest_checksum,
                )
            )
        )
        managed_object_count = int(managed_data_payload.get('managed_object_count', 0))

        bundle_payload = {
            'version': '1',
            'bundle_id': bundle_id,
            'bundle_kind': bundle_kind,
            'schema_revision': schema_revision,
            'release_key': release_key,
            'generated_at': normalized_generated_at,
            'message': message,
            'idempotency_key': idempotency_key,
            'artifacts': [
                {
                    'artifact_type': 'managed-data',
                    'filename': MANAGED_DATA_FILENAME,
                    'checksum': managed_data_checksum,
                    'idempotency_key': f'{bundle_id}:managed-data:{managed_data_checksum}',
                },
                {
                    'artifact_type': 'release-manifest',
                    'filename': RELEASE_MANIFEST_FILENAME,
                    'checksum': release_manifest_checksum,
                    'idempotency_key': f'{bundle_id}:release-manifest:{release_manifest_checksum}',
                },
            ],
        }

        desired_files = (
            ('managed-data', MANAGED_DATA_FILENAME, managed_data_payload),
            ('release-manifest', RELEASE_MANIFEST_FILENAME, release_manifest_payload),
            ('bundle', BUNDLE_FILENAME, bundle_payload),
        )
        self._assert_existing_files_compatible(bundle_dir, desired_files)

        bundle_dir.mkdir(parents=True, exist_ok=True)

        files = tuple(
            self._write_if_missing(
                artifact_type=artifact_type,
                bundle_dir=bundle_dir,
                filename=filename,
                payload=payload,
            )
            for artifact_type, filename, payload in desired_files
        )

        return ReleaseBundle(
            bundle_id=bundle_id,
            bundle_dir=bundle_dir,
            bundle_kind=bundle_kind,
            schema_revision=schema_revision,
            release_key=release_key,
            idempotency_key=idempotency_key,
            files=files,
            managed_object_count=managed_object_count,
        )

    @staticmethod
    def _validate_bundle_id(bundle_id: str) -> None:
        if not BUNDLE_ID_PATTERN.match(bundle_id):
            raise ValueError('bundle_id must match YYYYMMDD_NNN_slug, for example 20260402_001_datasource-baseline')

    def _assert_existing_files_compatible(
        self,
        bundle_dir: Path,
        desired_files: tuple[tuple[BundleArtifactType, str, dict[str, Any]], ...],
    ) -> None:
        if not bundle_dir.exists():
            return

        for _, filename, payload in desired_files:
            path = bundle_dir / filename
            if not path.exists():
                continue
            existing_payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
            existing_checksum = compute_payload_checksum(existing_payload)
            desired_checksum = compute_payload_checksum(payload)
            if existing_checksum != desired_checksum:
                raise ValueError(f'bundle file already exists with different content: {path}')

    def _write_if_missing(
        self,
        *,
        artifact_type: BundleArtifactType,
        bundle_dir: Path,
        filename: str,
        payload: dict[str, Any],
    ) -> ReleaseBundleFile:
        path = bundle_dir / filename
        if not path.exists():
            path.write_text(render_bundle_yaml(payload), encoding='utf-8')
        return ReleaseBundleFile(
            artifact_type=artifact_type,
            filename=filename,
            path=path,
            checksum=compute_payload_checksum(payload),
            size_bytes=path.stat().st_size,
        )


def build_managed_object_snapshot(
    *,
    compiled_state,
    enabled_modules: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Build the full managed-object metadata snapshot for a release target state."""

    managed_objects: list[dict[str, Any]] = []
    for module_key in sorted(enabled_modules):
        declaration = compiled_state.modules[module_key]
        source_path = str(declaration.source_path)

        for menu_id, row in sorted(declaration.resources.menus.items()):
            checksum = compute_payload_checksum(row)
            managed_objects.append(
                {
                    'object_type': 'sys_menu',
                    'object_key': str(menu_id),
                    'module_key': module_key,
                    'object_domain': 'menus',
                    'owner_scope': 'menus',
                    'source_path': source_path,
                    'source_checksum': checksum,
                    'checksum': checksum,
                }
            )

        for role_key, menu_ids in sorted(declaration.resources.role_grants.items()):
            for menu_id in menu_ids:
                checksum_payload = {'role_key': role_key, 'menu_id': menu_id}
                checksum = compute_payload_checksum(checksum_payload)
                managed_objects.append(
                    {
                        'object_type': 'sys_role_menu',
                        'object_key': f'{role_key}:{menu_id}',
                        'module_key': module_key,
                        'object_domain': 'role_grants',
                        'owner_scope': 'role_grants',
                        'source_path': source_path,
                        'source_checksum': checksum,
                        'checksum': checksum,
                    }
                )

        for dict_type, row in sorted(declaration.resources.dict_types.items()):
            checksum = compute_payload_checksum(row)
            managed_objects.append(
                {
                    'object_type': 'sys_dict_type',
                    'object_key': dict_type,
                    'module_key': module_key,
                    'object_domain': 'dict_types',
                    'owner_scope': 'dict_types',
                    'source_path': source_path,
                    'source_checksum': checksum,
                    'checksum': checksum,
                }
            )

        for (dict_type, dict_value), row in sorted(declaration.resources.dict_data.items()):
            checksum = compute_payload_checksum(row)
            managed_objects.append(
                {
                    'object_type': 'sys_dict_data',
                    'object_key': f'{dict_type}:{dict_value}',
                    'module_key': module_key,
                    'object_domain': 'dict_data',
                    'owner_scope': 'dict_data',
                    'source_path': source_path,
                    'source_checksum': checksum,
                    'checksum': checksum,
                }
            )

        for config_key, row in sorted(declaration.resources.configs.items()):
            checksum = compute_payload_checksum(row)
            managed_objects.append(
                {
                    'object_type': 'sys_config',
                    'object_key': config_key,
                    'module_key': module_key,
                    'object_domain': 'configs',
                    'owner_scope': 'configs',
                    'source_path': source_path,
                    'source_checksum': checksum,
                    'checksum': checksum,
                }
            )

    return sorted(managed_objects, key=lambda item: (item['object_type'], item['object_key']))


def build_managed_data_payload(
    bundle_id: str,
    plan: ManagedDataPlan,
    *,
    target_state: ManagedDataTargetState | None = None,
    release_selection: ReleasePlanSelection | None = None,
    managed_objects: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Serialize a normalized managed data plan into a bundle artifact payload."""

    operations = [
        {
            'op_type': operation.op_type,
            'entity_type': operation.entity_type,
            'object_key': operation.object_key,
            'match_fields': dict(operation.match_fields),
            'values': dict(operation.values),
        }
        for operation in plan.operations
    ]
    object_keys = sorted({operation.object_key for operation in plan.operations})
    counts_by_operation = {
        op_type: plan.count(op_type=op_type)
        for op_type in ('upsert-row', 'delete-row', 'ensure-link', 'remove-link')
        if plan.count(op_type=op_type) > 0
    }
    counts_by_entity = {
        entity_type: plan.count(entity_type=entity_type)
        for entity_type in ('sys_menu', 'sys_role_menu', 'sys_dict_type', 'sys_dict_data', 'sys_config')
        if plan.count(entity_type=entity_type) > 0
    }
    payload = {
        'version': '1',
        'bundle_id': bundle_id,
        'artifact_type': 'managed-data',
        'managed_object_count': len(object_keys),
        'operation_count': plan.operation_count,
        'summary': {
            'by_operation': counts_by_operation,
            'by_entity': counts_by_entity,
        },
        'operations': operations,
    }
    if target_state is not None:
        payload['target_state'] = build_target_state_payload(target_state)
    if release_selection is not None:
        payload['capability'] = _capability_payload(release_selection)
    if managed_objects is not None:
        payload['managed_objects'] = list(managed_objects)
    return payload


def build_release_manifest_payload(
    bundle_id: str,
    *,
    target_state: ManagedDataTargetState,
    release_selection: ReleasePlanSelection,
    selection_mode: ReleaseSelectionMode = 'full-declarations',
) -> dict[str, Any]:
    """Build the frozen release visibility manifest payload."""

    payload = {
        'version': '1',
        'bundle_id': bundle_id,
        'artifact_type': 'release-manifest',
        'release_key': release_selection.release_key,
        'selection_mode': selection_mode,
        'include': {
            'menu_ids': sorted(target_state.menus.keys()),
            'role_grants': [
                {'role_key': role_key, 'menu_ids': list(menu_ids_for_role)}
                for role_key, menu_ids_for_role in sorted(target_state.role_grants.items())
            ],
            'dict_types': sorted(target_state.dict_types.keys()),
            'config_keys': sorted(target_state.configs.keys()),
        },
    }
    payload['capability'] = _capability_payload(release_selection)
    return payload


def build_target_state_payload(target_state: ManagedDataTargetState) -> dict[str, Any]:
    """Serialize a target state snapshot into a stable payload."""

    return {
        'menus': {str(menu_id): row for menu_id, row in sorted(target_state.menus.items())},
        'role_grants': {role_key: list(menu_ids) for role_key, menu_ids in sorted(target_state.role_grants.items())},
        'dict_types': dict(sorted(target_state.dict_types.items())),
        'dict_data': {
            f'{dict_type}:{dict_value}': row for (dict_type, dict_value), row in sorted(target_state.dict_data.items())
        },
        'configs': dict(sorted(target_state.configs.items())),
    }


def load_target_state_payload(payload: dict[str, Any]):
    """Deserialize a managed-data target_state payload back into runtime state."""

    managed_data_target_state_type = importlib.import_module(
        'scripts.internal.db_workflow.managed_data_declaration_loader'
    ).ManagedDataTargetState

    menus = {int(menu_id): dict(row) for menu_id, row in dict(payload.get('menus') or {}).items()}
    role_grants = {
        str(role_key): tuple(int(menu_id) for menu_id in menu_ids)
        for role_key, menu_ids in dict(payload.get('role_grants') or {}).items()
    }
    dict_types = {
        str(dict_type): release_row('sys_dict_type', row)
        for dict_type, row in dict(payload.get('dict_types') or {}).items()
    }
    dict_data = {
        (str(dict_type), str(dict_value)): release_row('sys_dict_data', row)
        for combined_key, row in dict(payload.get('dict_data') or {}).items()
        for dict_type, _, dict_value in [str(combined_key).partition(':')]
    }
    configs = {
        str(config_key): release_row('sys_config', row)
        for config_key, row in dict(payload.get('configs') or {}).items()
    }
    return managed_data_target_state_type(
        menus=menus,
        role_grants=role_grants,
        dict_types=dict_types,
        dict_data=dict_data,
        configs=configs,
    )


def load_capability_payload(payload: dict[str, Any], *, artifact_name: str) -> dict[str, Any]:
    capability = payload.get('capability')
    if not isinstance(capability, dict):
        raise ValueError(f'{artifact_name} missing capability metadata')

    compiled_checksum = capability.get('compiled_checksum')
    release_plan_checksum = capability.get('release_plan_checksum')
    modules = capability.get('modules')
    enabled_modules = capability.get('enabled_modules')
    runtime_gates = capability.get('runtime_gates') or {}
    if not isinstance(compiled_checksum, str) or not compiled_checksum:
        raise ValueError(f'{artifact_name} missing compiled_checksum')
    if not isinstance(release_plan_checksum, str) or not release_plan_checksum:
        raise ValueError(f'{artifact_name} missing release_plan_checksum')
    if not isinstance(modules, dict):
        raise ValueError(f'{artifact_name} missing capability modules payload')
    if not isinstance(enabled_modules, list):
        raise ValueError(f'{artifact_name} missing enabled_modules payload')
    if not isinstance(runtime_gates, dict):
        raise ValueError(f'{artifact_name} runtime_gates must be a mapping when present')

    return {
        'compiled_checksum': compiled_checksum,
        'release_plan_checksum': release_plan_checksum,
        'modules': {str(module_key): bool(enabled) for module_key, enabled in modules.items()},
        'enabled_modules': tuple(str(module_key) for module_key in enabled_modules),
        'runtime_gates': {
            str(module_key): {
                'config_key': str(gate.get('config_key') or '').strip(),
                'default_enabled': bool(gate.get('default_enabled')),
            }
            for module_key, gate in runtime_gates.items()
            if isinstance(gate, dict) and str(gate.get('config_key') or '').strip()
        },
    }


def load_managed_object_snapshot(payload: dict[str, Any], *, artifact_name: str) -> list[dict[str, Any]]:
    managed_objects = payload.get('managed_objects')
    if not isinstance(managed_objects, list):
        raise ValueError(f'{artifact_name} missing managed_objects snapshot')

    normalized: list[dict[str, Any]] = []
    required_fields = (
        'object_type',
        'object_key',
        'module_key',
        'object_domain',
        'owner_scope',
        'source_path',
        'source_checksum',
        'checksum',
    )
    for index, row in enumerate(managed_objects):
        if not isinstance(row, dict):
            raise ValueError(f'{artifact_name} managed_objects[{index}] must be a mapping')
        missing = [
            field for field in required_fields if not isinstance(row.get(field), str) or not str(row[field]).strip()
        ]
        if missing:
            raise ValueError(f'{artifact_name} managed_objects[{index}] missing fields: {", ".join(missing)}')
        normalized.append({field: str(row[field]).strip() for field in required_fields})

    return sorted(normalized, key=lambda item: (item['object_type'], item['object_key']))


def _capability_payload(release_selection: ReleasePlanSelection) -> dict[str, Any]:
    return {
        'compiled_checksum': release_selection.compiled_checksum,
        'release_plan_checksum': release_selection.release_plan_checksum,
        'modules': dict(sorted(release_selection.modules.items())),
        'enabled_modules': list(release_selection.enabled_modules),
        'runtime_gates': {
            module_key: {
                'config_key': gate.config_key,
                'default_enabled': gate.default_enabled,
            }
            for module_key, gate in sorted(release_selection.runtime_gates.items())
        },
    }


def render_bundle_yaml(payload: dict[str, Any]) -> str:
    """Render payload into the committed YAML bundle format."""

    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


def compute_payload_checksum(payload: dict[str, Any]) -> str:
    """Compute a canonical SHA-256 checksum for YAML payload contents."""

    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return compute_text_checksum(canonical)


def compute_text_checksum(payload: str) -> str:
    return sha256(payload.encode('utf-8')).hexdigest()


def _format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return normalized.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
