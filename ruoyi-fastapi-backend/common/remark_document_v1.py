"""Frozen remark-a-v1 codec. No ORM, application services, HTML parsing or I/O.

Historical migrations must continue to import this version. An additive
admission may extend it only when every previously accepted document stays
accepted unchanged (2026-10-22: named text colors). Any other change of accepted
semantics requires a new codec/revision and an explicit conversion.
"""

import hashlib
import json
import re
from copy import deepcopy
from urllib.parse import unquote

from pydantic_core import Url

LIMITS = {
    'characters': 5000,
    'bytes': 256 * 1024,
    'nodes': 2000,
    'list_depth': 3,
    'tree_depth': 12,
    'container_depth': 32,
    'href': 2048,
}
BLOCK_ID = re.compile(r'^[a-z][a-z0-9]*_[a-z0-9]+$')
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff]')
# Same rank as the ZXUI schema, so canonical mark order matches the editor's.
MARK_ORDER = {'link': 0, 'textStyle': 1, 'bold': 2, 'italic': 3}
# ZXUI BASIC_RICH_TEXT_TEXT_COLORS; colors are stored by name, never as CSS.
TEXT_COLORS = ('red', 'orange', 'green', 'blue', 'purple', 'gray')


class RemarkError(ValueError):
    """A safe, content-free error suitable for a field validation response."""

    def __init__(self, code, path='remark'):
        self.code = code
        self.path = path
        super().__init__(f'{path}: {code}')


def _fail(code, path='remark'):
    raise RemarkError(code, path)


def _keys(value, required, optional=(), path='remark'):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        _fail('structure', path)


def _budget(value):
    stack = [(value, 1)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > 50000:
            _fail('resource-limit')
        if isinstance(item, (dict, list)):
            if depth > LIMITS['container_depth']:
                _fail('container-depth')
            children = item.values() if isinstance(item, dict) else item
            stack.extend((child, depth + 1) for child in children)
        elif isinstance(item, str):
            if CONTROL.search(item):
                _fail('unicode-control')
        elif item is not None and type(item) not in (int, float, bool):
            _fail('json-type')
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError):
        _fail('json-unicode')
    if len(encoded) > LIMITS['bytes']:
        _fail('bytes')


def validate_href(href):
    if not isinstance(href, str) or not href or len(href) > LIMITS['href']:
        _fail('link-length')
    if re.search(r'%(?![0-9a-fA-F]{2})', href):
        _fail('link-encoding')
    try:
        decoded = unquote(href, errors='strict')
    except UnicodeError:
        _fail('link-encoding')
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 or c in {'\\', '\ufeff'} for c in decoded):
        _fail('link-unsafe')
    if not re.match(r'^(https?://|mailto:|tel:)', href, re.IGNORECASE):
        _fail('link-protocol')
    try:
        # Reuse the existing WHATWG URL parser for host/IDNA/IP semantics.
        # Only validate here; preserving href avoids normalization drift.
        url = Url(href)
    except ValueError:
        _fail('link-target')
    if url.scheme in {'https', 'http'}:
        authority = re.match(r'^https?://([^/?#]*)', href, re.IGNORECASE)[1]
        if not authority or not url.host or url.username or url.password or re.search(r'[%@]', authority):
            _fail('link-host')
    elif url.host or not url.path:
        _fail('link-target')
    return href


