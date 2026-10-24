# ruff: noqa: E402
"""Module-manifest scaffold helpers and one-time legacy export utilities."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

if TYPE_CHECKING:
    import argparse

from modules.system.runtime.menu_registry_loader import MENU_FIELDS, MenuRegistryLoader, RegistryPayload
from scripts.internal.db_workflow.capability_declaration_compiler import (
    CapabilityDeclarationCompiler,
    format_capability_issues,
)

DEFAULT_CAPABILITY_MODULES_DIR = BACKEND_ROOT / 'capabilities' / 'modules'
SEED_DATA_DIR = BACKEND_ROOT / 'scripts' / 'seed_data'
DEFAULT_ROLES_FILE = SEED_DATA_DIR / 'base' / 'roles.yaml'
DEFAULT_LEGACY_MENU_REGISTRY_FILE = SEED_DATA_DIR / 'menus.registry.yaml'
DEFAULT_LEGACY_DICT_TYPES_FILE = SEED_DATA_DIR / 'base' / 'dict_types.yaml'
DEFAULT_LEGACY_DICT_DATA_FILE = SEED_DATA_DIR / 'base' / 'dict_data.yaml'
DEFAULT_LEGACY_CONFIGS_FILE = SEED_DATA_DIR / 'base' / 'configs.yaml'
MENU_KEY_ALLOWED_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-')


@dataclass
class ModuleManifestRecord:
    """Single module manifest payload loaded from disk."""

    module_key: str
    path: Path
    payload: dict[str, Any]

    @property
    def menus(self) -> list[dict[str, Any]]:
        menus = self.payload.setdefault('menus', [])
        if not isinstance(menus, list):
            raise ValueError(f'{self.path}: menus must be a list')
        return menus

    @property
    def dependencies(self) -> list[str]:
        dependencies = self.payload.setdefault('dependencies', [])
        if not isinstance(dependencies, list):
            raise ValueError(f'{self.path}: dependencies must be a list')
        return dependencies

    @property
    def role_grants(self) -> list[dict[str, Any]]:
        role_grants = self.payload.setdefault('role_grants', [])
        if not isinstance(role_grants, list):
            raise ValueError(f'{self.path}: role_grants must be a list')
        return role_grants


@dataclass(frozen=True)
class MenuOwnership:
    """Resolved ownership for one declared menu."""

    module_key: str
    source_path: Path
    menu_key: str
    menu_id: int
    parent_id: int
    parent_menu_key: str | None
    row_index: int


@dataclass(frozen=True)
class ManifestCatalog:
    """Cross-module menu index used by the scaffold."""

    manifests_by_module: dict[str, ModuleManifestRecord]
    menu_by_key: dict[str, MenuOwnership]
    menu_by_id: dict[int, MenuOwnership]
    children_by_parent_key: dict[str, tuple[str, ...]]


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f'YAML file does not exist: {path}')
    try:
        payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f'invalid YAML in {path}: {exc}') from exc
    if not isinstance(payload, dict):
        raise ValueError(f'YAML payload must be a mapping: {path}')
    return payload


def write_yaml_mapping(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def load_role_keys(path: Path) -> set[str]:
    payload = load_yaml_mapping(path)
    role_rows = payload.get('roles', [])
    if not isinstance(role_rows, list):
        raise ValueError(f'roles must be a list: {path}')

    role_keys: set[str] = set()
    for index, role in enumerate(role_rows):
        if not isinstance(role, dict):
            raise ValueError(f'role item must be a mapping: {path}#roles[{index}]')
        role_key = _normalize_identifier(role.get('role_key'))
        if role_key is None:
            raise ValueError(f'role_key must be a non-empty string: {path}#roles[{index}]')
        if role_key in role_keys:
            raise ValueError(f'duplicate role_key in bootstrap roles: {role_key}')
        role_keys.add(role_key)
    return role_keys


def load_module_manifests(modules_root: Path) -> dict[str, ModuleManifestRecord]:
    manifests: dict[str, ModuleManifestRecord] = {}
    if not modules_root.exists():
        return manifests

    for manifest_path in sorted(modules_root.glob('*.module.yaml')):
        payload = load_yaml_mapping(manifest_path)
        module_key = _normalize_identifier(payload.get('module_key'))
        if module_key is None:
            raise ValueError(f'{manifest_path}: module_key must be a non-empty string')
        if module_key in manifests:
            first_path = manifests[module_key].path
            raise ValueError(f'duplicate module_key across manifests: {module_key} ({first_path}, {manifest_path})')
        manifests[module_key] = ModuleManifestRecord(
            module_key=module_key,
            path=manifest_path,
            payload=_normalize_manifest_payload(payload, module_key=module_key, path=manifest_path),
        )

    return manifests


def run_add_command(
    *,
    modules_root: Path,
    roles_file: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    module_key = _require_identifier(args.module, '--module')
    manifests = load_module_manifests(modules_root)
    role_keys = load_role_keys(roles_file)
    catalog = build_manifest_catalog(manifests)

    target_manifest = manifests.get(module_key)
    if target_manifest is None:
        target_path = modules_root / f'{module_key}.module.yaml'
        if target_path.exists():
            raise ValueError(f'target manifest path already exists: {target_path}')
        target_manifest = ModuleManifestRecord(
            module_key=module_key,
            path=target_path,
            payload=_new_manifest_payload(module_key),
        )
        manifests = {**manifests, module_key: target_manifest}

    parent_menu_key = _normalize_identifier(getattr(args, 'parent_key', None))
    parent_owner = catalog.menu_by_key.get(parent_menu_key) if parent_menu_key else None
    if parent_menu_key and parent_owner is None:
        raise ValueError(f'parent menu_key does not exist: {parent_menu_key}')

    menu_type = str(args.menu_type)
    if menu_type == 'C':
        component = _require_non_empty_string(args.component, '--component')
    else:
        component = _normalize_optional_string(args.component)

    existing_menu_ids = set(catalog.menu_by_id)
    existing_menu_keys = set(catalog.menu_by_key)
    menu_id = next_menu_id(existing_menu_ids)
    generated_menu_key = _suggest_menu_key(
        module_key=module_key,
        parent_menu_key=parent_menu_key,
        path=args.path,
        existing_menu_keys=existing_menu_keys,
    )
    menu_key = _normalize_identifier(getattr(args, 'menu_key', None)) or generated_menu_key
    if menu_key in existing_menu_keys:
        raise ValueError(f'menu_key already exists: {menu_key}')

    parent_id = parent_owner.menu_id if parent_owner is not None else 0
    order_num = args.order_num if args.order_num is not None else next_order_num(manifests.values(), parent_id)
    new_menu = {
        'menu_id': menu_id,
        'menu_key': menu_key,
        'menu_name': args.menu_name,
        'parent_id': parent_id,
        'order_num': order_num,
        'path': args.path,
        'component': component,
        'query': _normalize_nullable_string(args.query),
        'route_name': _normalize_optional_string(args.route_name) or '',
        'is_frame': int(args.is_frame),
        'is_cache': int(args.is_cache),
        'menu_type': menu_type,
        'visible': str(args.visible),
        'status': str(args.status),
        'perms': _normalize_optional_string(args.perms) or '',
        'icon': _normalize_optional_string(args.icon) or '',
        'remark': _normalize_optional_string(args.remark) or '',
    }
    if parent_menu_key is not None:
        new_menu['parent_menu_key'] = parent_menu_key

    target_manifest.menus.append(new_menu)
    target_manifest.menus.sort(key=lambda row: int(row.get('menu_id', 0)))

    if parent_owner is not None and parent_owner.module_key != module_key:
        _append_dependency(target_manifest, parent_owner.module_key)

    granted_roles = tuple(sorted({_require_identifier(role_key, '--grant-role') for role_key in args.grant_role}))
    if granted_roles:
        unknown_roles = sorted(role_key for role_key in granted_roles if role_key not in role_keys)
        if unknown_roles:
            raise ValueError(f'grant roles not found in bootstrap roles: {", ".join(unknown_roles)}')
        _append_role_grants(target_manifest, granted_roles, menu_key)

    _validate_candidate_manifests(manifests, role_keys=role_keys)
    write_yaml_mapping(target_manifest.path, target_manifest.payload)

    return {
        'action': 'add',
        'moduleKey': module_key,
        'manifest': str(target_manifest.path),
        'menuId': menu_id,
        'menuKey': menu_key,
        'parentMenuKey': parent_menu_key,
        'menuName': args.menu_name,
        'grantedRoles': list(granted_roles),
    }


def run_remove_command(
    *,
    modules_root: Path,
    roles_file: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    module_key = _require_identifier(args.module, '--module')
    menu_key = _require_identifier(args.menu_key, '--menu-key')
    manifests = load_module_manifests(modules_root)
    if module_key not in manifests:
        raise ValueError(f'module manifest does not exist: {module_key}')

    role_keys = load_role_keys(roles_file)
    catalog = build_manifest_catalog(manifests)
    target_owner = catalog.menu_by_key.get(menu_key)
    if target_owner is None:
        raise ValueError(f'menu_key does not exist: {menu_key}')
    if target_owner.module_key != module_key:
        raise ValueError(f'menu_key {menu_key} belongs to module {target_owner.module_key}, not {module_key}')

    owned_descendants, foreign_descendants = collect_descendants(
        root_menu_key=menu_key,
        module_key=module_key,
        catalog=catalog,
    )
    if foreign_descendants:
        dependent_links = ', '.join(sorted(foreign_descendants))
        raise ValueError(f'menu_key has cross-module descendants and cannot be removed: {dependent_links}')
    if owned_descendants and not args.cascade:
        raise ValueError(f'menu_key has child menus, use --cascade to remove recursively: {menu_key}')

    remove_keys = {menu_key, *owned_descendants}
    target_manifest = manifests[module_key]
    target_manifest.payload['menus'] = [
        row
        for row in target_manifest.menus
        if _normalize_identifier(row.get('menu_key')) not in remove_keys
    ]
    removed_role_links = _remove_role_grants(target_manifest, remove_keys)

    _validate_candidate_manifests(manifests, role_keys=role_keys)
    write_yaml_mapping(target_manifest.path, target_manifest.payload)

    return {
        'action': 'remove',
        'moduleKey': module_key,
        'manifest': str(target_manifest.path),
        'menuKey': menu_key,
        'cascade': bool(args.cascade),
        'removedMenuCount': len(remove_keys),
        'removedRoleLinks': removed_role_links,
    }


def run_check_command(
    *,
    modules_root: Path = DEFAULT_CAPABILITY_MODULES_DIR,
    roles_file: Path = DEFAULT_ROLES_FILE,
    legacy_menu_registry: Path = DEFAULT_LEGACY_MENU_REGISTRY_FILE,
    legacy_dict_types: Path = DEFAULT_LEGACY_DICT_TYPES_FILE,
    legacy_dict_data: Path = DEFAULT_LEGACY_DICT_DATA_FILE,
    legacy_configs: Path = DEFAULT_LEGACY_CONFIGS_FILE,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    try:
        load_module_manifests(modules_root)
    except (FileNotFoundError, ValueError) as exc:
        issues.append(str(exc))

    try:
        role_keys = load_role_keys(roles_file)
    except (FileNotFoundError, ValueError) as exc:
        issues.append(str(exc))
        role_keys = set()

    compiler_issues = CapabilityDeclarationCompiler(
        modules_root=modules_root,
        known_role_keys=frozenset(role_keys),
    ).validate()
    issues.extend(
        f'[{issue.domain}] {issue.source_path}:{issue.location}: {issue.message}'
        for issue in compiler_issues
    )
    issues.extend(
        check_legacy_sources(
            menu_registry=legacy_menu_registry,
            dict_types=legacy_dict_types,
            dict_data=legacy_dict_data,
            configs=legacy_configs,
        )
    )
    return (not issues), issues


def migrate_legacy_declarations(
    *,
    module_key: str,
    modules_root: Path = DEFAULT_CAPABILITY_MODULES_DIR,
    roles_file: Path = DEFAULT_ROLES_FILE,
    menu_registry: Path = DEFAULT_LEGACY_MENU_REGISTRY_FILE,
    dict_types: Path = DEFAULT_LEGACY_DICT_TYPES_FILE,
    dict_data: Path = DEFAULT_LEGACY_DICT_DATA_FILE,
    configs: Path = DEFAULT_LEGACY_CONFIGS_FILE,
    gate_config_key: str | None = None,
    gate_default_enabled: bool = False,
) -> dict[str, Any]:
    normalized_module_key = _require_identifier(module_key, '--module')
    manifests = load_module_manifests(modules_root)
    if normalized_module_key in manifests:
        raise ValueError(f'module manifest already exists: {normalized_module_key}')

    target_path = modules_root / f'{normalized_module_key}.module.yaml'
    if target_path.exists():
        raise ValueError(f'target manifest path already exists: {target_path}')

    role_keys = load_role_keys(roles_file)
    payload = _build_manifest_from_legacy(
        module_key=normalized_module_key,
        menu_registry=menu_registry,
        dict_types=dict_types,
        dict_data=dict_data,
        configs=configs,
        role_keys=role_keys,
        gate_config_key=gate_config_key,
        gate_default_enabled=gate_default_enabled,
    )
    generated_manifest = ModuleManifestRecord(
        module_key=normalized_module_key,
        path=target_path,
        payload=payload,
    )

    manifests = {**manifests, normalized_module_key: generated_manifest}
    _validate_candidate_manifests(manifests, role_keys=role_keys)
    write_yaml_mapping(target_path, payload)

    return {
        'moduleKey': normalized_module_key,
        'manifest': str(target_path),
        'menuCount': len(payload['menus']),
        'roleGrantCount': len(payload['role_grants']),
        'dictTypeCount': len(payload['dict_types']),
        'dictDataCount': len(payload['dict_data']),
        'configCount': len(payload['configs']),
        'runtimeGate': gate_config_key,
    }


def build_manifest_catalog(manifests: dict[str, ModuleManifestRecord]) -> ManifestCatalog:
    menu_by_key: dict[str, MenuOwnership] = {}
    menu_by_id: dict[int, MenuOwnership] = {}

    for module_key, manifest in sorted(manifests.items()):
        for index, row in enumerate(manifest.menus):
            if not isinstance(row, dict):
                raise ValueError(f'{manifest.path}: menus[{index}] must be a mapping')
            menu_key = _require_identifier(row.get('menu_key'), f'{manifest.path}:menus[{index}].menu_key')
            menu_id = _require_int(row.get('menu_id'), f'{manifest.path}:menus[{index}].menu_id')
            parent_id = _require_int(row.get('parent_id', 0), f'{manifest.path}:menus[{index}].parent_id')
            parent_menu_key = _normalize_identifier(row.get('parent_menu_key'))
            if menu_key in menu_by_key:
                existing = menu_by_key[menu_key]
                raise ValueError(
                    f'duplicate menu_key across manifests: {menu_key} ({existing.source_path}, {manifest.path})'
                )
            if menu_id in menu_by_id:
                existing = menu_by_id[menu_id]
                raise ValueError(
                    f'duplicate menu_id across manifests: {menu_id} ({existing.source_path}, {manifest.path})'
                )
            ownership = MenuOwnership(
                module_key=module_key,
                source_path=manifest.path,
                menu_key=menu_key,
                menu_id=menu_id,
                parent_id=parent_id,
                parent_menu_key=parent_menu_key,
                row_index=index,
            )
            menu_by_key[menu_key] = ownership
            menu_by_id[menu_id] = ownership

    children_by_parent_key: dict[str, list[str]] = {}
    for ownership in menu_by_key.values():
        parent_menu_key = ownership.parent_menu_key
        if parent_menu_key is None and ownership.parent_id != 0:
            parent_owner = menu_by_id.get(ownership.parent_id)
            if parent_owner is not None:
                parent_menu_key = parent_owner.menu_key
        if parent_menu_key is None:
            continue
        children_by_parent_key.setdefault(parent_menu_key, []).append(ownership.menu_key)

    return ManifestCatalog(
        manifests_by_module=manifests,
        menu_by_key=menu_by_key,
        menu_by_id=menu_by_id,
        children_by_parent_key={
            parent_key: tuple(sorted(children))
            for parent_key, children in sorted(children_by_parent_key.items())
        },
    )


def next_menu_id(existing_menu_ids: set[int]) -> int:
    if not existing_menu_ids:
        return 1
    return max(existing_menu_ids) + 1


def next_order_num(manifests: list[ModuleManifestRecord] | tuple[ModuleManifestRecord, ...] | Any, parent_id: int) -> int:
    sibling_orders: list[int] = []
    for manifest in manifests:
        for row in manifest.menus:
            if not isinstance(row, dict):
                continue
            if not MenuRegistryLoader._is_int_like(row.get('parent_id', 0)):
                continue
            if int(row.get('parent_id', 0)) != parent_id:
                continue
            if not MenuRegistryLoader._is_int_like(row.get('order_num', 0)):
                continue
            sibling_orders.append(int(row.get('order_num', 0)))
    if not sibling_orders:
        return 1
    return max(sibling_orders) + 1


def collect_descendants(
    *,
    root_menu_key: str,
    module_key: str,
    catalog: ManifestCatalog,
) -> tuple[set[str], set[str]]:
    stack = list(catalog.children_by_parent_key.get(root_menu_key, ()))
    owned_descendants: set[str] = set()
    foreign_descendants: set[str] = set()
    seen: set[str] = set()

    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        ownership = catalog.menu_by_key[current]
        if ownership.module_key == module_key:
            owned_descendants.add(current)
        else:
            foreign_descendants.add(f'{current}@{ownership.module_key}')
        stack.extend(catalog.children_by_parent_key.get(current, ()))

    return owned_descendants, foreign_descendants


def check_legacy_sources(
    *,
    menu_registry: Path,
    dict_types: Path,
    dict_data: Path,
    configs: Path,
) -> list[str]:
    issues: list[str] = []
    legacy_paths = (
        (menu_registry, ('menus', 'role_grants')),
        (dict_types, ('dict_types',)),
        (dict_data, ('dict_data',)),
        (configs, ('configs',)),
    )
    for path, keys in legacy_paths:
        if not path.exists():
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding='utf-8'))
        except yaml.YAMLError as exc:
            issues.append(f'{path}: invalid YAML: {exc}')
            continue
        if _legacy_payload_is_empty(payload, keys):
            continue
        issues.append(f'{path}: legacy declaration file is no longer supported; migrate content into capabilities/modules/*.module.yaml')
    return issues


def _build_manifest_from_legacy(
    *,
    module_key: str,
    menu_registry: Path,
    dict_types: Path,
    dict_data: Path,
    configs: Path,
    role_keys: set[str],
    gate_config_key: str | None,
    gate_default_enabled: bool,
) -> dict[str, Any]:
    registry_loader = MenuRegistryLoader(menu_registry)
    registry_payload = (
        registry_loader.load_registry(menu_registry)
        if menu_registry.exists()
        else RegistryPayload(version='1', menus=[], role_grants=[])
    )
    registry_issues = registry_loader.validate_registry(registry_payload)
    registry_issues.extend(registry_loader.validate_role_keys(registry_payload, role_keys))
    if registry_issues:
        issues_text = '; '.join(f'{issue.location}: {issue.message}' for issue in registry_issues)
        raise ValueError(f'legacy menu registry validation failed: {issues_text}')

    dict_types_payload = _load_legacy_collection(dict_types, root_key='dict_types')
    dict_data_payload = _load_legacy_collection(dict_data, root_key='dict_data')
    configs_payload = _load_legacy_collection(configs, root_key='configs')
    if not any((registry_payload.menus, registry_payload.role_grants, dict_types_payload, dict_data_payload, configs_payload)):
        raise ValueError('no legacy managed declarations found to migrate')

    id_to_key = {int(menu['menu_id']): f'{module_key}.menu.{int(menu["menu_id"])}' for menu in registry_payload.menus}
    menus: list[dict[str, Any]] = []
    for raw_menu in sorted(registry_payload.menus, key=lambda row: int(row['menu_id'])):
        normalized_menu = MenuRegistryLoader._normalize_menu(raw_menu)
        menu_id = int(normalized_menu['menu_id'])
        menu_row = {field_name: normalized_menu[field_name] for field_name in MENU_FIELDS}
        menu_row['menu_key'] = id_to_key[menu_id]
        if int(menu_row['parent_id']) != 0:
            parent_key = id_to_key.get(int(menu_row['parent_id']))
            if parent_key is None:
                raise ValueError(f'legacy menu parent is missing from registry: menu_id={menu_id}')
            menu_row['parent_menu_key'] = parent_key
        menus.append(menu_row)

    role_grants: list[dict[str, Any]] = []
    for grant in sorted(registry_payload.role_grants, key=lambda row: str(row['role_key'])):
        menu_keys = [id_to_key[int(menu_id)] for menu_id in grant.get('menu_ids', [])]
        role_grants.append({'role_key': str(grant['role_key']).strip(), 'menu_keys': menu_keys})

    payload: dict[str, Any] = {
        'version': '1',
        'module_key': module_key,
        'menus': menus,
        'role_grants': role_grants,
        'dict_types': dict_types_payload,
        'dict_data': dict_data_payload,
        'configs': configs_payload,
    }

    normalized_gate_key = _normalize_identifier(gate_config_key)
    if normalized_gate_key is not None:
        if normalized_gate_key not in {str(row.get('config_key') or '').strip() for row in configs_payload if isinstance(row, dict)}:
            raise ValueError(f'gate config_key is not declared in migrated configs: {normalized_gate_key}')
        payload['runtime_gate'] = {
            'config_key': normalized_gate_key,
            'default_enabled': bool(gate_default_enabled),
        }

    return payload


def _load_legacy_collection(path: Path, *, root_key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = load_yaml_mapping(path)
    rows = payload.get(root_key, [])
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError(f'{path}: {root_key} must be a list')
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f'{path}: {root_key}[{index}] must be a mapping')
    return [dict(row) for row in rows]


def _new_manifest_payload(module_key: str) -> dict[str, Any]:
    return {
        'version': '1',
        'module_key': module_key,
        'menus': [],
        'role_grants': [],
        'dict_types': [],
        'dict_data': [],
        'configs': [],
    }


def _normalize_manifest_payload(payload: dict[str, Any], *, module_key: str, path: Path) -> dict[str, Any]:
    normalized = dict(payload)
    normalized['version'] = str(normalized.get('version') or '1')
    normalized['module_key'] = module_key

    for field_name in ('menus', 'role_grants', 'dict_types', 'dict_data', 'configs'):
        value = normalized.get(field_name, [])
        if value is None:
            value = []
        if not isinstance(value, list):
            raise ValueError(f'{path}: {field_name} must be a list')
        normalized[field_name] = value

    dependencies = normalized.get('dependencies', [])
    if dependencies is None:
        dependencies = []
    if not isinstance(dependencies, list):
        raise ValueError(f'{path}: dependencies must be a list')
    normalized['dependencies'] = dependencies
    return normalized


def _append_dependency(manifest: ModuleManifestRecord, dependency_module_key: str) -> None:
    dependencies = [_require_identifier(value, f'{manifest.path}:dependencies') for value in manifest.dependencies]
    if dependency_module_key not in dependencies:
        dependencies.append(dependency_module_key)
    manifest.payload['dependencies'] = sorted(set(dependencies))


def _append_role_grants(manifest: ModuleManifestRecord, role_keys: tuple[str, ...], menu_key: str) -> None:
    grants_by_role: dict[str, list[str]] = {}
    for index, row in enumerate(manifest.role_grants):
        if not isinstance(row, dict):
            raise ValueError(f'{manifest.path}: role_grants[{index}] must be a mapping')
        role_key = _require_identifier(row.get('role_key'), f'{manifest.path}:role_grants[{index}].role_key')
        menu_keys = row.get('menu_keys', [])
        if not isinstance(menu_keys, list):
            raise ValueError(f'{manifest.path}: role_grants[{index}].menu_keys must be a list')
        grants_by_role[role_key] = sorted({_require_identifier(value, f'{manifest.path}:role_grants[{index}].menu_keys') for value in menu_keys})

    for role_key in role_keys:
        current_keys = set(grants_by_role.get(role_key, []))
        current_keys.add(menu_key)
        grants_by_role[role_key] = sorted(current_keys)

    manifest.payload['role_grants'] = [
        {'role_key': role_key, 'menu_keys': menu_keys}
        for role_key, menu_keys in sorted(grants_by_role.items())
        if menu_keys
    ]


def _remove_role_grants(manifest: ModuleManifestRecord, remove_keys: set[str]) -> int:
    updated_grants: list[dict[str, Any]] = []
    removed_links = 0

    for index, row in enumerate(manifest.role_grants):
        if not isinstance(row, dict):
            raise ValueError(f'{manifest.path}: role_grants[{index}] must be a mapping')
        role_key = _require_identifier(row.get('role_key'), f'{manifest.path}:role_grants[{index}].role_key')
        menu_keys = row.get('menu_keys', [])
        if not isinstance(menu_keys, list):
            raise ValueError(f'{manifest.path}: role_grants[{index}].menu_keys must be a list')
        normalized_keys = [
            _require_identifier(menu_key, f'{manifest.path}:role_grants[{index}].menu_keys')
            for menu_key in menu_keys
        ]
        filtered_keys = [menu_key for menu_key in normalized_keys if menu_key not in remove_keys]
        removed_links += len(normalized_keys) - len(filtered_keys)
        if filtered_keys:
            updated_grants.append({'role_key': role_key, 'menu_keys': sorted(set(filtered_keys))})

    manifest.payload['role_grants'] = updated_grants
    return removed_links


def _validate_candidate_manifests(
    manifests: dict[str, ModuleManifestRecord],
    *,
    role_keys: set[str],
) -> None:
    with tempfile.TemporaryDirectory(prefix='module-manifest-validate-') as temp_dir:
        temp_root = Path(temp_dir)
        for manifest in sorted(manifests.values(), key=lambda item: item.path.name):
            temp_path = temp_root / manifest.path.name
            write_yaml_mapping(temp_path, manifest.payload)
        issues = CapabilityDeclarationCompiler(
            modules_root=temp_root,
            known_role_keys=frozenset(role_keys),
        ).validate()
    if issues:
        raise ValueError(format_capability_issues(issues))


def _legacy_payload_is_empty(payload: Any, keys: tuple[str, ...]) -> bool:
    if payload in (None, {}):
        return True
    if not isinstance(payload, dict):
        return False
    return all(not payload.get(key) for key in keys)


def _suggest_menu_key(
    *,
    module_key: str,
    parent_menu_key: str | None,
    path: str,
    existing_menu_keys: set[str],
) -> str:
    fragment = _slug_menu_key_fragment(path) or 'menu'
    if parent_menu_key and parent_menu_key.startswith(f'{module_key}.'):
        base_key = f'{parent_menu_key}.{fragment}'
    else:
        base_key = f'{module_key}.{fragment}'
    candidate = base_key
    index = 2
    while candidate in existing_menu_keys:
        candidate = f'{base_key}.{index}'
        index += 1
    return candidate


def _slug_menu_key_fragment(value: str | None) -> str:
    raw = str(value or '').strip().replace('/', '.')
    if not raw:
        return ''
    pieces: list[str] = []
    for char in raw:
        if char.isalnum() or char in {'_', '-', '.', ':'}:
            pieces.append(char.lower())
        else:
            pieces.append('-')
    collapsed = ''.join(pieces).strip('.-_:')
    while '..' in collapsed:
        collapsed = collapsed.replace('..', '.')
    while '--' in collapsed:
        collapsed = collapsed.replace('--', '-')
    return collapsed


def _normalize_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if any(char not in MENU_KEY_ALLOWED_CHARS for char in normalized):
        return None
    return normalized


def _require_identifier(value: Any, location: str) -> str:
    normalized = _normalize_identifier(value)
    if normalized is None:
        raise ValueError(f'{location} must be a non-empty identifier')
    return normalized


def _require_non_empty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{location} must be a non-empty string')
    return value.strip()


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value)
    normalized = value.strip()
    return normalized or None


def _normalize_nullable_string(value: Any) -> str | None:
    normalized = _normalize_optional_string(value)
    return normalized if normalized is not None else None


def _require_int(value: Any, location: str) -> int:
    if not MenuRegistryLoader._is_int_like(value):
        raise ValueError(f'{location} must be an integer')
    return int(value)
