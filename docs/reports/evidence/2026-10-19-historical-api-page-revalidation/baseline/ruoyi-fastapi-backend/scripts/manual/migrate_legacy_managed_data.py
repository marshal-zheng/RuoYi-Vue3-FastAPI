"""Export deprecated centralized managed declarations into one module manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.internal.menu_registry import (
        DEFAULT_CAPABILITY_MODULES_DIR,
        DEFAULT_LEGACY_CONFIGS_FILE,
        DEFAULT_LEGACY_DICT_DATA_FILE,
        DEFAULT_LEGACY_DICT_TYPES_FILE,
        DEFAULT_LEGACY_MENU_REGISTRY_FILE,
        DEFAULT_ROLES_FILE,
        migrate_legacy_declarations,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import sys

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from scripts.internal.menu_registry import (
        DEFAULT_CAPABILITY_MODULES_DIR,
        DEFAULT_LEGACY_CONFIGS_FILE,
        DEFAULT_LEGACY_DICT_DATA_FILE,
        DEFAULT_LEGACY_DICT_TYPES_FILE,
        DEFAULT_LEGACY_MENU_REGISTRY_FILE,
        DEFAULT_ROLES_FILE,
        migrate_legacy_declarations,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Export legacy managed declarations into one *.module.yaml file')
    parser.add_argument('--module', required=True, help='Target module_key for the generated manifest')
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
        help='Bootstrap roles seed file used to validate legacy role_grants',
    )
    parser.add_argument(
        '--menu-registry',
        type=Path,
        default=DEFAULT_LEGACY_MENU_REGISTRY_FILE,
        help='Legacy menus.registry.yaml path',
    )
    parser.add_argument(
        '--dict-types',
        type=Path,
        default=DEFAULT_LEGACY_DICT_TYPES_FILE,
        help='Legacy dict_types.yaml path',
    )
    parser.add_argument(
        '--dict-data',
        type=Path,
        default=DEFAULT_LEGACY_DICT_DATA_FILE,
        help='Legacy dict_data.yaml path',
    )
    parser.add_argument(
        '--configs',
        type=Path,
        default=DEFAULT_LEGACY_CONFIGS_FILE,
        help='Legacy configs.yaml path',
    )
    parser.add_argument(
        '--gate-config-key',
        default=None,
        help='Optional runtime gate config_key to wire into runtime_gate',
    )
    parser.add_argument(
        '--gate-default-enabled',
        action='store_true',
        help='When --gate-config-key is set, mark runtime_gate.default_enabled=true',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    summary = migrate_legacy_declarations(
        module_key=args.module,
        modules_root=args.modules_root,
        roles_file=args.roles_file,
        menu_registry=args.menu_registry,
        dict_types=args.dict_types,
        dict_data=args.dict_data,
        configs=args.configs,
        gate_config_key=args.gate_config_key,
        gate_default_enabled=args.gate_default_enabled,
    )

    print(f"module_key={summary['moduleKey']}")
    print(f"manifest={summary['manifest']}")
    print(f"menu_count={summary['menuCount']}")
    print(f"role_grant_count={summary['roleGrantCount']}")
    print(f"dict_type_count={summary['dictTypeCount']}")
    print(f"dict_data_count={summary['dictDataCount']}")
    print(f"config_count={summary['configCount']}")
    if summary['runtimeGate']:
        print(f"runtime_gate={summary['runtimeGate']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