def _marks(value, path):
    if not isinstance(value, list):
        _fail('marks', path)
    result, seen = [], set()
    for index, mark in enumerate(value):
        mark_path = f'{path}.marks.{index}'
        if not isinstance(mark, dict) or not isinstance(mark.get('type'), str) or mark['type'] not in MARK_ORDER:
            _fail('mark-type', path)
        kind = mark['type']
        if kind in seen:
            _fail('duplicate-mark', path)
        seen.add(kind)
        _keys(mark, ['type', 'attrs'] if kind in {'link', 'textStyle'} else ['type'], path=path)
        if kind == 'textStyle':
            attrs = mark['attrs']
            _keys(attrs, ['fontFamily', 'fontSize', 'color'], path=path)
            if attrs['fontFamily'] is not None or attrs['fontSize'] is not None or attrs['color'] not in TEXT_COLORS:
                _fail('text-style', path)
        if kind == 'link':
            attrs = mark['attrs']
            _keys(attrs, ['href', 'target', 'rel', 'class', 'title'], path=path)
            if (
                attrs['target'] != '_blank'
                or attrs['rel'] != 'noopener noreferrer nofollow'
                or attrs['class'] is not None
                or attrs['title'] is not None
            ):
                _fail('link-attributes', path)
            try:
                validate_href(attrs['href'])
            except RemarkError as error:
                raise RemarkError(error.code, f'{mark_path}.attrs.href') from None
        result.append(deepcopy(mark))
    return sorted(result, key=lambda m: MARK_ORDER[m['type']])


def _literal(node):
    if node['type'] == 'text':
        return node['text']
    if node['type'] == 'hardBreak':
        return '\n'
    separator = '' if node['type'] == 'paragraph' else '\n'
    return separator.join(_literal(n) for n in node.get('content', []))


def validate_remark(value):  # noqa: PLR0912, PLR0915 -- Frozen finite grammar boundary.
    """Accept only a full Document v2 object/null, return canonical JSON/null."""
    if value is None:
        return None
    _budget(value)
    _keys(value, ['version', 'body', 'annotations', 'assets', 'meta'])
    if type(value['version']) is not int or value['version'] != 2:
        _fail('version')
    if value['annotations'] != [] or value['assets'] != []:
        _fail('resources')
    if value['meta'] != {'schemaVersion': 'stable-block-identity/v2'}:
        _fail('meta')
    _keys(value['body'], ['format', 'content'])
    if value['body']['format'] != 'json':
        _fail('body-format')
    root = value['body']['content']
    if not isinstance(root, dict) or root.get('type') != 'doc':
        _fail('root')
    stack = [(root, 1, 0, 'remark.body.content')]
    ids, node_count = set(), 0
    allowed_children = {
        'doc': {'paragraph', 'bulletList', 'orderedList'},
        'paragraph': {'text', 'hardBreak'},
        'bulletList': {'listItem'},
        'orderedList': {'listItem'},
        'listItem': {'paragraph', 'bulletList', 'orderedList'},
        'text': set(),
        'hardBreak': set(),
    }
    while stack:
        n, depth, list_depth, path = stack.pop()
        node_count += 1
        if node_count > LIMITS['nodes']:
            _fail('nodes', path)
        if depth > LIMITS['tree_depth']:
            _fail('tree-depth', path)
        if not isinstance(n, dict) or not isinstance(n.get('type'), str) or n['type'] not in allowed_children:
            _fail('node-type', path)
        kind = n['type']
        if kind in {'bulletList', 'orderedList'}:
            list_depth += 1
        if list_depth > LIMITS['list_depth']:
            _fail('list-depth', path)
        required = ['type']
        optional = []
        if kind not in {'doc', 'text', 'hardBreak'}:
            required.append('attrs')
        if kind == 'text':
            required.append('text')
        if kind in {'text', 'hardBreak'}:
            optional.append('marks')
        else:
            optional.append('content')
        _keys(n, required, optional, path)
        if 'attrs' in required:
            attrs = n['attrs']
            expected = ['blockId'] + (
                ['textAlign'] if kind == 'paragraph' else ['start', 'type'] if kind == 'orderedList' else []
            )
            _keys(attrs, expected, path=path)
            bid = attrs['blockId']
            if not isinstance(bid, str) or not 4 <= len(bid) <= 64 or not BLOCK_ID.fullmatch(bid) or bid in ids:
                _fail('block-id', path)
            ids.add(bid)
            if kind == 'paragraph' and attrs['textAlign'] is not None:
                _fail('text-align', path)
            if kind == 'orderedList' and (
                attrs['type'] is not None or type(attrs['start']) is not int or not 1 <= attrs['start'] <= 1000000
            ):
                _fail('list-start', path)
        if kind == 'text' and (
            not isinstance(n['text'], str) or not n['text'] or '\n' in n['text'] or '\r' in n['text']
        ):
            _fail('text', path)
        if 'marks' in n:
            _marks(n['marks'], path)
        children = n.get('content', [])
        if not isinstance(children, list):
            _fail('children', path)
        if kind in {'doc', 'listItem', 'bulletList', 'orderedList'} and not children:
            _fail('empty-block', path)
        if kind == 'listItem' and (not isinstance(children[0], dict) or children[0].get('type') != 'paragraph'):
            _fail('list-item-first-paragraph', path)
        for i, child in enumerate(children):
            if (
                not isinstance(child, dict)
                or not isinstance(child.get('type'), str)
                or child['type'] not in allowed_children[kind]
            ):
                _fail('parent-child', path)
            stack.append((child, depth + 1, list_depth, f'{path}.content.{i}'))
    result = deepcopy(value)

    def normalize(n):
        if 'marks' in n:
            marks = _marks(n['marks'], 'remark')
            if marks:
                n['marks'] = marks
            else:
                n.pop('marks')
        if 'content' in n:
            out = []
            for child in n['content']:
                normalize(child)
                if (
                    out
                    and child['type'] == 'text'
                    and out[-1]['type'] == 'text'
                    and child.get('marks') == out[-1].get('marks')
                ):
                    out[-1]['text'] += child['text']
                else:
                    out.append(child)
            if out:
                n['content'] = out
            else:
                n.pop('content')

    normalize(result['body']['content'])
    if len(_literal(result['body']['content'])) > LIMITS['characters']:
        _fail('characters')
    _budget(result)
    nodes = result['body']['content']['content']
    if len(nodes) == 1 and nodes[0]['type'] == 'paragraph' and not nodes[0].get('content'):
        return None
    return result


