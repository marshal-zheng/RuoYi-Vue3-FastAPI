#!/usr/bin/env python3
# ruff: noqa: E402
"""Module-manifest menu scaffold entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.internal.menu_registry import (
    DEFAULT_CAPABILITY_MODULES_DIR,
    DEFAULT_LEGACY_CONFIGS_FILE,
    DEFAULT_LEGACY_DICT_DATA_FILE,
    DEFAULT_LEGACY_DICT_TYPES_FILE,
    DEFAULT_LEGACY_MENU_REGISTRY_FILE,
    DEFAULT_ROLES_FILE,
    run_add_command,
    run_check_command,
    run_remove_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage capability module manifests')
    parser.add_argument(
        '--modules-root',
        type=Path,
        default=DEFAULT_CAPABILITY_MODULES_DIR,
        help='Directory containing capabilities/modules/*.module.yaml',
    )
    parser.add_argument(
        '--roles-file',
        type=Path,
        default=DEFAULT_ROLES_FILE,
        help='Bootstrap roles seed file used to validate role_grants',
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    add_parser = subparsers.add_parser('add', help='Add one menu entry into a module manifest')
    add_parser.add_argument('--module', type=str, required=True, help='Owning module_key')
    add_parser.add_argument('--parent-key', type=str, required=False, help='Parent menu_key; omit for a top-level menu')
    add_parser.add_argument('--menu-key', type=str, required=False, help='Optional explicit menu_key override')
    add_parser.add_argument('--menu-name', type=str, required=True)
    add_parser.add_argument('--path', type=str, required=True)
    add_parser.add_argument('--component', type=str, required=False)
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
    add_parser.add_argument(
        '--grant-role',
        action='append',
        default=[],
        help='Optional role_key to receive this menu; can be repeated',
    )

    remove_parser = subparsers.add_parser('remove', help='Remove menu entry from a module manifest')
    remove_parser.add_argument('--module', type=str, required=True, help='Owning module_key')
    remove_parser.add_argument('--menu-key', type=str, required=True, help='menu_key to remove')
    remove_parser.add_argument('--cascade', action='store_true', help='Also remove same-module descendants')

    check_parser = subparsers.add_parser('check', help='Validate module manifests and block legacy declarations')
    check_parser.add_argument(
        '--legacy-menu-registry',
        type=Path,
        default=DEFAULT_LEGACY_MENU_REGISTRY_FILE,
        help='Legacy menus.registry.yaml path to verify as empty',
    )
    check_parser.add_argument(
        '--legacy-dict-types',
        type=Path,
        default=DEFAULT_LEGACY_DICT_TYPES_FILE,
        help='Legacy dict_types.yaml path to verify as empty',
    )
    check_parser.add_argument(
        '--legacy-dict-data',
        type=Path,
        default=DEFAULT_LEGACY_DICT_DATA_FILE,
        help='Legacy dict_data.yaml path to verify as empty',
    )
    check_parser.add_argument(
        '--legacy-configs',
        type=Path,
        default=DEFAULT_LEGACY_CONFIGS_FILE,
        help='Legacy configs.yaml path to verify as empty',
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == 'check':
        passed, issues = run_check_command(
            modules_root=args.modules_root,
            roles_file=args.roles_file,
            legacy_menu_registry=args.legacy_menu_registry,
            legacy_dict_types=args.legacy_dict_types,
            legacy_dict_data=args.legacy_dict_data,
            legacy_configs=args.legacy_configs,
        )
        if not passed:
            for issue in issues:
                print(f'[menu-check] {issue}')
            return 1
        print('[menu-check] passed')
        return 0

    if args.command == 'add':
        summary = run_add_command(
            modules_root=args.modules_root,
            roles_file=args.roles_file,
            args=args,
        )
    elif args.command == 'remove':
        summary = run_remove_command(
            modules_root=args.modules_root,
            roles_file=args.roles_file,
            args=args,
        )
    else:  # pragma: no cover
        raise ValueError(f'unsupported command: {args.command}')

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
