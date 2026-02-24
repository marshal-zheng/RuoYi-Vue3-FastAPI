#!/usr/bin/env python3
"""Validate implementation signatures are synchronized with protocol contracts."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ParameterShape:
    name: str
    kind: str
    has_default: bool


@dataclass(frozen=True)
class MethodShape:
    is_async: bool
    parameters: tuple[ParameterShape, ...]


def _iter_python_files(paths: list[Path] | tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.exists():
            files.extend(sorted(path.rglob('*.py')))
    return files


def _method_mode(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return 'instance'
    decorators = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
    if 'classmethod' in decorators:
        return 'class'
    if 'staticmethod' in decorators:
        return 'static'
    return 'instance'


def _extract_method_shape(node: ast.AST, mode: str, is_protocol: bool = False) -> MethodShape:
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

    args = node.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parameters: list[ParameterShape] = []

    for index, arg in enumerate(positional):
        default = defaults[index]
        if is_protocol and index == 0 and arg.arg == 'self':
            continue
        if mode == 'instance' and index == 0 and arg.arg == 'self':
            continue
        if mode == 'class' and index == 0 and arg.arg == 'cls':
            continue
        parameters.append(ParameterShape(name=arg.arg, kind='positional', has_default=default is not None))

    if args.vararg:
        parameters.append(ParameterShape(name=args.vararg.arg, kind='vararg', has_default=False))

    for index, arg in enumerate(args.kwonlyargs):
        default = args.kw_defaults[index]
        parameters.append(ParameterShape(name=arg.arg, kind='kwonly', has_default=default is not None))

    if args.kwarg:
        parameters.append(ParameterShape(name=args.kwarg.arg, kind='kwarg', has_default=False))

    return MethodShape(is_async=isinstance(node, ast.AsyncFunctionDef), parameters=tuple(parameters))


def _collect_protocol_shapes(file_path: Path) -> dict[str, dict[str, MethodShape]]:
    tree = ast.parse(file_path.read_text(encoding='utf-8'))
    protocol_shapes: dict[str, dict[str, MethodShape]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not node.name.startswith('I') or node.name in {'IBaseRepository', 'IBaseService'}:
            continue
        methods: dict[str, MethodShape] = {}
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.name.startswith('_'):
                continue
            methods[item.name] = _extract_method_shape(item, mode='instance', is_protocol=True)
        protocol_shapes[node.name] = methods
    return protocol_shapes


def _collect_impl_shapes(category: str) -> dict[str, tuple[Path, dict[str, MethodShape]]]:
    if category == 'repository':
        dirs = (ROOT / 'module_admin' / 'repository', ROOT / 'module_generator' / 'repository')

        def matcher(file_name: str) -> bool:
            return file_name.endswith('_repository.py')

        def class_filter(class_name: str) -> bool:
            return class_name not in {'IRepository', 'BaseRepository'} and not class_name.startswith('_')

    else:
        dirs = (ROOT / 'module_admin' / 'service', ROOT / 'module_generator' / 'service')

        def matcher(file_name: str) -> bool:
            return file_name.endswith('.py')

        def class_filter(class_name: str) -> bool:
            return class_name.endswith('Service')

    shapes: dict[str, tuple[Path, dict[str, MethodShape]]] = {}
    for file_path in _iter_python_files(dirs):
        if not matcher(file_path.name):
            continue
        tree = ast.parse(file_path.read_text(encoding='utf-8'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not class_filter(node.name):
                continue
            methods: dict[str, MethodShape] = {}
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith('_') or item.name == '__init__':
                    continue
                mode = _method_mode(item)
                methods[item.name] = _extract_method_shape(item, mode=mode, is_protocol=False)
            if methods:
                shapes[node.name] = (file_path, methods)
    return shapes


def _compare_shapes(
    impl_name: str, impl_methods: dict[str, MethodShape], protocol_methods: dict[str, MethodShape]
) -> list[str]:
    errors: list[str] = []

    impl_set = set(impl_methods.keys())
    protocol_set = set(protocol_methods.keys())

    missing = sorted(impl_set - protocol_set)
    extra = sorted(protocol_set - impl_set)

    if missing:
        errors.append(f'missing protocol methods: {missing}')
    if extra:
        errors.append(f'protocol has extra methods: {extra}')

    for method_name in sorted(impl_set & protocol_set):
        impl_shape = impl_methods[method_name]
        protocol_shape = protocol_methods[method_name]

        if impl_shape.is_async != protocol_shape.is_async:
            errors.append(
                f'method async mismatch for `{method_name}`: '
                f'impl={impl_shape.is_async} protocol={protocol_shape.is_async}'
            )
            continue

        if impl_shape.parameters != protocol_shape.parameters:
            errors.append(
                f'method signature mismatch for `{method_name}`: '
                f'impl={impl_shape.parameters} protocol={protocol_shape.parameters}'
            )

    return errors


def main() -> int:
    protocol_repository = _collect_protocol_shapes(ROOT / 'ports' / 'repositories.py')
    protocol_service = _collect_protocol_shapes(ROOT / 'ports' / 'services.py')
    impl_repository = _collect_impl_shapes('repository')
    impl_service = _collect_impl_shapes('service')

    failures: list[str] = []

    for class_name, (file_path, methods) in sorted(impl_repository.items()):
        protocol_name = f'I{class_name}'
        protocol_methods = protocol_repository.get(protocol_name)
        if protocol_methods is None:
            failures.append(
                f'[repository] {class_name} ({file_path.relative_to(ROOT)}): missing protocol `{protocol_name}`'
            )
            continue
        failures.extend(
            f'[repository] {class_name} ({file_path.relative_to(ROOT)}): {error}'
            for error in _compare_shapes(class_name, methods, protocol_methods)
        )

    for class_name, (file_path, methods) in sorted(impl_service.items()):
        protocol_name = f'I{class_name}'
        protocol_methods = protocol_service.get(protocol_name)
        if protocol_methods is None:
            failures.append(
                f'[service] {class_name} ({file_path.relative_to(ROOT)}): missing protocol `{protocol_name}`'
            )
            continue
        failures.extend(
            f'[service] {class_name} ({file_path.relative_to(ROOT)}): {error}'
            for error in _compare_shapes(class_name, methods, protocol_methods)
        )

    if failures:
        print('Protocol update check failed:')
        for failure in failures:
            print(f'- {failure}')
        return 1

    print('Protocol update check passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
