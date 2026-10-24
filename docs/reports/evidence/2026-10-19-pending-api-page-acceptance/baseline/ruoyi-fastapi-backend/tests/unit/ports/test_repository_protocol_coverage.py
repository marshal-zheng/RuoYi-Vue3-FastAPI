import ast
from pathlib import Path

import ports


def _collect_repository_class_names() -> set[str]:
    """Collect repository class names that require protocol contracts."""
    repository_roots = (
        Path(__file__).resolve().parents[3] / 'module_admin' / 'repository',
        Path(__file__).resolve().parents[3] / 'module_generator' / 'repository',
    )
    class_names: set[str] = set()
    ignored = {'BaseRepository', 'IRepository'}

    for root in repository_roots:
        for file in sorted(root.glob('*_repository.py')):
            tree = ast.parse(file.read_text(encoding='utf-8'))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                if node.name.startswith('_') or node.name in ignored:
                    continue
                has_public_method = any(
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name != '__init__'
                    and not item.name.startswith('_')
                    for item in node.body
                )
                if has_public_method:
                    class_names.add(node.name)
    return class_names


def test_repository_protocols_cover_all_public_repository_classes() -> None:
    repository_classes = _collect_repository_class_names()
    exported = set(ports.__all__)
    missing = sorted(f'I{name}' for name in repository_classes if f'I{name}' not in exported)

    assert not missing, f'Missing repository protocols: {missing}'
