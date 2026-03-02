"""Menu registry loader and validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MENU_REGISTRY_FILE = BACKEND_ROOT / 'scripts' / 'seed_data' / 'menus.registry.yaml'

MENU_FIELDS = (
    'menu_id',
    'menu_name',
    'parent_id',
    'order_num',
    'path',
    'component',
    'query',
    'route_name',
    'is_frame',
    'is_cache',
    'menu_type',
    'visible',
    'status',
    'perms',
    'icon',
    'remark',
)

REQUIRED_MENU_FIELDS = (
    'menu_id',
    'menu_name',
    'parent_id',
    'order_num',
    'path',
    'is_frame',
    'is_cache',
    'menu_type',
    'visible',
    'status',
)

INTEGER_MENU_FIELDS = {'menu_id', 'parent_id', 'order_num', 'is_frame', 'is_cache'}
MENU_TYPE_SET = {'M', 'C', 'F'}
FLAG_SET = {'0', '1'}
COMPONENT_PATH_PATTERN = re.compile(r'^[A-Za-z0-9_/-]+$')


@dataclass(frozen=True)
class ValidationIssue:
    """Validation issue with precise location for developer feedback."""

    location: str
    message: str


@dataclass(frozen=True)
class RegistryPayload:
    """Raw menu registry payload."""

    version: str
    menus: list[dict[str, Any]]
    role_grants: list[dict[str, Any]]


@dataclass(frozen=True)
class TargetState:
    """Normalized target state for sys_menu/sys_role_menu reconciliation."""

    target_menus: dict[int, dict[str, Any]]
    target_role_menu_pairs: set[tuple[int, int]]


class MenuRegistryLoader:
    """Load and validate menus.registry.yaml payload."""

    def __init__(self, registry_path: str | Path | None = None) -> None:
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_MENU_REGISTRY_FILE

    def load_registry(self, path: str | Path | None = None) -> RegistryPayload:
        registry_path = Path(path) if path else self.registry_path
        if not registry_path.exists():
            raise FileNotFoundError(f'menu registry not found: {registry_path}')

        with registry_path.open('r', encoding='utf-8') as handle:
            payload = yaml.safe_load(handle) or {}

        if not isinstance(payload, dict):
            raise ValueError(f'menu registry payload must be a mapping: {registry_path}')

        version = payload.get('version', '')
        menus = payload.get('menus', [])
        role_grants = payload.get('role_grants', [])
        return RegistryPayload(
            version=str(version) if version is not None else '',
            menus=menus if isinstance(menus, list) else [],
            role_grants=role_grants if isinstance(role_grants, list) else [],
        )

    def validate_registry(self, payload: RegistryPayload) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not payload.version.strip():
            issues.append(ValidationIssue(location='version', message='version is required and must be non-empty'))

        menu_ids: list[int] = []
        menu_map: dict[int, dict[str, Any]] = {}

        for index, menu in enumerate(payload.menus):
            prefix = f'menus[{index}]'
            if not isinstance(menu, dict):
                issues.append(ValidationIssue(location=prefix, message='menu item must be a mapping'))
                continue

            missing_fields = [field for field in REQUIRED_MENU_FIELDS if field not in menu]
            if missing_fields:
                issues.append(
                    ValidationIssue(
                        location=prefix,
                        message=f'missing required fields: {", ".join(missing_fields)}',
                    )
                )
                continue

            menu_id_value = menu.get('menu_id')
            if not self._is_int_like(menu_id_value):
                issues.append(ValidationIssue(location=f'{prefix}.menu_id', message='menu_id must be an integer'))
                continue
            menu_id = int(menu_id_value)
            if menu_id in menu_ids:
                issues.append(ValidationIssue(location=f'{prefix}.menu_id', message=f'duplicate menu_id: {menu_id}'))
                continue
            menu_ids.append(menu_id)
            menu_map[menu_id] = menu

            for field in INTEGER_MENU_FIELDS:
                if field in menu and not self._is_int_like(menu[field]):
                    issues.append(ValidationIssue(location=f'{prefix}.{field}', message=f'{field} must be an integer'))

            menu_type = str(menu.get('menu_type'))
            if menu_type not in MENU_TYPE_SET:
                issues.append(
                    ValidationIssue(
                        location=f'{prefix}.menu_type',
                        message=f'menu_type must be one of {sorted(MENU_TYPE_SET)}',
                    )
                )

            visible = str(menu.get('visible'))
            if visible not in FLAG_SET:
                issues.append(ValidationIssue(location=f'{prefix}.visible', message='visible must be "0" or "1"'))

            status = str(menu.get('status'))
            if status not in FLAG_SET:
                issues.append(ValidationIssue(location=f'{prefix}.status', message='status must be "0" or "1"'))

            menu_name = menu.get('menu_name')
            if not isinstance(menu_name, str) or not menu_name.strip():
                issues.append(
                    ValidationIssue(
                        location=f'{prefix}.menu_name',
                        message='menu_name must be a non-empty string',
                    )
                )

            path = menu.get('path')
            if not isinstance(path, str):
                issues.append(ValidationIssue(location=f'{prefix}.path', message='path must be a string'))

            component = menu.get('component')
            if menu_type == 'C':
                if not isinstance(component, str) or not component.strip():
                    issues.append(
                        ValidationIssue(location=f'{prefix}.component', message='component is required for menu_type=C')
                    )
                elif not COMPONENT_PATH_PATTERN.match(component.strip()):
                    issues.append(
                        ValidationIssue(
                            location=f'{prefix}.component',
                            message='component contains invalid characters (allowed: letters, digits, _, /, -)',
                        )
                    )
            elif component is not None and not isinstance(component, str):
                issues.append(
                    ValidationIssue(
                        location=f'{prefix}.component',
                        message='component must be null or string for non-C menus',
                    )
                )

            managed_by_seed = menu.get('managed_by_seed', True)
            if not self._is_truthy_flag(managed_by_seed):
                issues.append(
                    ValidationIssue(
                        location=f'{prefix}.managed_by_seed',
                        message='managed_by_seed must be true/1 (registry only manages seeded menus)',
                    )
                )

        menu_id_set = set(menu_ids)
        for menu_id, menu in menu_map.items():
            parent_id_raw = menu.get('parent_id')
            if not self._is_int_like(parent_id_raw):
                continue
            parent_id = int(parent_id_raw)
            if parent_id != 0 and parent_id not in menu_id_set:
                issues.append(
                    ValidationIssue(
                        location=f'menu_id={menu_id}.parent_id',
                        message=f'parent menu {parent_id} does not exist',
                    )
                )

        issues.extend(self._detect_parent_cycles(menu_map))

        seen_role_keys: set[str] = set()
        for index, grant in enumerate(payload.role_grants):
            prefix = f'role_grants[{index}]'
            if not isinstance(grant, dict):
                issues.append(ValidationIssue(location=prefix, message='role grant must be a mapping'))
                continue

            role_key = grant.get('role_key')
            if not isinstance(role_key, str) or not role_key.strip():
                issues.append(
                    ValidationIssue(
                        location=f'{prefix}.role_key',
                        message='role_key must be a non-empty string',
                    )
                )
                continue
            role_key = role_key.strip()

            if role_key in seen_role_keys:
                issues.append(ValidationIssue(location=f'{prefix}.role_key', message=f'duplicate role_key: {role_key}'))
            seen_role_keys.add(role_key)

            menu_ids_value = grant.get('menu_ids')
            if not isinstance(menu_ids_value, list):
                issues.append(ValidationIssue(location=f'{prefix}.menu_ids', message='menu_ids must be a list'))
                continue

            role_menu_ids: set[int] = set()
            for menu_index, menu_id_value in enumerate(menu_ids_value):
                location = f'{prefix}.menu_ids[{menu_index}]'
                if not self._is_int_like(menu_id_value):
                    issues.append(ValidationIssue(location=location, message='menu_id must be an integer'))
                    continue
                menu_id = int(menu_id_value)
                if menu_id in role_menu_ids:
                    issues.append(ValidationIssue(location=location, message=f'duplicate menu_id in grant: {menu_id}'))
                    continue
                role_menu_ids.add(menu_id)
                if menu_id not in menu_id_set:
                    issues.append(
                        ValidationIssue(location=location, message=f'menu_id={menu_id} is not declared in menus list')
                    )

        return issues

    def validate_role_keys(self, payload: RegistryPayload, existing_role_keys: set[str]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for index, grant in enumerate(payload.role_grants):
            if not isinstance(grant, dict):
                continue
            role_key = str(grant.get('role_key') or '').strip()
            if not role_key:
                continue
            if role_key not in existing_role_keys:
                issues.append(
                    ValidationIssue(
                        location=f'role_grants[{index}].role_key',
                        message=f'role_key not found in system roles: {role_key}',
                    )
                )
        return issues

    def build_menu_target_map(self, payload: RegistryPayload) -> dict[int, dict[str, Any]]:
        registry_issues = self.validate_registry(payload)
        if registry_issues:
            raise ValueError(format_validation_issues(registry_issues))

        target_menus: dict[int, dict[str, Any]] = {}
        for raw_menu in payload.menus:
            normalized = self._normalize_menu(raw_menu)
            target_menus[normalized['menu_id']] = normalized
        return target_menus

    def build_target_state(self, payload: RegistryPayload, role_key_to_id: dict[str, int]) -> TargetState:
        target_menus = self.build_menu_target_map(payload)
        role_issues = self.validate_role_keys(payload, set(role_key_to_id.keys()))
        if role_issues:
            raise ValueError(format_validation_issues(role_issues))

        role_menu_pairs: set[tuple[int, int]] = set()
        for grant in payload.role_grants:
            role_key = str(grant['role_key']).strip()
            role_id = int(role_key_to_id[role_key])
            for menu_id_value in grant.get('menu_ids', []):
                menu_id = int(menu_id_value)
                if menu_id not in target_menus:
                    continue
                if target_menus[menu_id].get('managed_by_seed') != 1:
                    continue
                role_menu_pairs.add((role_id, menu_id))

        return TargetState(target_menus=target_menus, target_role_menu_pairs=role_menu_pairs)

    @staticmethod
    def _normalize_menu(raw_menu: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            'query': None,
            'route_name': '',
            'component': None,
            'perms': '',
            'icon': '',
            'remark': '',
            'managed_by_seed': True,
        }
        normalized: dict[str, Any] = {}

        for field in MENU_FIELDS:
            value = raw_menu.get(field, defaults.get(field))
            if field in INTEGER_MENU_FIELDS:
                value = int(value)
            elif field in {'visible', 'status', 'menu_type'}:
                value = str(value)
            elif field in {'menu_name', 'path', 'route_name', 'perms', 'icon', 'remark'} and value is None:
                value = ''
            normalized[field] = value

        managed_by_seed = MenuRegistryLoader._is_truthy_flag(raw_menu.get('managed_by_seed', True))
        normalized['managed_by_seed'] = 1 if managed_by_seed else 0
        return normalized

    @staticmethod
    def _is_int_like(value: Any) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            return bool(re.fullmatch(r'[+-]?\d+', value.strip()))
        return False

    @staticmethod
    def _is_truthy_flag(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return False

    @staticmethod
    def _detect_parent_cycles(menu_map: dict[int, dict[str, Any]]) -> list[ValidationIssue]:
        graph: dict[int, int] = {}
        for menu_id, menu in menu_map.items():
            parent_id = menu.get('parent_id')
            if MenuRegistryLoader._is_int_like(parent_id):
                graph[menu_id] = int(parent_id)

        issues: list[ValidationIssue] = []
        visiting: set[int] = set()
        visited: set[int] = set()

        def dfs(node: int, trail: list[int]) -> None:
            if node in visited:
                return
            if node in visiting:
                cycle = trail[trail.index(node):] + [node]
                issues.append(
                    ValidationIssue(
                        location=f'menu_id={node}.parent_id',
                        message=f'parent cycle detected: {" -> ".join(str(item) for item in cycle)}',
                    )
                )
                return

            visiting.add(node)
            parent = graph.get(node, 0)
            if parent in graph and parent != 0:
                dfs(parent, trail + [parent])
            visiting.remove(node)
            visited.add(node)

        for menu_id in graph:
            dfs(menu_id, [menu_id])

        return issues


def format_validation_issues(issues: list[ValidationIssue]) -> str:
    """Format validation issues to one readable error string."""

    return '; '.join(f'{issue.location}: {issue.message}' for issue in issues)
