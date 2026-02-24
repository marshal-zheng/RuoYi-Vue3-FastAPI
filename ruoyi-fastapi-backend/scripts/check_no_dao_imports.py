#!/usr/bin/env python3
"""Block runtime imports from module_admin.dao.

Repository is the only approved data access layer for runtime code.
Tests and legacy DAO implementation files are excluded from this check.
"""

from __future__ import annotations

import ast
from pathlib import Path


RUNTIME_DIRS = (
    'module_admin',
    'module_generator',
    'module_task',
    'config',
    'middlewares',
    'exceptions',
    'utils',
)
RUNTIME_FILES = ('server.py', 'app.py')
LEGACY_DAO_PATHS = (
    'module_admin/dao',
    'module_generator/dao',
    'tests/unit/dao',
    'module_generator/templates/python/dao.py.jinja2',
)


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if 'tests' in parts or 'alembic' in parts or 'docs' in parts or 'scripts' in parts:
        return True
    if 'module_admin' in parts and 'dao' in parts:
        return True
    if 'venv' in parts or '.pytest_cache' in parts:
        return True
    return False


def _is_dao_import(module: str | None) -> bool:
    if not module:
        return False
    return module == 'module_admin.dao' or module.startswith('module_admin.dao.')


def _collect_targets(root: Path) -> list[Path]:
    targets: set[Path] = set()
    for runtime_dir in RUNTIME_DIRS:
        dir_path = root / runtime_dir
        if dir_path.exists():
            for file_path in dir_path.rglob('*.py'):
                if not _should_skip(file_path):
                    targets.add(file_path)

    for runtime_file in RUNTIME_FILES:
        file_path = root / runtime_file
        if file_path.exists() and not _should_skip(file_path):
            targets.add(file_path)

    return sorted(targets)


def find_violations(root: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    for file_path in _collect_targets(root):
        try:
            source = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=str(file_path))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_dao_import(alias.name):
                        violations.append((file_path, node.lineno, f'import {alias.name}'))
            elif isinstance(node, ast.ImportFrom):
                if _is_dao_import(node.module):
                    violations.append((file_path, node.lineno, f'from {node.module} import ...'))
                elif node.module == 'module_admin' and any(alias.name == 'dao' for alias in node.names):
                    violations.append((file_path, node.lineno, 'from module_admin import dao'))
    return violations


def find_legacy_dao_paths(root: Path) -> list[Path]:
    found: list[Path] = []
    for rel_path in LEGACY_DAO_PATHS:
        target = root / rel_path
        if target.exists():
            found.append(target)
    return found


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = find_violations(root)
    legacy_paths = find_legacy_dao_paths(root)

    if not violations and not legacy_paths:
        print('DAO decommission check passed')
        return 0

    if violations:
        print('DAO import violations found (use repository layer instead):')
        for path, line, code in violations:
            rel_path = path.relative_to(root)
            print(f'{rel_path}:{line} -> {code}')

    if legacy_paths:
        print('Legacy DAO artifacts found (should not exist after decommission):')
        for path in legacy_paths:
            print(path.relative_to(root))

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
