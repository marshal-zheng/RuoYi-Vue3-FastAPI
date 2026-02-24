#!/usr/bin/env python3
"""
Fail CI when service/controller runtime code reintroduces status flag magic literals.

Guarded fields:
- status
- del_flag
- is_locked
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TARGET_DIRS = [
    ROOT_DIR / 'module_admin' / 'service',
    ROOT_DIR / 'module_admin' / 'controller',
]
MAGIC_FLAG_PATTERN = re.compile(r"\b(status|del_flag|is_locked)\b\s*(==|!=|=)\s*['\"](0|1|2)['\"]")


def _iter_python_files():
    for directory in TARGET_DIRS:
        if not directory.exists():
            continue
        for file_path in directory.rglob('*.py'):
            yield file_path


def _is_ignorable_line(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith('#')


def main() -> int:
    violations: list[tuple[Path, int, str]] = []
    for file_path in _iter_python_files():
        for line_no, line in enumerate(file_path.read_text(encoding='utf-8').splitlines(), start=1):
            if _is_ignorable_line(line):
                continue
            if MAGIC_FLAG_PATTERN.search(line):
                violations.append((file_path, line_no, line.strip()))

    if violations:
        print('Found magic flag literals in runtime code. Use enums/constants instead:')
        for file_path, line_no, line in violations:
            rel_path = file_path.relative_to(ROOT_DIR)
            print(f'  - {rel_path}:{line_no}: {line}')
        return 1

    print('Magic flag literal check passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
