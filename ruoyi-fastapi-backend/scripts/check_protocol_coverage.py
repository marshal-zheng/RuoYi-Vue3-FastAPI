#!/usr/bin/env python3
"""Check protocol coverage for repository and service classes."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TargetClass:
    category: str
    name: str
    path: Path

    @property
    def protocol_name(self) -> str:
        return f'I{self.name}'


def _iter_python_files(paths: list[Path] | tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.exists():
            files.extend(sorted(path.rglob('*.py')))
    return files


def _public_methods(class_node: ast.ClassDef) -> list[ast.AST]:
    methods: list[ast.AST] = []
    for node in class_node.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith('_') or node.name == '__init__':
            continue
        methods.append(node)
    return methods


def _collect_repository_targets() -> list[TargetClass]:
    targets: list[TargetClass] = []
    ignored = {'IRepository', 'BaseRepository'}
    repo_dirs = (
        ROOT / 'module_admin' / 'repository',
        ROOT / 'module_generator' / 'repository',
    )

    for file_path in _iter_python_files(repo_dirs):
        if not file_path.name.endswith('_repository.py'):
            continue
        tree = ast.parse(file_path.read_text(encoding='utf-8'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.startswith('_') or node.name in ignored:
                continue
            if not _public_methods(node):
                continue
            targets.append(TargetClass(category='repository', name=node.name, path=file_path))
    return targets


def _collect_service_targets() -> list[TargetClass]:
    targets: list[TargetClass] = []
    service_dirs = (
        ROOT / 'module_admin' / 'service',
        ROOT / 'module_generator' / 'service',
    )
    for file_path in _iter_python_files(service_dirs):
        tree = ast.parse(file_path.read_text(encoding='utf-8'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith('Service'):
                continue
            if not _public_methods(node):
                continue
            targets.append(TargetClass(category='service', name=node.name, path=file_path))
    return targets


def _read_ports_exports() -> set[str]:
    ports_init = ROOT / 'ports' / '__init__.py'
    tree = ast.parse(ports_init.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == '__all__'
                    and isinstance(node.value, (ast.List, ast.Tuple))
                ):
                    exports = [
                        item.value
                        for item in node.value.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    ]
                    return set(exports)
    return set()


def _build_report() -> dict:
    repository_targets = _collect_repository_targets()
    service_targets = _collect_service_targets()
    all_targets = repository_targets + service_targets
    exports = _read_ports_exports()

    missing = [
        {
            'category': target.category,
            'class_name': target.name,
            'protocol_name': target.protocol_name,
            'path': str(target.path.relative_to(ROOT)),
        }
        for target in all_targets
        if target.protocol_name not in exports
    ]

    total = len(all_targets)
    covered = total - len(missing)
    coverage = 100.0 if total == 0 else round((covered / total) * 100, 2)

    return {
        'summary': {
            'total_classes': total,
            'covered_classes': covered,
            'missing_classes': len(missing),
            'coverage_percent': coverage,
        },
        'categories': {
            'repository': len(repository_targets),
            'service': len(service_targets),
        },
        'missing': missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Check protocol coverage.')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args()

    report = _build_report()
    missing = report['missing']

    if args.format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        summary = report['summary']
        print('Protocol coverage report')
        print(f'- Total classes: {summary["total_classes"]}')
        print(f'- Covered classes: {summary["covered_classes"]}')
        print(f'- Missing classes: {summary["missing_classes"]}')
        print(f'- Coverage: {summary["coverage_percent"]}%')
        if missing:
            print('Missing contracts:')
            for item in missing:
                print(f'- [{item["category"]}] {item["class_name"]} -> {item["protocol_name"]} ({item["path"]})')

    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
