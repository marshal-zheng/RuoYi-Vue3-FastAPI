"""Small protocol boundary for the configured provider adapter."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

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


@dataclass(frozen=True)
class ProviderChunk:
    text: str = ''
    finish: str | None = None


class TextFieldProvider(Protocol):
    def stream(self, messages: list[dict]) -> AsyncIterator[ProviderChunk]: ...
