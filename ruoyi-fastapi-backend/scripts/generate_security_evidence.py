#!/usr/bin/env python3
"""Generate release evidence package for jwt-security-hardcut."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    mapping_path = repo_root / 'docs/specs/jwt-security-hardcut/standards-mapping.json'
    tasks_path = repo_root / 'docs/specs/jwt-security-hardcut/tasks.md'
    output_path = repo_root / 'docs/specs/jwt-security-hardcut/release-evidence.json'

    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    controls = mapping.get('controls', [])
    unique_standards = sorted({std for item in controls for std in item.get('standards', [])})
    covered_ac_ids = sorted({item.get('id') for item in controls if item.get('id')})

    tasks_text = tasks_path.read_text(encoding='utf-8')
    completed_tasks = tasks_text.count('- [x]')
    total_tasks = tasks_text.count('- [ ]') + completed_tasks

    report = {
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'spec': 'jwt-security-hardcut',
        'mappingVersion': mapping.get('version'),
        'coverage': {
            'acceptanceCriteriaCount': len(covered_ac_ids),
            'standardsCount': len(unique_standards),
            'standards': unique_standards,
        },
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
        },
        'riskWaivers': [],
    }

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(output_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
