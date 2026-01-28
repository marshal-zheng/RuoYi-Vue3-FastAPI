#!/usr/bin/env python3
"""Static checks for sensitive field queries.

Flags:
- LIKE usage on sensitive fields
- direct == or in_ comparisons without sensitive_equals

Allowlist by adding '# sensitive-allow' on the same line.
"""
from pathlib import Path
import re
from typing import Dict, List, Tuple


SENSITIVE_FIELDS: Tuple[Tuple[str, str], ...] = (
    ('SysUser', 'phonenumber'),
    ('SysUser', 'email'),
    ('SysDept', 'phone'),
    ('SysUser', 'id_card'),
)

DISALLOWED_PATTERNS = (
    r'\.like\s*\(',
    r'==',
    r'\.in_\s*\(',
)


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if 'tests' in parts or 'alembic' in parts or 'scripts' in parts:
        return True
    if path.name.startswith('.'):
        return True
    return False


def _build_patterns() -> List[Tuple[re.Pattern, str]]:
    patterns: List[Tuple[re.Pattern, str]] = []
    for model, field in SENSITIVE_FIELDS:
        for token in DISALLOWED_PATTERNS:
            patterns.append((re.compile(rf'{model}\.{field}\s*{token}', re.S), f'{model}.{field}'))
    return patterns


def find_violations(root: Path) -> List[Dict[str, str]]:
    violations: List[Dict[str, str]] = []
    patterns = _build_patterns()
    for path in root.rglob('*.py'):
        if _should_skip(path):
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            continue
        lines = content.splitlines()
        for pattern, label in patterns:
            for match in pattern.finditer(content):
                line_no = content.count('\n', 0, match.start()) + 1
                line = lines[line_no - 1] if line_no - 1 < len(lines) else ''
                if 'sensitive-allow' in line:
                    continue
                violations.append({
                    'file': str(path),
                    'line': str(line_no),
                    'code': line.strip() or label,
                })
    return violations


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = find_violations(root)
    if not violations:
        print('Sensitive query check passed')
        return 0

    print('Sensitive query violations:')
    for item in violations:
        print(f"{item['file']}:{item['line']} -> {item['code']}")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
