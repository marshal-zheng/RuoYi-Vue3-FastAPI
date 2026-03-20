#!/usr/bin/env python3
"""Validate standards mapping coverage for jwt-security-hardcut spec."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_AC_IDS = [
    'R1.AC1', 'R1.AC2', 'R1.AC3',
    'R2.AC1', 'R2.AC2', 'R2.AC3', 'R2.AC4',
    'R3.AC1', 'R3.AC2', 'R3.AC3', 'R3.AC4',
    'R4.AC1', 'R4.AC2', 'R4.AC3', 'R4.AC4', 'R4.AC5',
    'R5.AC1', 'R5.AC2', 'R5.AC3',
    'R6.AC1', 'R6.AC2', 'R6.AC3',
    'R7.AC1', 'R7.AC2', 'R7.AC3', 'R7.AC4', 'R7.AC5',
    'R8.AC1', 'R8.AC2', 'R8.AC3', 'R8.AC4',
    'R9.AC1', 'R9.AC2', 'R9.AC3',
    'R10.AC1', 'R10.AC2', 'R10.AC3',
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    mapping_path = repo_root / 'docs/specs/jwt-security-hardcut/standards-mapping.json'
    data = json.loads(mapping_path.read_text(encoding='utf-8'))
    controls = data.get('controls', [])

    by_id = {item.get('id'): item for item in controls if item.get('id')}
    missing = [ac for ac in REQUIRED_AC_IDS if ac not in by_id]
    invalid = []
    for ac, item in by_id.items():
        standards = item.get('standards', [])
        if not isinstance(standards, list) or not standards:
            invalid.append(ac)

    if missing or invalid:
        print('Security mapping validation failed')
        if missing:
            print('Missing AC IDs:')
            for ac in missing:
                print(f'  - {ac}')
        if invalid:
            print('AC IDs without standards mapping:')
            for ac in invalid:
                print(f'  - {ac}')
        return 1

    print(f'Security mapping validation passed ({len(REQUIRED_AC_IDS)} AC items covered)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
