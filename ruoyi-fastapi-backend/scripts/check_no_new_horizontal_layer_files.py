#!/usr/bin/env python3
"""Guard against adding new business files under horizontal layer directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = (
    ROOT.parent
    / 'docs'
    / 'specs'
    / 'backend-arch-p3-vertical-slice-ddd'
    / 'baselines'
    / 'horizontal-layer-files-allowlist.txt'
)

HORIZONTAL_LAYER_DIRS = (
    ROOT / 'module_admin' / 'controller',
    ROOT / 'module_admin' / 'service',
    ROOT / 'module_admin' / 'repository',
    ROOT / 'module_admin' / 'entity',
    ROOT / 'module_generator' / 'controller',
    ROOT / 'module_generator' / 'service',
    ROOT / 'module_generator' / 'repository',
    ROOT / 'module_generator' / 'entity',
)


def _collect_current_files() -> list[str]:
    files: set[str] = set()
    for directory in HORIZONTAL_LAYER_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob('*.py'):
            if '__pycache__' in path.parts:
                continue
            files.add(path.relative_to(ROOT.parent).as_posix())
    return sorted(files)


def _read_baseline(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(
        line.strip()
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.strip().startswith('#')
    )


def _write_baseline(path: Path, entries: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(entries) + ('\n' if entries else ''), encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Check no new files under horizontal-layer business directories.')
    parser.add_argument('--baseline', type=Path, default=DEFAULT_BASELINE)
    parser.add_argument('--write-baseline', action='store_true')
    args = parser.parse_args()

    current = _collect_current_files()
    if args.write_baseline:
        _write_baseline(args.baseline, current)
        print(f'Wrote baseline with {len(current)} entries to {args.baseline}')
        return 0

    baseline = _read_baseline(args.baseline)
    if not baseline:
        print(f'Baseline file not found or empty: {args.baseline}')
        print('Run with --write-baseline to initialize.')
        return 1

    baseline_set = set(baseline)
    new_files = [entry for entry in current if entry not in baseline_set]
    if new_files:
        print('New files detected under horizontal-layer directories (not allowed):')
        for entry in new_files:
            print(f'- {entry}')
        return 1

    print(f'Horizontal-layer file regression check passed ({len(baseline)} tracked entries)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
