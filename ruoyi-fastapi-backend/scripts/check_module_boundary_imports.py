#!/usr/bin/env python3
"""Guard against cross-context internal imports in modules/*.

Rule:
- Cross-context imports are allowed only via `modules.<context>.ports`.
- TYPE_CHECKING-only imports are ignored for this gate.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES_ROOT = ROOT / 'modules'


@dataclass
class Violation:
    path: Path
    line: int
    import_stmt: str
    source_context: str
    target_context: str

    def render(self) -> str:
        relative = self.path.relative_to(ROOT.parent).as_posix()
        return (
            f'{relative}:{self.line} [{self.source_context}->{self.target_context}] '
            f'{self.import_stmt}'
        )


def _is_type_checking_guard(test: ast.expr) -> bool:
    if isinstance(test, ast.Name):
        return test.id == 'TYPE_CHECKING'
    if isinstance(test, ast.Attribute):
        return test.attr == 'TYPE_CHECKING'
    return False


class _BoundaryVisitor(ast.NodeVisitor):
    def __init__(self, *, path: Path, source_context: str):
        self.path = path
        self.source_context = source_context
        self.violations: list[Violation] = []
        self._in_type_checking = False

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        if not _is_type_checking_guard(node.test):
            self.generic_visit(node)
            return

        previous = self._in_type_checking
        self._in_type_checking = True
        for stmt in node.body:
            self.visit(stmt)
        self._in_type_checking = previous
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            self._check_import(alias.name, node.lineno, f'import {alias.name}')

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.level and node.module is None:
            return
        module_name = node.module or ''
        self._check_import(module_name, node.lineno, f'from {module_name} import ...')

    def _check_import(self, module_name: str, line: int, import_stmt: str) -> None:
        if self._in_type_checking:
            return
        if not module_name.startswith('modules.'):
            return

        parts = module_name.split('.')
        if len(parts) < 2:
            return
        target_context = parts[1]
        if target_context == self.source_context:
            return

        is_ports_import = len(parts) >= 3 and parts[2] == 'ports'
        if is_ports_import:
            return

        self.violations.append(
            Violation(
                path=self.path,
                line=line,
                import_stmt=import_stmt,
                source_context=self.source_context,
                target_context=target_context,
            )
        )


def _collect_module_files() -> list[Path]:
    if not MODULES_ROOT.exists():
        return []
    return sorted(
        path
        for path in MODULES_ROOT.rglob('*.py')
        if '__pycache__' not in path.parts and path.is_file()
    )


def _context_of(path: Path) -> str | None:
    relative = path.relative_to(MODULES_ROOT)
    if len(relative.parts) < 2:
        return None
    context = relative.parts[0]
    if context.startswith('__'):
        return None
    return context


def _write_report(report_path: Path, scanned: int, violations: list[Violation]) -> None:
    rel = lambda p: p.relative_to(ROOT.parent).as_posix()
    edge_counter: Counter[str] = Counter()
    context_counter: Counter[str] = Counter()
    for item in violations:
        edge_key = f'{item.source_context}->{item.target_context}'
        edge_counter[edge_key] += 1
        context_counter[item.source_context] += 1

    payload = {
        'scanned_files': scanned,
        'violations_count': len(violations),
        'violations_by_edge': dict(sorted(edge_counter.items())),
        'violations_by_source_context': dict(sorted(context_counter.items())),
        'violations': [
            {
                'file': rel(item.path),
                'line': item.line,
                'source_context': item.source_context,
                'target_context': item.target_context,
                'import': item.import_stmt,
            }
            for item in sorted(violations, key=lambda v: (str(v.path), v.line))
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Check module boundary imports for cross-context violations.')
    parser.add_argument('--report', type=Path, default=None, help='Optional JSON report output path.')
    args = parser.parse_args()

    violations: list[Violation] = []
    scanned = 0

    for file_path in _collect_module_files():
        context = _context_of(file_path)
        if context is None:
            continue
        scanned += 1
        tree = ast.parse(file_path.read_text(encoding='utf-8'), filename=str(file_path))
        visitor = _BoundaryVisitor(path=file_path, source_context=context)
        visitor.visit(tree)
        violations.extend(visitor.violations)

    if args.report is not None:
        _write_report(args.report, scanned, violations)

    if violations:
        print('Cross-context boundary violations detected:')
        for violation in sorted(violations, key=lambda v: (str(v.path), v.line)):
            print(f'- {violation.render()}')
        print('Only cross-context imports via modules.<context>.ports are allowed at runtime.')
        return 1

    print(f'Module boundary import check passed ({scanned} files scanned).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
