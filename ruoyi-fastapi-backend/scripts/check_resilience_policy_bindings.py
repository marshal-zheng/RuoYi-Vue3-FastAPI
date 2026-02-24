#!/usr/bin/env python3
"""Ensure critical external call types are bound to resilience policies."""

from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = BACKEND_ROOT / 'resilience' / 'policy_bindings.json'
SCAN_DIRS = (
    BACKEND_ROOT / 'module_admin',
    BACKEND_ROOT / 'module_generator',
    BACKEND_ROOT / 'utils',
)
REDIS_PATTERN = re.compile(r'\.redis\.(get|set|setex|setnx|expire|delete|keys|info|dbsize|rpush|ltrim|llen|lrange|ping)\(')
REQUESTS_PATTERN = re.compile(r'\brequests\.(get|post|put|patch|delete)\(')


def _scan_operations() -> set[str]:
    operations: set[str] = set()
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for file_path in scan_dir.rglob('*.py'):
            text = file_path.read_text(encoding='utf-8')
            operations.update(f'redis.{name}' for name in REDIS_PATTERN.findall(text))
            operations.update(f'http.requests_{name}' for name in REQUESTS_PATTERN.findall(text))
    return operations


def _load_binding_ops() -> set[str]:
    payload = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    bindings = payload.get('bindings', [])
    result = set()
    for item in bindings:
        op = str(item.get('operation', '')).strip()
        if op:
            result.add(op)
    return result


def main() -> int:
    if not POLICY_PATH.exists():
        print(f'Missing resilience policy file: {POLICY_PATH}')
        return 1

    discovered = _scan_operations()
    bound = _load_binding_ops()
    missing = sorted(op for op in discovered if op not in bound)

    if missing:
        print('Unbound critical external call operations detected:')
        for item in missing:
            print(f'- {item}')
        return 1

    print(f'Resilience policy binding check passed ({len(discovered)} operations discovered)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
