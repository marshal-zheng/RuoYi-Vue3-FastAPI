#!/usr/bin/env python3
"""Block newly introduced classmethod business service entries."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
BASELINE_PATH = REPO_ROOT / 'docs/specs/backend-arch-p2-dependency-injection/baselines/service_classmethod_allowlist.txt'
SERVICE_DIRS = (
    BACKEND_ROOT / 'module_admin' / 'service',
    BACKEND_ROOT / 'module_generator' / 'service',
)


def _iter_service_files() -> list[Path]:
    files: list[Path] = []
    for service_dir in SERVICE_DIRS:
        if service_dir.exists():
            files.extend(sorted(service_dir.rglob('*.py')))
    return files


def _collect_classmethod_entries() -> list[str]:
    entries: set[str] = set()
    for file_path in _iter_service_files():
        tree = ast.parse(file_path.read_text(encoding='utf-8'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith('Service'):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                decorator_names = {
                    decorator.id
                    for decorator in item.decorator_list
                    if isinstance(decorator, ast.Name)
                }
                if 'classmethod' not in decorator_names:
                    continue
                entries.add(
                    f'{file_path.relative_to(REPO_ROOT)}::{node.name}::{item.name}'
                )
    return sorted(entries)


def _write_baseline(entries: list[str]) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text('\n'.join(entries) + '\n', encoding='utf-8')


def _load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(
            f'Baseline not found: {BASELINE_PATH}. '
            'Run with --write-baseline to initialize.'
        )
    lines = [line.strip() for line in BASELINE_PATH.read_text(encoding='utf-8').splitlines()]
    return {line for line in lines if line and not line.startswith('#')}


def main() -> int:
    parser = argparse.ArgumentParser(description='Check for newly introduced service classmethods.')
    parser.add_argument('--write-baseline', action='store_true', help='Write current scan result as baseline.')
    args = parser.parse_args()

    current_entries = _collect_classmethod_entries()

    if args.write_baseline:
        _write_baseline(current_entries)
        print(f'Wrote classmethod baseline: {BASELINE_PATH} ({len(current_entries)} entries)')
        return 0

    baseline_entries = _load_baseline()
    newly_added = sorted(set(current_entries) - baseline_entries)

    if newly_added:
        print('New service classmethod entries detected (not allowed):')
        for entry in newly_added:
            print(f'- {entry}')
        return 1

    print(f'Service classmethod regression check passed ({len(current_entries)} tracked entries)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
