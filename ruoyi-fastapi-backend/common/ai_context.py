"""Shared placeholder grammar checks; never restore or retain personal originals on the server."""

import re
from typing import Literal
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


AIErrorCode = Literal[
    'context-rejected',
    'policy-rejected',
    'permission-denied',
    'quota-exceeded',
    'provider-unavailable',
    'timeout',
    'invalid-output',
    'output-limit',
    'incomplete-output',
]


MESSAGES = {
    'context-rejected': 'AI 上下文已失效，请重新打开后重试',
    'policy-rejected': 'AI 策略已更新，请重新加载后重试',
    'permission-denied': '没有此操作权限',
    'quota-exceeded': 'AI 请求过于频繁，请稍后重试',
    'provider-unavailable': 'AI 服务暂不可用，请联系管理员或稍后重试',
    'timeout': 'AI 生成超时，请稍后重试',
    'invalid-output': 'AI 返回格式不符合要求，请重试或调整要求',
    'output-limit': 'AI 返回内容超过限制，请缩短要求后重试',
    'incomplete-output': 'AI 输出中断，请重试',
}


class AIError(Exception):
    def __init__(self, code: str):
        self.code = code
        self.message = MESSAGES[code]
        super().__init__(code)
