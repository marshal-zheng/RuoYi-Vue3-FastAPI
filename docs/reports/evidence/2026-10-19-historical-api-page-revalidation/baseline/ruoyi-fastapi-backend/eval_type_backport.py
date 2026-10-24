"""Local fallback for pydantic on Python < 3.10 when `eval_type_backport` is unavailable."""

from __future__ import annotations

import ast
import typing
from typing import Any


def _is_typing_union(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        target = node.value
        if isinstance(target, ast.Name) and target.id == 'Union':
            return True
        if isinstance(target, ast.Attribute) and target.attr == 'Union':
            return True
    return False


def _union_items(node: ast.AST) -> list[ast.AST]:
    if _is_typing_union(node) and isinstance(node, ast.Subscript):
        union_slice = node.slice
        if isinstance(union_slice, ast.Tuple):
            return list(union_slice.elts)
        return [union_slice]
    return [node]


class _UnionTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        node = typing.cast(ast.BinOp, self.generic_visit(node))
        if not isinstance(node.op, ast.BitOr):
            return node

        left_items = _union_items(node.left)
        right_items = _union_items(node.right)
        union_items = left_items + right_items

        union_node = ast.Subscript(
            value=ast.Attribute(value=ast.Name(id='typing', ctx=ast.Load()), attr='Union', ctx=ast.Load()),
            slice=ast.Tuple(elts=union_items, ctx=ast.Load()),
            ctx=ast.Load(),
        )
        return ast.copy_location(union_node, node)


def eval_type_backport(
    value: Any,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
    *,
    try_default: bool = False,  # noqa: ARG001 - kept for compatibility with upstream signature
) -> Any:
    """Evaluate ForwardRef annotations containing ``X | Y`` syntax on Python 3.9."""

    evaluation_globals = dict(globalns or {})
    evaluation_globals.setdefault('typing', typing)
    evaluation_locals = dict(localns or {})

    if isinstance(value, typing.ForwardRef):
        expression = value.__forward_arg__
    elif isinstance(value, str):
        expression = value
    else:
        return value

    parsed = ast.parse(expression, mode='eval')
    transformed = _UnionTransformer().visit(parsed)
    ast.fix_missing_locations(transformed)
    compiled = compile(transformed, filename='<eval_type_backport>', mode='eval')
    return eval(compiled, evaluation_globals, evaluation_locals)
