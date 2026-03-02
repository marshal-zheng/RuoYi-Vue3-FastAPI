"""Validate menus.registry.yaml and block legacy menu source regressions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from modules.system.runtime.menu_registry_loader import (
    DEFAULT_MENU_REGISTRY_FILE,
    MenuRegistryLoader,
    ValidationIssue,
)

SEED_DATA_DIR = BACKEND_ROOT / 'scripts' / 'seed_data'
DEFAULT_BASE_MENUS_FILE = SEED_DATA_DIR / 'base' / 'menus.yaml'
DEFAULT_ROLES_FILE = SEED_DATA_DIR / 'base' / 'roles.yaml'
DEFAULT_OVERLAYS_DIR = SEED_DATA_DIR / 'overlays'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check menu registry and legacy-source guardrails')
    parser.add_argument('--strict', action='store_true', help='Enable legacy source regression checks')
    parser.add_argument('--registry', type=Path, default=DEFAULT_MENU_REGISTRY_FILE, help='Menu registry file path')
    parser.add_argument('--roles-file', type=Path, default=DEFAULT_ROLES_FILE, help='Roles seed file path')
    parser.add_argument('--base-menus', type=Path, default=DEFAULT_BASE_MENUS_FILE, help='Legacy base menus file path')
    parser.add_argument(
        '--overlays-dir',
        type=Path,
        default=DEFAULT_OVERLAYS_DIR,
        help='Legacy overlays directory path',
    )
    return parser.parse_args()


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f'YAML payload must be mapping: {path}')
    return payload


def load_role_keys(path: Path) -> set[str]:
    payload = load_yaml_mapping(path)
    role_rows = payload.get('roles', [])
    role_keys: set[str] = set()
    if not isinstance(role_rows, list):
        return role_keys

    for index, role in enumerate(role_rows):
        if not isinstance(role, dict):
            raise ValueError(f'role item must be mapping: {path}#roles[{index}]')
        role_key = role.get('role_key')
        if role_key is None:
            continue
        role_keys.add(str(role_key).strip())
    return {role_key for role_key in role_keys if role_key}


def check_legacy_sources(base_menus: Path, overlays_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    base_payload = load_yaml_mapping(base_menus)
    legacy_menus = base_payload.get('menus', [])
    if isinstance(legacy_menus, list) and legacy_menus:
        issues.append(
            ValidationIssue(
                location=str(base_menus),
                message='legacy menus.yaml still contains menus definitions',
            )
        )

    for overlay_path in sorted(overlays_dir.glob('*.yaml')):
        payload = load_yaml_mapping(overlay_path)

        overlay_menus = payload.get('menus', [])
        if isinstance(overlay_menus, list) and overlay_menus:
            issues.append(
                ValidationIssue(
                    location=str(overlay_path),
                    message='legacy overlay menus definitions are not allowed',
                )
            )

        role_menus = payload.get('role_menus', [])
        if isinstance(role_menus, list) and role_menus:
            issues.append(
                ValidationIssue(
                    location=str(overlay_path),
                    message='legacy overlay role_menus definitions are not allowed',
                )
            )

    return issues


def main() -> int:
    args = parse_args()
    loader = MenuRegistryLoader(args.registry)
    payload = loader.load_registry(args.registry)

    issues = loader.validate_registry(payload)
    role_keys = load_role_keys(args.roles_file)
    issues.extend(loader.validate_role_keys(payload, role_keys))

    if args.strict:
        issues.extend(check_legacy_sources(args.base_menus, args.overlays_dir))

    if issues:
        for issue in issues:
            print(f'[menu-registry-check] {issue.location}: {issue.message}')
        return 1

    print('[menu-registry-check] passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
