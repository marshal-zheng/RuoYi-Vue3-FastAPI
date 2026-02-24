#!/usr/bin/env python3
"""Guardrail: system controllers must not regress to direct business service calls.

This check enforces P4 CQRS cutover constraints for system management controllers:
- read/write business logic should be dispatched through Mediator.
- controller-level service usage is only allowed for export mapping helpers and
  user import template generation.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET_CONTROLLERS = (
    ROOT / 'module_admin/controller/config_controller.py',
    ROOT / 'module_admin/controller/dict_controller.py',
    ROOT / 'module_admin/controller/dept_controller.py',
    ROOT / 'module_admin/controller/menu_controller.py',
    ROOT / 'module_admin/controller/notice_controller.py',
    ROOT / 'module_admin/controller/post_controller.py',
    ROOT / 'module_admin/controller/role_controller.py',
    ROOT / 'module_admin/controller/user_controller.py',
)

ALLOWED_HELPER_METHODS = {
    'get_user_import_template_services',
}
ALLOWED_HELPER_PREFIXES = (
    'export_',
)


@dataclass
class Violation:
    path: Path
    line: int
    service_ref: str
    method: str

    def render(self) -> str:
        rel_path = self.path.relative_to(ROOT)
        return f'{rel_path}:{self.line} -> {self.service_ref}.{self.method}()'


def _is_service_reference(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name) and (node.id.endswith('_service') or node.id.endswith('Service')):
        return node.id
    return None


def _is_allowed_helper_method(method_name: str) -> bool:
    if method_name in ALLOWED_HELPER_METHODS:
        return True
    return method_name.startswith(ALLOWED_HELPER_PREFIXES)


def _scan_controller(path: Path) -> list[Violation]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    violations: list[Violation] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue

        service_ref = _is_service_reference(node.func.value)
        if service_ref is None:
            continue

        method_name = node.func.attr
        if _is_allowed_helper_method(method_name):
            continue

        violations.append(
            Violation(
                path=path,
                line=node.lineno,
                service_ref=service_ref,
                method=method_name,
            )
        )

    return violations


def main() -> int:
    violations: list[Violation] = []
    for controller_path in TARGET_CONTROLLERS:
        if not controller_path.exists():
            print(f'Missing target controller: {controller_path}', file=sys.stderr)
            return 2
        violations.extend(_scan_controller(controller_path))

    if violations:
        print('CQRS controller cutover regression detected:')
        for item in sorted(violations, key=lambda v: (str(v.path), v.line, v.method)):
            print(f'  - {item.render()}')
        print(
            'Only export helpers and user import template helper are allowed. '
            'Move business calls to CommandHandler/QueryHandler.'
        )
        return 1

    print(f'CQRS controller cutover check passed ({len(TARGET_CONTROLLERS)} files scanned).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
