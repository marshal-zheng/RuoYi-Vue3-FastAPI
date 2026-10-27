"""Existing remark grammar normalization, followed by the shared codec (no new document codec)."""

from copy import deepcopy
from uuid import uuid4

from pydantic_core import from_json

from common.remark_document_v1 import LIMITS, RemarkError, validate_remark
from modules.system.application.services.ai_providers.base import AIError


def _invalid_output():
    return AIError('invalid-output')


def normalize_output(content: str):  # noqa: PLR0912 -- Finite grammar defaults before the shared codec.
    """Supply structural defaults and new block identities, then use the frozen remark codec."""
    try:
        root = from_json(content, allow_inf_nan=False)
        if not isinstance(root, dict) or root.get('type') != 'doc':
            raise _invalid_output()
        root = deepcopy(root)
        stack, count = [(root, 1)], 0
        while stack:
            node, depth = stack.pop()
            count += 1
            if count > LIMITS['nodes'] or depth > LIMITS['tree_depth']:
                raise AIError('output-limit')
            if not isinstance(node, dict):
                raise _invalid_output()
            kind = node.get('type')
            if kind in {'paragraph', 'bulletList', 'orderedList', 'listItem'}:
                attrs = node.setdefault('attrs', {})
                if not isinstance(attrs, dict):
                    raise _invalid_output()
                attrs['blockId'] = 'blk_' + uuid4().hex
                if kind == 'paragraph':
                    attrs.setdefault('textAlign', None)
                elif kind == 'orderedList':
                    attrs.setdefault('start', 1)
                    attrs.setdefault('type', None)
            marks = node.get('marks', [])
            if not isinstance(marks, list):
                raise _invalid_output()
            for mark in marks:
                if not isinstance(mark, dict):
                    raise _invalid_output()
                if mark.get('type') in {'link', 'textStyle'}:
                    attrs = mark.setdefault('attrs', {})
                    if not isinstance(attrs, dict):
                        raise _invalid_output()
                    defaults = (
                        {'target': '_blank', 'rel': 'noopener noreferrer nofollow', 'class': None, 'title': None}
                        if mark['type'] == 'link'
                        else {'fontFamily': None, 'fontSize': None}
                    )
                    for key, value in defaults.items():
                        attrs.setdefault(key, value)
            children = node.get('content', [])
            if not isinstance(children, list):
                raise _invalid_output()
            stack.extend((child, depth + 1) for child in children)
        result = validate_remark(
            {
                'version': 2,
                'body': {'format': 'json', 'content': root},
                'annotations': [],
                'assets': [],
                'meta': {'schemaVersion': 'stable-block-identity/v2'},
            }
        )
        if result is None:
            raise AIError('invalid-output')
        return result
    except RemarkError as error:
        if error.code in {
            'characters',
            'bytes',
            'nodes',
            'list-depth',
            'tree-depth',
            'container-depth',
            'resource-limit',
        }:
            raise AIError('output-limit') from None
        raise _invalid_output() from None
    except (ValueError, TypeError, RecursionError):
        raise _invalid_output() from None


def preview_text(content: str) -> str:
    """Extract only parsed body text; incomplete JSON syntax and reasoning never reach the UI."""
    try:
        root = from_json(content, allow_partial='trailing-strings', allow_inf_nan=False, cache_strings=False)
    except ValueError:
        return ''

    def read(node, depth=0):
        if depth > LIMITS['tree_depth'] or not isinstance(node, dict):
            return ''
        kind = node.get('type')
        if kind == 'text':
            return node.get('text') if isinstance(node.get('text'), str) else ''
        if kind == 'hardBreak':
            return '\n'
        if kind not in {'doc', 'paragraph', 'bulletList', 'orderedList', 'listItem'}:
            return ''
        children = node.get('content', [])
        if not isinstance(children, list):
            return ''
        separator = '' if kind == 'paragraph' else '\n'
        return separator.join(read(child, depth + 1) for child in children)

    root = root.get('document') if isinstance(root, dict) else None
    return read(root) if isinstance(root, dict) and root.get('type') == 'doc' else ''