def plain_to_remark(text, *, identity_key):
    if text is None or text == '':
        return None
    if not isinstance(text, str):
        _fail('plaintext-type')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if len(text) > LIMITS['characters']:
        _fail('characters')
    paragraphs = []
    for i, part in enumerate(text.split('\n')):
        seed = json.dumps(['remark-a-v1', identity_key, i, text], ensure_ascii=False, separators=(',', ':'))
        try:
            bid = 'blk_' + hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]
        except UnicodeError:
            _fail('unicode')
        node = {'type': 'paragraph', 'attrs': {'textAlign': None, 'blockId': bid}}
        if part:
            node['content'] = [{'type': 'text', 'text': part}]
        paragraphs.append(node)
    return validate_remark(
        {
            'version': 2,
            'body': {'format': 'json', 'content': {'type': 'doc', 'content': paragraphs}},
            'annotations': [],
            'assets': [],
            'meta': {'schemaVersion': 'stable-block-identity/v2'},
        }
    )


def remark_to_storage(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    return validate_remark(value)


def remark_literal_text(document):
    value = remark_to_storage(document)
    return _literal(value['body']['content']) if value else ''


def remark_display_text(document):
    value = remark_to_storage(document)
    if value is None:
        return ''

    def blocks(nodes, depth=0):
        lines = []
        for n in nodes:
            if n['type'] == 'paragraph':
                lines.append(_literal(n))
            else:
                for i, item in enumerate(n['content']):
                    prefix = f'{n["attrs"]["start"] + i}. ' if n['type'] == 'orderedList' else '- '
                    first = True
                    for child in item['content']:
                        if child['type'] == 'paragraph':
                            text_lines = _literal(child).split('\n')
                            for text in text_lines:
                                lines.append('  ' * depth + (prefix if first else ' ' * len(prefix)) + text)
                                first = False
                        else:
                            lines.append(blocks([child], depth + 1))
        return '\n'.join(lines)

    return blocks(value['body']['content']['content'])
