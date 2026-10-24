"""Capability declaration compiler and migration adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from modules.system.runtime.menu_registry_loader import (
    COMPONENT_PATH_PATTERN,
    FLAG_SET,
    INTEGER_MENU_FIELDS,
    MENU_FIELDS,
    MENU_TYPE_SET,
    REQUIRED_MENU_FIELDS,
    MenuRegistryLoader,
)

from .capability_models import (
    CapabilityCompilationChecksums,
    CapabilityResourceState,
    CapabilityRuntimeGate,
    CompiledCapabilityState,
    ModuleCapabilityDeclaration,
)
from .release_bundle_service import compute_payload_checksum

BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CAPABILITY_MODULES_DIR = BACKEND_ROOT / 'capabilities' / 'modules'

STATUS_FLAG_SET = {'0', '1'}
YES_NO_FLAG_SET = {'Y', 'N'}
MENU_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_.:-]+$')
RUNTIME_GATE_CONFIG_ID_MIN = -2_000_000_000
RUNTIME_GATE_CONFIG_ID_MAX = -1
_SourceKind = Literal['manifest']


@dataclass(frozen=True)
class CapabilityDeclarationIssue:
    """Structured compiler validation issue."""

    domain: str
    source_path: str
    location: str
    message: str


@dataclass
class _ModuleDraft:
    module_key: str
    source_path: Path
    source_kind: _SourceKind
    dependencies: set[str] = field(default_factory=set)
    resources: CapabilityResourceState = field(default_factory=CapabilityResourceState)
    runtime_gate: CapabilityRuntimeGate | None = None
    menu_ids_by_key: dict[str, int] = field(default_factory=dict)
    menu_keys_by_id: dict[int, str] = field(default_factory=dict)
    menu_parent_refs: dict[str, tuple[int, str | None]] = field(default_factory=dict)

    def as_declaration(self) -> ModuleCapabilityDeclaration:
        return ModuleCapabilityDeclaration(
            module_key=self.module_key,
            source_path=self.source_path,
            dependencies=tuple(sorted(self.dependencies)),
            resources=_sorted_resources(self.resources),
            runtime_gate=self.runtime_gate,
        )


@dataclass(frozen=True)
class _MenuOwner:
    module_key: str
    menu_key: str
    menu_id: int
    source_path: Path


class ModuleManifestAdapter:
    """Read future-state `*.module.yaml` declarations."""

    def __init__(
        self,
        *,
        modules_root: str | Path | None = None,
        known_role_keys: set[str] | frozenset[str] | None = None,
    ) -> None:
        self.modules_root = Path(modules_root) if modules_root else DEFAULT_CAPABILITY_MODULES_DIR
        self.known_role_keys = set(known_role_keys or ())

    def adapt(
        self,
    ) -> tuple[list[_ModuleDraft], list[CapabilityDeclarationIssue], list[tuple[str, dict[str, Any]]]]:
        if not self.modules_root.exists():
            return [], [], []

        drafts: list[_ModuleDraft] = []
        issues: list[CapabilityDeclarationIssue] = []
        source_payloads: list[tuple[str, dict[str, Any]]] = []

        for manifest_path in sorted(self.modules_root.glob('*.module.yaml')):
            payload, load_issues = _load_yaml_mapping(manifest_path, domain='modules')
            issues.extend(load_issues)
            if payload is None:
                continue
            source_payloads.append((str(manifest_path), payload))

            module_key = _normalize_identifier(payload.get('module_key'))
            if module_key is None:
                issues.append(_issue('modules', manifest_path, 'module_key', 'module_key must be a non-empty string'))
                continue

            dependencies = _normalize_string_list(
                payload.get('dependencies', []),
                domain='modules',
                source_path=manifest_path,
                location='dependencies',
                issues=issues,
            )

            draft = _ModuleDraft(
                module_key=module_key,
                source_path=manifest_path,
                source_kind='manifest',
                dependencies=set(dependencies),
            )

            menus = self._normalize_menus(manifest_path, payload.get('menus', []), issues)
            draft.resources = CapabilityResourceState(
                menus={menu_id: row for menu_id, (_, row, _) in menus.items()},
                role_grants=self._normalize_role_grants(manifest_path, payload.get('role_grants', []), menus, issues),
                dict_types=self._normalize_dict_types(manifest_path, payload.get('dict_types', []), issues),
                dict_data={},
                configs={},
            )
            draft.menu_ids_by_key = {menu_key: menu_id for menu_id, (menu_key, _, _) in menus.items()}
            draft.menu_keys_by_id = {menu_id: menu_key for menu_id, (menu_key, _, _) in menus.items()}
            draft.menu_parent_refs = {
                menu_key: (int(row['parent_id']), parent_menu_key)
                for menu_id, (menu_key, row, parent_menu_key) in menus.items()
            }

            dict_data_map = self._normalize_dict_data(
                manifest_path,
                payload.get('dict_data', []),
                declared_dict_types=set(draft.resources.dict_types),
                issues=issues,
            )
            config_map = self._normalize_configs(manifest_path, payload.get('configs', []), issues)
            draft.resources = CapabilityResourceState(
                menus=draft.resources.menus,
                role_grants=draft.resources.role_grants,
                dict_types=draft.resources.dict_types,
                dict_data=dict_data_map,
                configs=config_map,
            )
            draft.runtime_gate = self._normalize_runtime_gate(
                manifest_path,
                module_key=module_key,
                payload=payload.get('runtime_gate'),
                issues=issues,
            )

            drafts.append(draft)

        return drafts, issues, source_payloads

    def _normalize_menus(  # noqa: PLR0912, PLR0915
        self,
        source_path: Path,
        payload: Any,
        issues: list[CapabilityDeclarationIssue],
    ) -> dict[int, tuple[str, dict[str, Any], str | None]]:
        if payload is None:
            return {}
        if not isinstance(payload, list):
            issues.append(_issue('menus', source_path, 'menus', 'menus must be a list'))
            return {}

        seen_menu_ids: set[int] = set()
        seen_menu_keys: set[str] = set()
        normalized: dict[int, tuple[str, dict[str, Any], str | None]] = {}

        for index, row in enumerate(payload):
            prefix = f'menus[{index}]'
            if not isinstance(row, dict):
                issues.append(_issue('menus', source_path, prefix, 'menu item must be a mapping'))
                continue

            menu_key = _normalize_identifier(row.get('menu_key'))
            if menu_key is None:
                issues.append(_issue('menus', source_path, f'{prefix}.menu_key', 'menu_key must be a non-empty string'))
                continue
            if not MENU_KEY_PATTERN.fullmatch(menu_key):
                issues.append(
                    _issue('menus', source_path, f'{prefix}.menu_key', 'menu_key contains invalid characters')
                )
                continue
            if menu_key in seen_menu_keys:
                issues.append(_issue('menus', source_path, f'{prefix}.menu_key', f'duplicate menu_key: {menu_key}'))
                continue
            seen_menu_keys.add(menu_key)

            missing_fields = [field_name for field_name in REQUIRED_MENU_FIELDS if field_name not in row]
            if missing_fields:
                issues.append(
                    _issue('menus', source_path, prefix, f'missing required fields: {", ".join(missing_fields)}')
                )
                continue

            menu_id_value = row.get('menu_id')
            if not MenuRegistryLoader._is_int_like(menu_id_value):
                issues.append(_issue('menus', source_path, f'{prefix}.menu_id', 'menu_id must be an integer'))
                continue
            menu_id = int(menu_id_value)
            if menu_id in seen_menu_ids:
                issues.append(_issue('menus', source_path, f'{prefix}.menu_id', f'duplicate menu_id: {menu_id}'))
                continue
            seen_menu_ids.add(menu_id)

            issues.extend(
                _issue('menus', source_path, f'{prefix}.{field_name}', f'{field_name} must be an integer')
                for field_name in INTEGER_MENU_FIELDS
                if field_name in row and not MenuRegistryLoader._is_int_like(row[field_name])
            )

            menu_type = str(row.get('menu_type'))
            if menu_type not in MENU_TYPE_SET:
                issues.append(
                    _issue('menus', source_path, f'{prefix}.menu_type', f'menu_type must be one of {sorted(MENU_TYPE_SET)}')
                )

            if str(row.get('visible')) not in FLAG_SET:
                issues.append(_issue('menus', source_path, f'{prefix}.visible', 'visible must be "0" or "1"'))
            if str(row.get('status')) not in FLAG_SET:
                issues.append(_issue('menus', source_path, f'{prefix}.status', 'status must be "0" or "1"'))

            menu_name = row.get('menu_name')
            if not isinstance(menu_name, str) or not menu_name.strip():
                issues.append(_issue('menus', source_path, f'{prefix}.menu_name', 'menu_name must be a non-empty string'))

            if not isinstance(row.get('path'), str):
                issues.append(_issue('menus', source_path, f'{prefix}.path', 'path must be a string'))

            component = row.get('component')
            if menu_type == 'C':
                if not isinstance(component, str) or not component.strip():
                    issues.append(_issue('menus', source_path, f'{prefix}.component', 'component is required for menu_type=C'))
                elif not COMPONENT_PATH_PATTERN.match(component.strip()):
                    issues.append(_issue('menus', source_path, f'{prefix}.component', 'component contains invalid characters'))
            elif component is not None and not isinstance(component, str):
                issues.append(
                    _issue('menus', source_path, f'{prefix}.component', 'component must be null or string for non-C menus')
                )

            parent_menu_key = _normalize_identifier(row.get('parent_menu_key'))
            if parent_menu_key == menu_key:
                issues.append(
                    _issue('menus', source_path, f'{prefix}.parent_menu_key', 'parent_menu_key cannot reference itself')
                )

            normalized[menu_id] = (menu_key, _normalize_menu_row(row), parent_menu_key)

        return normalized

    def _normalize_role_grants(
        self,
        source_path: Path,
        payload: Any,
        menus: dict[int, tuple[str, dict[str, Any], str | None]],
        issues: list[CapabilityDeclarationIssue],
    ) -> dict[str, tuple[int, ...]]:
        if payload is None:
            return {}
        if not isinstance(payload, list):
            issues.append(_issue('role_grants', source_path, 'role_grants', 'role_grants must be a list'))
            return {}

        menu_ids_by_key = {menu_key: menu_id for menu_id, (menu_key, _, _) in menus.items()}
        role_grants: dict[str, set[int]] = {}
        seen_role_keys: set[str] = set()

        for index, row in enumerate(payload):
            prefix = f'role_grants[{index}]'
            if not isinstance(row, dict):
                issues.append(_issue('role_grants', source_path, prefix, 'role grant must be a mapping'))
                continue

            role_key = _normalize_identifier(row.get('role_key'))
            if role_key is None:
                issues.append(_issue('role_grants', source_path, f'{prefix}.role_key', 'role_key must be a non-empty string'))
                continue
            if role_key in seen_role_keys:
                issues.append(_issue('role_grants', source_path, f'{prefix}.role_key', f'duplicate role_key: {role_key}'))
            seen_role_keys.add(role_key)
            if self.known_role_keys and role_key not in self.known_role_keys:
                issues.append(_issue('role_grants', source_path, f'{prefix}.role_key', f'role_key not found in known roles: {role_key}'))

            menu_keys = row.get('menu_keys', [])
            if not isinstance(menu_keys, list):
                issues.append(_issue('role_grants', source_path, f'{prefix}.menu_keys', 'menu_keys must be a list'))
                continue

            resolved_menu_ids: set[int] = set()
            seen_menu_keys: set[str] = set()
            for menu_index, raw_menu_key in enumerate(menu_keys):
                location = f'{prefix}.menu_keys[{menu_index}]'
                menu_key = _normalize_identifier(raw_menu_key)
                if menu_key is None:
                    issues.append(_issue('role_grants', source_path, location, 'menu_key must be a non-empty string'))
                    continue
                if menu_key in seen_menu_keys:
                    issues.append(_issue('role_grants', source_path, location, f'duplicate menu_key: {menu_key}'))
                    continue
                seen_menu_keys.add(menu_key)
                menu_id = menu_ids_by_key.get(menu_key)
                if menu_id is None:
                    issues.append(_issue('role_grants', source_path, location, f'menu_key is not declared in this module: {menu_key}'))
                    continue
                resolved_menu_ids.add(menu_id)

            role_grants[role_key] = tuple(sorted(resolved_menu_ids))

        return {role_key: tuple(sorted(menu_ids)) for role_key, menu_ids in sorted(role_grants.items())}

    def _normalize_dict_types(
        self,
        source_path: Path,
        payload: Any,
        issues: list[CapabilityDeclarationIssue],
    ) -> dict[str, dict[str, Any]]:
        rows = _normalize_mapping_list(payload, domain='dict_types', source_path=source_path, location='dict_types', issues=issues)
        seen_ids: set[int] = set()
        seen_keys: set[str] = set()
        result: dict[str, dict[str, Any]] = {}

        for index, row in rows:
            prefix = f'dict_types[{index}]'
            missing_fields = [field for field in ('dict_id', 'dict_name', 'dict_type', 'status') if field not in row]
            if missing_fields:
                issues.append(_issue('dict_types', source_path, prefix, f'missing required fields: {", ".join(missing_fields)}'))
                continue
            normalized = _normalize_dict_type_row(row, source_path=source_path, location=prefix, issues=issues)
            if normalized is None:
                continue
            if int(normalized['dict_id']) in seen_ids:
                issues.append(_issue('dict_types', source_path, f'{prefix}.dict_id', f'duplicate dict_id: {normalized["dict_id"]}'))
                continue
            if normalized['dict_type'] in seen_keys:
                issues.append(
                    _issue('dict_types', source_path, f'{prefix}.dict_type', f'duplicate dict_type: {normalized["dict_type"]}')
                )
                continue
            seen_ids.add(int(normalized['dict_id']))
            seen_keys.add(normalized['dict_type'])
            result[normalized['dict_type']] = normalized

        return result

    def _normalize_dict_data(
        self,
        source_path: Path,
        payload: Any,
        *,
        declared_dict_types: set[str],
        issues: list[CapabilityDeclarationIssue],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        rows = _normalize_mapping_list(payload, domain='dict_data', source_path=source_path, location='dict_data', issues=issues)
        seen_codes: set[int] = set()
        seen_keys: set[tuple[str, str]] = set()
        result: dict[tuple[str, str], dict[str, Any]] = {}

        for index, row in rows:
            prefix = f'dict_data[{index}]'
            missing_fields = [
                field for field in ('dict_code', 'dict_sort', 'dict_label', 'dict_value', 'dict_type', 'is_default', 'status')
                if field not in row
            ]
            if missing_fields:
                issues.append(_issue('dict_data', source_path, prefix, f'missing required fields: {", ".join(missing_fields)}'))
                continue
            normalized = _normalize_dict_data_row(row, source_path=source_path, location=prefix, issues=issues)
            if normalized is None:
                continue
            business_key = (normalized['dict_type'], normalized['dict_value'])
            if normalized['dict_type'] not in declared_dict_types:
                issues.append(
                    _issue('dict_data', source_path, f'{prefix}.dict_type', f'dict_type is not declared in this module: {normalized["dict_type"]}')
                )
                continue
            if int(normalized['dict_code']) in seen_codes:
                issues.append(_issue('dict_data', source_path, f'{prefix}.dict_code', f'duplicate dict_code: {normalized["dict_code"]}'))
                continue
            if business_key in seen_keys:
                issues.append(
                    _issue(
                        'dict_data',
                        source_path,
                        f'{prefix}.dict_value',
                        f'duplicate dict_type + dict_value pair: {business_key[0]}/{business_key[1]}',
                    )
                )
                continue
            seen_codes.add(int(normalized['dict_code']))
            seen_keys.add(business_key)
            result[business_key] = normalized

        return result

    def _normalize_configs(
        self,
        source_path: Path,
        payload: Any,
        issues: list[CapabilityDeclarationIssue],
    ) -> dict[str, dict[str, Any]]:
        rows = _normalize_mapping_list(payload, domain='configs', source_path=source_path, location='configs', issues=issues)
        seen_ids: set[int] = set()
        seen_keys: set[str] = set()
        result: dict[str, dict[str, Any]] = {}

        for index, row in rows:
            prefix = f'configs[{index}]'
            missing_fields = [field for field in ('config_id', 'config_name', 'config_key', 'config_value', 'config_type') if field not in row]
            if missing_fields:
                issues.append(_issue('configs', source_path, prefix, f'missing required fields: {", ".join(missing_fields)}'))
                continue
            normalized = _normalize_config_row(row, source_path=source_path, location=prefix, issues=issues)
            if normalized is None:
                continue
            if int(normalized['config_id']) in seen_ids:
                issues.append(_issue('configs', source_path, f'{prefix}.config_id', f'duplicate config_id: {normalized["config_id"]}'))
                continue
            if normalized['config_key'] in seen_keys:
                issues.append(
                    _issue('configs', source_path, f'{prefix}.config_key', f'duplicate config_key: {normalized["config_key"]}')
                )
                continue
            seen_ids.add(int(normalized['config_id']))
            seen_keys.add(normalized['config_key'])
            result[normalized['config_key']] = normalized

        return result

    def _normalize_runtime_gate(
        self,
        source_path: Path,
        *,
        module_key: str,
        payload: Any,
        issues: list[CapabilityDeclarationIssue],
    ) -> CapabilityRuntimeGate | None:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            issues.append(_issue('runtime_gates', source_path, 'runtime_gate', 'runtime_gate must be a mapping'))
            return None

        config_key = _normalize_identifier(payload.get('config_key'))
        if config_key is None:
            issues.append(_issue('runtime_gates', source_path, 'runtime_gate.config_key', 'config_key must be a non-empty string'))
            return None

        default_enabled_raw = payload.get('default_enabled', False)
        if not isinstance(default_enabled_raw, bool):
            issues.append(
                _issue('runtime_gates', source_path, 'runtime_gate.default_enabled', 'default_enabled must be a boolean')
            )
            return None

        return CapabilityRuntimeGate(
            module_key=module_key,
            config_key=config_key,
            default_enabled=default_enabled_raw,
        )


class CapabilityDeclarationCompiler:
    """Compile module manifests into one target state."""

    def __init__(
        self,
        *,
        modules_root: str | Path | None = None,
        known_role_keys: set[str] | frozenset[str] | None = None,
    ) -> None:
        self.modules_root = Path(modules_root) if modules_root else DEFAULT_CAPABILITY_MODULES_DIR
        self.known_role_keys = set(known_role_keys or ())

    def validate(self) -> list[CapabilityDeclarationIssue]:
        _, issues = self._compile_internal()
        return issues

    def compile(self) -> CompiledCapabilityState:
        compiled_state, issues = self._compile_internal()
        if issues:
            raise ValueError(format_capability_issues(issues))
        assert compiled_state is not None
        return compiled_state

    def _compile_internal(self) -> tuple[CompiledCapabilityState | None, list[CapabilityDeclarationIssue]]:
        module_adapter = ModuleManifestAdapter(modules_root=self.modules_root, known_role_keys=self.known_role_keys)
        drafts, issues, source_payloads = module_adapter.adapt()
        if not drafts:
            issues.append(_issue('modules', self.modules_root, 'file', 'no module manifests found'))

        _materialize_runtime_gate_configs(drafts)
        issues.extend(self._validate_drafts(drafts))
        if issues:
            return None, _sorted_issues(issues)

        compiled_state = self._build_compiled_state(drafts, source_payloads=source_payloads)
        return compiled_state, []

    def _validate_drafts(self, drafts: list[_ModuleDraft]) -> list[CapabilityDeclarationIssue]:  # noqa: PLR0912, PLR0915
        issues: list[CapabilityDeclarationIssue] = []
        declared_module_keys = {draft.module_key for draft in drafts}

        menu_owner_by_key: dict[str, _MenuOwner] = {}
        menu_owner_by_id: dict[int, _MenuOwner] = {}
        dict_type_owner_by_key: dict[str, str] = {}
        dict_type_owner_by_id: dict[int, str] = {}
        dict_data_owner_by_key: dict[tuple[str, str], str] = {}
        dict_data_owner_by_code: dict[int, str] = {}
        config_owner_by_key: dict[str, str] = {}
        config_owner_by_id: dict[int, str] = {}
        role_grant_owner_by_identity: dict[tuple[str, int], str] = {}
        runtime_gate_by_module: dict[str, CapabilityRuntimeGate] = {}

        for draft in sorted(drafts, key=_validation_sort_key):
            for dependency in sorted(draft.dependencies):
                if dependency == draft.module_key:
                    issues.append(_issue('modules', draft.source_path, 'dependencies', 'module cannot depend on itself'))
                elif dependency not in declared_module_keys:
                    issues.append(
                        _issue('modules', draft.source_path, 'dependencies', f'unknown module dependency: {dependency}')
                    )

            for menu_key, menu_id in sorted(draft.menu_ids_by_key.items()):
                existing_menu_key = menu_owner_by_key.get(menu_key)
                if existing_menu_key is not None:
                    issues.append(
                        _issue(
                            'menus',
                            draft.source_path,
                            f'menu_key={menu_key}',
                            f'menu_key already owned by module {existing_menu_key.module_key}',
                        )
                    )
                else:
                    menu_owner_by_key[menu_key] = _MenuOwner(
                        module_key=draft.module_key,
                        menu_key=menu_key,
                        menu_id=menu_id,
                        source_path=draft.source_path,
                    )

                existing_menu_id = menu_owner_by_id.get(menu_id)
                if existing_menu_id is not None:
                    issues.append(
                        _issue(
                            'menus',
                            draft.source_path,
                            f'menu_id={menu_id}',
                            f'menu_id already owned by module {existing_menu_id.module_key}',
                        )
                    )
                else:
                    menu_owner_by_id[menu_id] = _MenuOwner(
                        module_key=draft.module_key,
                        menu_key=menu_key,
                        menu_id=menu_id,
                        source_path=draft.source_path,
                    )

            for dict_type, row in sorted(draft.resources.dict_types.items()):
                dict_id = int(row['dict_id'])
                if dict_type in dict_type_owner_by_key:
                    issues.append(
                        _issue('dict_types', draft.source_path, dict_type, f'dict_type already owned by module {dict_type_owner_by_key[dict_type]}')
                    )
                else:
                    dict_type_owner_by_key[dict_type] = draft.module_key
                if dict_id in dict_type_owner_by_id:
                    issues.append(
                        _issue('dict_types', draft.source_path, f'dict_id={dict_id}', f'dict_id already owned by module {dict_type_owner_by_id[dict_id]}')
                    )
                else:
                    dict_type_owner_by_id[dict_id] = draft.module_key

            for business_key, row in sorted(draft.resources.dict_data.items()):
                dict_code = int(row['dict_code'])
                owner_module = dict_type_owner_by_key.get(row['dict_type'])
                if owner_module is not None and owner_module != draft.module_key:
                    issues.append(
                        _issue(
                            'dict_data',
                            draft.source_path,
                            f'{business_key[0]}:{business_key[1]}',
                            f'dict_data ownership must follow dict_type owner: {owner_module}',
                        )
                    )
                if business_key in dict_data_owner_by_key:
                    issues.append(
                        _issue(
                            'dict_data',
                            draft.source_path,
                            f'{business_key[0]}:{business_key[1]}',
                            f'dict_data already owned by module {dict_data_owner_by_key[business_key]}',
                        )
                    )
                else:
                    dict_data_owner_by_key[business_key] = draft.module_key
                if dict_code in dict_data_owner_by_code:
                    issues.append(
                        _issue(
                            'dict_data',
                            draft.source_path,
                            f'dict_code={dict_code}',
                            f'dict_code already owned by module {dict_data_owner_by_code[dict_code]}',
                        )
                    )
                else:
                    dict_data_owner_by_code[dict_code] = draft.module_key

            for config_key, row in sorted(draft.resources.configs.items()):
                config_id = int(row['config_id'])
                if config_key in config_owner_by_key:
                    issues.append(
                        _issue('configs', draft.source_path, config_key, f'config_key already owned by module {config_owner_by_key[config_key]}')
                    )
                else:
                    config_owner_by_key[config_key] = draft.module_key
                if config_id in config_owner_by_id:
                    issues.append(
                        _issue('configs', draft.source_path, f'config_id={config_id}', f'config_id already owned by module {config_owner_by_id[config_id]}')
                    )
                else:
                    config_owner_by_id[config_id] = draft.module_key

        resolved_parent_graph: dict[str, str] = {}
        for draft in drafts:
            for menu_key, (parent_id, parent_menu_key) in sorted(draft.menu_parent_refs.items()):
                if parent_id == 0 and parent_menu_key is None:
                    continue

                parent_owner = None
                if parent_menu_key is not None:
                    parent_owner = menu_owner_by_key.get(parent_menu_key)
                    if parent_owner is None:
                        issues.append(
                            _issue('menus', draft.source_path, menu_key, f'parent_menu_key is not declared: {parent_menu_key}')
                        )
                        continue
                    if parent_id not in (0, parent_owner.menu_id):
                        issues.append(
                            _issue(
                                'menus',
                                draft.source_path,
                                menu_key,
                                f'parent_menu_key resolves to menu_id={parent_owner.menu_id}, expected parent_id={parent_id}',
                            )
                        )
                else:
                    parent_owner = menu_owner_by_id.get(parent_id)
                    if parent_owner is None:
                        issues.append(
                            _issue('menus', draft.source_path, menu_key, f'parent menu is not declared: {parent_id}')
                        )
                        continue

                resolved_parent_graph[menu_key] = parent_owner.menu_key
                if parent_owner.module_key == draft.module_key:
                    continue
                if parent_owner.module_key not in draft.dependencies:
                    issues.append(
                        _issue(
                            'modules',
                            draft.source_path,
                            menu_key,
                            f'module dependency missing for parent menu owner: {parent_owner.module_key}',
                        )
                    )

        for draft in drafts:
            for role_key, menu_ids in sorted(draft.resources.role_grants.items()):
                for menu_id in menu_ids:
                    menu_owner = menu_owner_by_id.get(menu_id)
                    if menu_owner is None:
                        issues.append(
                            _issue('role_grants', draft.source_path, role_key, f'role grant references undeclared menu_id: {menu_id}')
                        )
                        continue
                    if menu_owner.module_key != draft.module_key:
                        issues.append(
                            _issue(
                                'role_grants',
                                draft.source_path,
                                role_key,
                                f'role grant ownership must follow menu owner: {menu_owner.module_key}',
                            )
                        )
                    identity = (role_key, menu_id)
                    previous_owner = role_grant_owner_by_identity.get(identity)
                    if previous_owner is not None and previous_owner != draft.module_key:
                        issues.append(
                            _issue(
                                'role_grants',
                                draft.source_path,
                                role_key,
                                f'role grant already declared by module {previous_owner}: {menu_id}',
                            )
                        )
                    else:
                        role_grant_owner_by_identity[identity] = draft.module_key

            if draft.runtime_gate is not None:
                previous_gate = runtime_gate_by_module.get(draft.module_key)
                if previous_gate is not None and previous_gate != draft.runtime_gate:
                    issues.append(
                        _issue(
                            'runtime_gates',
                            draft.source_path,
                            draft.module_key,
                            f'runtime gate already declared for module {draft.module_key}',
                        )
                    )
                else:
                    runtime_gate_by_module[draft.module_key] = draft.runtime_gate
                config_owner = config_owner_by_key.get(draft.runtime_gate.config_key)
                if config_owner is not None and config_owner != draft.module_key:
                    issues.append(
                        _issue(
                            'runtime_gates',
                            draft.source_path,
                            draft.runtime_gate.config_key,
                            f'runtime gate config ownership must follow module owner: {config_owner}',
                        )
                    )

        issues.extend(_detect_dependency_cycles(drafts))
        issues.extend(_detect_menu_parent_cycles(drafts, resolved_parent_graph))
        return issues

    def _build_compiled_state(
        self,
        drafts: list[_ModuleDraft],
        *,
        source_payloads: list[tuple[str, dict[str, Any]]],
    ) -> CompiledCapabilityState:
        modules = _build_module_declarations(drafts)

        merged_menus: dict[int, dict[str, Any]] = {}
        merged_role_grants: dict[str, set[int]] = {}
        merged_dict_types: dict[str, dict[str, Any]] = {}
        merged_dict_data: dict[tuple[str, str], dict[str, Any]] = {}
        merged_configs: dict[str, dict[str, Any]] = {}
        runtime_gates: dict[str, CapabilityRuntimeGate] = {}

        for module_key, declaration in modules.items():
            merged_menus.update(declaration.resources.menus)
            merged_dict_types.update(declaration.resources.dict_types)
            merged_dict_data.update(declaration.resources.dict_data)
            merged_configs.update(declaration.resources.configs)
            for role_key, menu_ids in declaration.resources.role_grants.items():
                merged_role_grants.setdefault(role_key, set()).update(menu_ids)
            if declaration.runtime_gate is not None:
                runtime_gates[module_key] = declaration.runtime_gate

        compiled_resources = _sorted_resources(
            CapabilityResourceState(
                menus=merged_menus,
                role_grants={role_key: tuple(sorted(menu_ids)) for role_key, menu_ids in merged_role_grants.items()},
                dict_types=merged_dict_types,
                dict_data=merged_dict_data,
                configs=merged_configs,
            )
        )

        source_checksum = compute_payload_checksum(
            {
                'sources': [
                    {'path': path, 'payload': payload}
                    for path, payload in sorted(source_payloads, key=lambda item: item[0])
                ]
            }
        )
        compiled_checksum = compute_payload_checksum(_compiled_state_payload(modules, compiled_resources, runtime_gates))

        return CompiledCapabilityState(
            modules=modules,
            resources=compiled_resources,
            runtime_gates={module_key: runtime_gates[module_key] for module_key in sorted(runtime_gates)},
            checksums=CapabilityCompilationChecksums(
                source_checksum=source_checksum,
                compiled_checksum=compiled_checksum,
            ),
        )


def format_capability_issues(issues: list[CapabilityDeclarationIssue]) -> str:
    """Render compiler issues as one readable error string."""

    return '; '.join(
        f'[{issue.domain}] {issue.source_path}:{issue.location}: {issue.message}'
        for issue in _sorted_issues(issues)
    )


def _compiled_state_payload(
    modules: dict[str, ModuleCapabilityDeclaration],
    resources: CapabilityResourceState,
    runtime_gates: dict[str, CapabilityRuntimeGate],
) -> dict[str, Any]:
    return {
        'modules': {
            module_key: {
                'source_path': str(declaration.source_path),
                'dependencies': list(declaration.dependencies),
                'resources': _resources_payload(declaration.resources),
                'runtime_gate': (
                    {
                        'module_key': declaration.runtime_gate.module_key,
                        'config_key': declaration.runtime_gate.config_key,
                        'default_enabled': declaration.runtime_gate.default_enabled,
                    }
                    if declaration.runtime_gate is not None
                    else None
                ),
            }
            for module_key, declaration in modules.items()
        },
        'resources': _resources_payload(resources),
        'runtime_gates': {
            module_key: {
                'config_key': gate.config_key,
                'default_enabled': gate.default_enabled,
            }
            for module_key, gate in sorted(runtime_gates.items())
        },
    }


def _resources_payload(resources: CapabilityResourceState) -> dict[str, Any]:
    return {
        'menus': {str(menu_id): row for menu_id, row in sorted(resources.menus.items())},
        'role_grants': {role_key: list(menu_ids) for role_key, menu_ids in sorted(resources.role_grants.items())},
        'dict_types': dict(sorted(resources.dict_types.items())),
        'dict_data': {f'{dict_type}:{dict_value}': row for (dict_type, dict_value), row in sorted(resources.dict_data.items())},
        'configs': dict(sorted(resources.configs.items())),
    }


def _sorted_resources(resources: CapabilityResourceState) -> CapabilityResourceState:
    return CapabilityResourceState(
        menus={menu_id: resources.menus[menu_id] for menu_id in sorted(resources.menus)},
        role_grants={role_key: tuple(sorted(resources.role_grants[role_key])) for role_key in sorted(resources.role_grants)},
        dict_types={dict_type: resources.dict_types[dict_type] for dict_type in sorted(resources.dict_types)},
        dict_data={key: resources.dict_data[key] for key in sorted(resources.dict_data)},
        configs={config_key: resources.configs[config_key] for config_key in sorted(resources.configs)},
    )


def _materialize_runtime_gate_configs(drafts: list[_ModuleDraft]) -> None:
    used_config_ids = {
        int(row['config_id'])
        for draft in drafts
        for row in draft.resources.configs.values()
        if MenuRegistryLoader._is_int_like(row.get('config_id'))
    }

    for draft in sorted(drafts, key=_validation_sort_key):
        runtime_gate = draft.runtime_gate
        if runtime_gate is None or runtime_gate.config_key in draft.resources.configs:
            continue

        synthesized_config = _build_runtime_gate_config_row(
            module_key=draft.module_key,
            config_key=runtime_gate.config_key,
            default_enabled=runtime_gate.default_enabled,
            used_config_ids=used_config_ids,
        )
        draft.resources = CapabilityResourceState(
            menus=draft.resources.menus,
            role_grants=draft.resources.role_grants,
            dict_types=draft.resources.dict_types,
            dict_data=draft.resources.dict_data,
            configs={
                **draft.resources.configs,
                synthesized_config['config_key']: synthesized_config,
            },
        )
        used_config_ids.add(int(synthesized_config['config_id']))


def _build_runtime_gate_config_row(
    *,
    module_key: str,
    config_key: str,
    default_enabled: bool,
    used_config_ids: set[int],
) -> dict[str, Any]:
    return {
        'config_id': _allocate_runtime_gate_config_id(config_key=config_key, used_config_ids=used_config_ids),
        'config_name': f'Capability Gate: {module_key}',
        'config_key': config_key,
        'config_value': 'true' if default_enabled else 'false',
        'config_type': 'Y',
        'remark': f'Auto-generated runtime gate config for module {module_key}',
    }


def _allocate_runtime_gate_config_id(*, config_key: str, used_config_ids: set[int]) -> int:
    hash_fragment = compute_payload_checksum({'runtime_gate_config_key': config_key})[:8]
    candidate = -((int(hash_fragment, 16) % abs(RUNTIME_GATE_CONFIG_ID_MIN)) + 1)
    while candidate in used_config_ids:
        candidate -= 1
        if candidate < RUNTIME_GATE_CONFIG_ID_MIN:
            candidate = RUNTIME_GATE_CONFIG_ID_MAX
    return candidate


def _build_module_declarations(drafts: list[_ModuleDraft]) -> dict[str, ModuleCapabilityDeclaration]:
    grouped_drafts = _group_drafts_by_module_key(drafts)
    declarations: dict[str, ModuleCapabilityDeclaration] = {}

    for module_key, module_drafts in sorted(grouped_drafts.items()):
        merged_menus: dict[int, dict[str, Any]] = {}
        merged_role_grants: dict[str, set[int]] = {}
        merged_dict_types: dict[str, dict[str, Any]] = {}
        merged_dict_data: dict[tuple[str, str], dict[str, Any]] = {}
        merged_configs: dict[str, dict[str, Any]] = {}
        runtime_gate: CapabilityRuntimeGate | None = None

        for draft in sorted(module_drafts, key=_merge_sort_key):
            merged_menus.update(draft.resources.menus)
            merged_dict_types.update(draft.resources.dict_types)
            merged_dict_data.update(draft.resources.dict_data)
            merged_configs.update(draft.resources.configs)
            for role_key, menu_ids in draft.resources.role_grants.items():
                merged_role_grants.setdefault(role_key, set()).update(menu_ids)
            if draft.runtime_gate is not None:
                runtime_gate = draft.runtime_gate

        declarations[module_key] = ModuleCapabilityDeclaration(
            module_key=module_key,
            source_path=_select_primary_source_path(module_drafts),
            dependencies=tuple(sorted({dependency for draft in module_drafts for dependency in draft.dependencies})),
            resources=_sorted_resources(
                CapabilityResourceState(
                    menus=merged_menus,
                    role_grants={role_key: tuple(sorted(menu_ids)) for role_key, menu_ids in merged_role_grants.items()},
                    dict_types=merged_dict_types,
                    dict_data=merged_dict_data,
                    configs=merged_configs,
                )
            ),
            runtime_gate=runtime_gate,
        )

    return declarations


def _detect_dependency_cycles(drafts: list[_ModuleDraft]) -> list[CapabilityDeclarationIssue]:
    graph: dict[str, set[str]] = {}
    for draft in drafts:
        graph.setdefault(draft.module_key, set()).update(draft.dependencies)

    source_path_by_module = {
        module_key: _select_primary_source_path(module_drafts)
        for module_key, module_drafts in _group_drafts_by_module_key(drafts).items()
    }
    issues: list[CapabilityDeclarationIssue] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(module_key: str, trail: list[str]) -> None:
        if module_key in visited:
            return
        if module_key in visiting:
            cycle = [*trail[trail.index(module_key):], module_key]
            source_path = source_path_by_module.get(module_key, Path())
            issues.append(
                _issue('modules', source_path, module_key, f'module dependency cycle detected: {" -> ".join(cycle)}')
            )
            return

        visiting.add(module_key)
        for dependency in sorted(graph.get(module_key, ())):
            dfs(dependency, [*trail, dependency])
        visiting.remove(module_key)
        visited.add(module_key)

    for module_key in sorted(graph):
        dfs(module_key, [module_key])
    return issues


def _detect_menu_parent_cycles(
    drafts: list[_ModuleDraft],
    parent_graph: dict[str, str],
) -> list[CapabilityDeclarationIssue]:
    issues: list[CapabilityDeclarationIssue] = []
    source_path_by_menu_key = {
        menu_key: draft.source_path
        for draft in drafts
        for menu_key in draft.menu_ids_by_key
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(menu_key: str, trail: list[str]) -> None:
        if menu_key in visited:
            return
        if menu_key in visiting:
            cycle = [*trail[trail.index(menu_key):], menu_key]
            issues.append(
                _issue(
                    'menus',
                    source_path_by_menu_key.get(menu_key, Path()),
                    menu_key,
                    f'parent menu cycle detected: {" -> ".join(cycle)}',
                )
            )
            return
        visiting.add(menu_key)
        parent_key = parent_graph.get(menu_key)
        if parent_key is not None:
            dfs(parent_key, [*trail, parent_key])
        visiting.remove(menu_key)
        visited.add(menu_key)

    for menu_key in sorted(parent_graph):
        dfs(menu_key, [menu_key])
    return issues


def _load_yaml_mapping(
    path: Path,
    *,
    domain: str,
) -> tuple[dict[str, Any] | None, list[CapabilityDeclarationIssue]]:
    if not path.exists():
        return None, [_issue(domain, path, 'file', 'declaration file does not exist')]
    try:
        payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except yaml.YAMLError as exc:
        return None, [_issue(domain, path, 'file', f'invalid YAML: {exc}')]
    if not isinstance(payload, dict):
        return None, [_issue(domain, path, 'root', 'YAML payload must be a mapping')]
    return payload, []


def _normalize_mapping_list(
    payload: Any,
    *,
    domain: str,
    source_path: Path,
    location: str,
    issues: list[CapabilityDeclarationIssue],
) -> list[tuple[int, dict[str, Any]]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        issues.append(_issue(domain, source_path, location, f'{location} must be a list'))
        return []

    normalized: list[tuple[int, dict[str, Any]]] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            issues.append(_issue(domain, source_path, f'{location}[{index}]', 'item must be a mapping'))
            continue
        normalized.append((index, row))
    return normalized


def _normalize_menu_row(raw_row: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        'query': None,
        'route_name': '',
        'component': None,
        'perms': '',
        'icon': '',
        'remark': '',
    }
    normalized: dict[str, Any] = {}

    for field_name in MENU_FIELDS:
        value = raw_row.get(field_name, defaults.get(field_name))
        if field_name in INTEGER_MENU_FIELDS:
            value = int(value)
        elif field_name in {'visible', 'status', 'menu_type'}:
            value = str(value)
        elif field_name in {'menu_name', 'path', 'route_name', 'perms', 'icon', 'remark'} and value is None:
            value = ''
        normalized[field_name] = value

    return normalized


def _normalize_dict_type_row(
    row: dict[str, Any],
    *,
    source_path: Path,
    location: str,
    issues: list[CapabilityDeclarationIssue],
) -> dict[str, Any] | None:
    if not MenuRegistryLoader._is_int_like(row.get('dict_id')):
        issues.append(_issue('dict_types', source_path, f'{location}.dict_id', 'dict_id must be an integer'))
        return None
    dict_name = row.get('dict_name')
    if not isinstance(dict_name, str) or not dict_name.strip():
        issues.append(_issue('dict_types', source_path, f'{location}.dict_name', 'dict_name must be a non-empty string'))
        return None
    dict_type = _normalize_identifier(row.get('dict_type'))
    if dict_type is None:
        issues.append(_issue('dict_types', source_path, f'{location}.dict_type', 'dict_type must be a non-empty string'))
        return None
    status = str(row.get('status'))
    if status not in STATUS_FLAG_SET:
        issues.append(_issue('dict_types', source_path, f'{location}.status', 'status must be "0" or "1"'))
        return None
    remark = row.get('remark')
    if remark is not None and not isinstance(remark, str):
        issues.append(_issue('dict_types', source_path, f'{location}.remark', 'remark must be null or string'))
        return None
    return {
        'dict_id': int(row['dict_id']),
        'dict_name': dict_name.strip(),
        'dict_type': dict_type,
        'status': status,
        'remark': '' if remark is None else remark,
    }


def _normalize_dict_data_row(
    row: dict[str, Any],
    *,
    source_path: Path,
    location: str,
    issues: list[CapabilityDeclarationIssue],
) -> dict[str, Any] | None:
    int_fields = ('dict_code', 'dict_sort')
    for field_name in int_fields:
        if not MenuRegistryLoader._is_int_like(row.get(field_name)):
            issues.append(_issue('dict_data', source_path, f'{location}.{field_name}', f'{field_name} must be an integer'))
            return None
    required_text_fields = ('dict_label', 'dict_value', 'dict_type')
    normalized_text: dict[str, str] = {}
    for field_name in required_text_fields:
        value = row.get(field_name)
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue('dict_data', source_path, f'{location}.{field_name}', f'{field_name} must be a non-empty string')
            )
            return None
        normalized_text[field_name] = value.strip()
    if str(row.get('is_default')) not in YES_NO_FLAG_SET:
        issues.append(_issue('dict_data', source_path, f'{location}.is_default', 'is_default must be "Y" or "N"'))
        return None
    if str(row.get('status')) not in STATUS_FLAG_SET:
        issues.append(_issue('dict_data', source_path, f'{location}.status', 'status must be "0" or "1"'))
        return None
    return {
        'dict_code': int(row['dict_code']),
        'dict_sort': int(row['dict_sort']),
        'dict_label': normalized_text['dict_label'],
        'dict_value': normalized_text['dict_value'],
        'dict_type': normalized_text['dict_type'],
        'css_class': '' if row.get('css_class') is None else str(row.get('css_class')),
        'list_class': '' if row.get('list_class') is None else str(row.get('list_class')),
        'is_default': str(row['is_default']),
        'status': str(row['status']),
        'remark': '' if row.get('remark') is None else str(row.get('remark')),
    }


def _normalize_config_row(
    row: dict[str, Any],
    *,
    source_path: Path,
    location: str,
    issues: list[CapabilityDeclarationIssue],
) -> dict[str, Any] | None:
    if not MenuRegistryLoader._is_int_like(row.get('config_id')):
        issues.append(_issue('configs', source_path, f'{location}.config_id', 'config_id must be an integer'))
        return None
    config_name = row.get('config_name')
    if not isinstance(config_name, str) or not config_name.strip():
        issues.append(_issue('configs', source_path, f'{location}.config_name', 'config_name must be a non-empty string'))
        return None
    config_key = _normalize_identifier(row.get('config_key'))
    if config_key is None:
        issues.append(_issue('configs', source_path, f'{location}.config_key', 'config_key must be a non-empty string'))
        return None
    config_value = row.get('config_value')
    if not isinstance(config_value, str):
        issues.append(_issue('configs', source_path, f'{location}.config_value', 'config_value must be a string'))
        return None
    config_type = str(row.get('config_type'))
    if config_type not in YES_NO_FLAG_SET:
        issues.append(_issue('configs', source_path, f'{location}.config_type', 'config_type must be "Y" or "N"'))
        return None
    return {
        'config_id': int(row['config_id']),
        'config_name': config_name.strip(),
        'config_key': config_key,
        'config_value': config_value,
        'config_type': config_type,
        'remark': '' if row.get('remark') is None else str(row.get('remark')),
    }


def _normalize_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_string_list(
    payload: Any,
    *,
    domain: str,
    source_path: Path,
    location: str,
    issues: list[CapabilityDeclarationIssue],
) -> tuple[str, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        issues.append(_issue(domain, source_path, location, f'{location} must be a list'))
        return ()
    normalized_values: list[str] = []
    seen: set[str] = set()
    for index, raw_value in enumerate(payload):
        normalized = _normalize_identifier(raw_value)
        if normalized is None:
            issues.append(_issue(domain, source_path, f'{location}[{index}]', 'value must be a non-empty string'))
            continue
        if normalized in seen:
            issues.append(_issue(domain, source_path, f'{location}[{index}]', f'duplicate value: {normalized}'))
            continue
        seen.add(normalized)
        normalized_values.append(normalized)
    return tuple(normalized_values)


def _issue(domain: str, source_path: Path, location: str, message: str) -> CapabilityDeclarationIssue:
    return CapabilityDeclarationIssue(domain=domain, source_path=str(source_path), location=location, message=message)


def _group_drafts_by_module_key(drafts: list[_ModuleDraft]) -> dict[str, list[_ModuleDraft]]:
    grouped: dict[str, list[_ModuleDraft]] = {}
    for draft in drafts:
        grouped.setdefault(draft.module_key, []).append(draft)
    return grouped


def _select_primary_source_path(drafts: list[_ModuleDraft]) -> Path:
    return sorted(drafts, key=_merge_sort_key)[0].source_path


def _merge_sort_key(draft: _ModuleDraft) -> tuple[int, str, str]:
    return (0, draft.module_key, str(draft.source_path))


def _validation_sort_key(draft: _ModuleDraft) -> tuple[int, str, str]:
    return (0, draft.module_key, str(draft.source_path))


def _sorted_issues(issues: list[CapabilityDeclarationIssue]) -> list[CapabilityDeclarationIssue]:
    return sorted(issues, key=lambda issue: (issue.domain, issue.source_path, issue.location, issue.message))
