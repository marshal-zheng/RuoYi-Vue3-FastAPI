"""Shared placeholder grammar checks; never restore or retain personal originals on the server."""

import re
from urllib.parse import unquote

TOKEN = re.compile(r'\{\{(PHONE|EMAIL|ID|ADDRESS|PERSONAL)_([1-9][0-9]{0,2})\}\}')
PREFIXES = {'phone': 'PHONE', 'email': 'EMAIL', 'id': 'ID', 'address': 'ADDRESS', 'other': 'PERSONAL'}
RESERVED = ('{{', '}}', 'PHONE_', 'EMAIL_', 'ID_', 'ADDRESS_', 'PERSONAL_')


def text_tokens(text: str) -> set[str]:
    remaining = TOKEN.sub('', text)
    if any(part in remaining for part in RESERVED):
        raise ValueError('invalid placeholder')
    return {match.group() for match in TOKEN.finditer(text)}


def document_tokens(document) -> set[str]:
    tokens = set()
    count = 0

    def visit(value, depth=0):  # noqa: PLR0912 -- Finite JSON token-position validation.
        nonlocal count
        count += 1
        if depth > 48 or count > 20000:
            raise ValueError('document resource limit')
        if isinstance(value, str):
            if any(part in unquote(value) for part in RESERVED):
                raise ValueError('placeholder outside text')
        elif isinstance(value, list):
            for child in value:
                visit(child, depth + 1)
        elif isinstance(value, dict):
            children = value.get('content')
            if isinstance(children, list):
                run = []
                for child in [*children, None]:
                    if isinstance(child, dict) and child.get('type') == 'text' and isinstance(child.get('text'), str):
                        run.append(child['text'])
                    else:
                        if run and text_tokens(''.join(run)) != set().union(*(text_tokens(part) for part in run)):
                            raise ValueError('split placeholder')
                        run = []
            for key, child in value.items():
                if key == 'text' and value.get('type') == 'text' and isinstance(child, str):
                    tokens.update(text_tokens(child))
                else:
                    visit(child, depth + 1)

    visit(document)
    return tokens
