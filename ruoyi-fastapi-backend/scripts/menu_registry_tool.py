"""Menu registry scaffolding tool for add/remove operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from modules.system.runtime.menu_registry_loader import (
    DEFAULT_MENU_REGISTRY_FILE,
    MenuRegistryLoader,
    RegistryPayload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Scaffold menu registry entries')
    parser.add_argument('--registry', type=Path, default=DEFAULT_MENU_REGISTRY_FILE, help='Menu registry file path')

    subparsers = parser.add_subparsers(dest='command', required=True)

    add_parser = subparsers.add_parser('add', help='Add one menu entry')
    add_parser.add_argument('--parent-id', type=int, required=True)
    add_parser.add_argument('--menu-name', type=str, required=True)
    add_parser.add_argument('--path', type=str, required=True)
    add_parser.add_argument('--component', type=str, required=True)
    add_parser.add_argument('--menu-id', type=int, required=False)
    add_parser.add_argument('--menu-type', type=str, choices=['M', 'C', 'F'], default='C')
    add_parser.add_argument('--order-num', type=int, required=False)
    add_parser.add_argument('--query', type=str, required=False)
    add_parser.add_argument('--route-name', type=str, default='')
    add_parser.add_argument('--is-frame', type=int, choices=[0, 1], default=1)
    add_parser.add_argument('--is-cache', type=int, choices=[0, 1], default=0)
    add_parser.add_argument('--visible', type=str, choices=['0', '1'], default='0')
    add_parser.add_argument('--status', type=str, choices=['0', '1'], default='0')
    add_parser.add_argument('--perms', type=str, default='')
    add_parser.add_argument('--icon', type=str, default='menu')
    add_parser.add_argument('--remark', type=str, default='')

    remove_parser = subparsers.add_parser('remove', help='Remove menu entry from registry')
    remove_parser.add_argument('--menu-id', type=int, required=True)
    remove_parser.add_argument('--cascade', action='store_true')

    return parser.parse_args()


def load_registry_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f'menu registry not found: {path}')
    with path.open('r', encoding='utf-8') as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f'registry payload must be mapping: {path}')
    payload.setdefault('version', '1')
    payload.setdefault('menus', [])
    payload.setdefault('role_grants', [])
    return payload


def write_registry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def next_menu_id(existing_menu_ids: set[int]) -> int:
    if not existing_menu_ids:
        return 1
    return max(existing_menu_ids) + 1


def next_order_num(menus: list[dict[str, Any]], parent_id: int) -> int:
    sibling_orders = [int(menu.get('order_num', 0)) for menu in menus if int(menu.get('parent_id', 0)) == parent_id]
    if not sibling_orders:
        return 1
    return max(sibling_orders) + 1


def collect_descendants(parent_id: int, children_by_parent: dict[int, list[int]]) -> set[int]:
    stack = [parent_id]
    descendants: set[int] = set()
    while stack:
        current = stack.pop()
        if current in descendants:
            continue
        descendants.add(current)
        stack.extend(children_by_parent.get(current, []))
    return descendants


def run_add_command(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    menus = payload.get('menus', [])
    if not isinstance(menus, list):
        raise ValueError('menus must be a list')

    existing_menu_ids = {
        int(menu.get('menu_id'))
        for menu in menus
        if isinstance(menu, dict) and menu.get('menu_id') is not None
    }
    if args.parent_id != 0 and args.parent_id not in existing_menu_ids:
        raise ValueError(f'parent_id does not exist: {args.parent_id}')

    menu_id = args.menu_id if args.menu_id is not None else next_menu_id(existing_menu_ids)
    if menu_id in existing_menu_ids:
        raise ValueError(f'menu_id already exists: {menu_id}')

    order_num = args.order_num if args.order_num is not None else next_order_num(menus, args.parent_id)
    new_menu = {
        'menu_id': menu_id,
        'menu_name': args.menu_name,
        'parent_id': args.parent_id,
        'order_num': order_num,
        'path': args.path,
        'component': args.component,
        'query': args.query,
        'route_name': args.route_name,
        'is_frame': args.is_frame,
        'is_cache': args.is_cache,
        'menu_type': args.menu_type,
        'visible': args.visible,
        'status': args.status,
        'perms': args.perms,
        'icon': args.icon,
        'remark': args.remark,
        'managed_by_seed': True,
    }
    menus.append(new_menu)
    menus.sort(key=lambda item: int(item.get('menu_id', 0)))

    return {
        'action': 'add',
        'menuId': menu_id,
        'parentId': args.parent_id,
        'menuName': args.menu_name,
    }


def run_remove_command(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    menus = payload.get('menus', [])
    role_grants = payload.get('role_grants', [])
    if not isinstance(menus, list):
        raise ValueError('menus must be a list')
    if not isinstance(role_grants, list):
        raise ValueError('role_grants must be a list')

    menu_id_to_row = {
        int(menu.get('menu_id')): menu
        for menu in menus
        if isinstance(menu, dict) and menu.get('menu_id') is not None
    }
    if args.menu_id not in menu_id_to_row:
        raise ValueError(f'menu_id does not exist: {args.menu_id}')

    children_by_parent: dict[int, list[int]] = {}
    for menu in menus:
        if not isinstance(menu, dict):
            continue
        child_id = int(menu.get('menu_id', 0))
        parent_id = int(menu.get('parent_id', 0))
        children_by_parent.setdefault(parent_id, []).append(child_id)

    direct_children = children_by_parent.get(args.menu_id, [])
    if direct_children and not args.cascade:
        raise ValueError(f'menu_id has children, use --cascade to remove recursively: {args.menu_id}')

    remove_ids = collect_descendants(args.menu_id, children_by_parent) if args.cascade else {args.menu_id}
    payload['menus'] = [
        menu
        for menu in menus
        if not isinstance(menu, dict) or int(menu.get('menu_id', -1)) not in remove_ids
    ]

    updated_grants: list[dict[str, Any]] = []
    removed_role_links = 0
    for grant in role_grants:
        if not isinstance(grant, dict):
            continue
        role_key = grant.get('role_key')
        menu_ids = grant.get('menu_ids', [])
        if not isinstance(menu_ids, list):
            continue

        filtered_ids = [int(menu_id) for menu_id in menu_ids if int(menu_id) not in remove_ids]
        removed_role_links += len(menu_ids) - len(filtered_ids)
        if filtered_ids:
            updated_grants.append({'role_key': role_key, 'menu_ids': filtered_ids})

    payload['role_grants'] = updated_grants

    return {
        'action': 'remove',
        'menuId': args.menu_id,
        'cascade': bool(args.cascade),
        'removedMenuCount': len(remove_ids),
        'removedRoleLinks': removed_role_links,
    }


def validate_registry(path: Path, payload: dict[str, Any]) -> None:
    loader = MenuRegistryLoader(path)
    registry_payload = RegistryPayload(
        version=str(payload.get('version', '')),
        menus=payload.get('menus', []) if isinstance(payload.get('menus', []), list) else [],
        role_grants=payload.get('role_grants', []) if isinstance(payload.get('role_grants', []), list) else [],
    )
    issues = loader.validate_registry(registry_payload)
    if issues:
        issue_text = '; '.join(f'{issue.location}: {issue.message}' for issue in issues)
        raise ValueError(f'menu registry validation failed: {issue_text}')


def main() -> int:
    args = parse_args()
    payload = load_registry_mapping(args.registry)

    if args.command == 'add':
        summary = run_add_command(payload, args)
    elif args.command == 'remove':
        summary = run_remove_command(payload, args)
    else:
        raise ValueError(f'unsupported command: {args.command}')

    validate_registry(args.registry, payload)
    write_registry(args.registry, payload)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
