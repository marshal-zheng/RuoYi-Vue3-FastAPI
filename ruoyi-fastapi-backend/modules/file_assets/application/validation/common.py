"""Shared validation helpers: wall-clock budgets and safe display names."""

from __future__ import annotations

import time
import unicodedata

from modules.file_assets.domain.errors import AssetInvalidError

MAX_NAME_LENGTH = 255
# Characters that would allow path traversal or response-header injection.
_FORBIDDEN_NAME_CHARS = frozenset('/\\"\x7f')


class Deadline:
    """Cooperative wall-clock budget checked between entries/streams (threads cannot be killed)."""

    def __init__(self, seconds: float, *, reason: str = 'PARSE_TIMEOUT'):
        self._expires = time.monotonic() + seconds
        self._reason = reason

    def check(self) -> None:
        if time.monotonic() > self._expires:
            raise AssetInvalidError(self._reason, '文件解析超时，无法完成校验')


def safe_display_name(raw: str | None) -> tuple[str, str]:
    """Return (stem-preserving display name, lowercased extension) or reject the name.

    Names are never used to build disk paths or object keys; they only feed metadata and
    Content-Disposition, so anything resembling a path or header control is refused.
    """
    name = unicodedata.normalize('NFC', (raw or '').strip())
    if not name:
        raise AssetInvalidError('INVALID_FILENAME', '文件名不能为空', field='file')
    if any(ord(char) < 0x20 for char in name) or any(char in _FORBIDDEN_NAME_CHARS for char in name):
        raise AssetInvalidError('INVALID_FILENAME', '文件名包含不允许的字符', field='file')
    if len(name) > MAX_NAME_LENGTH:
        raise AssetInvalidError('INVALID_FILENAME', '文件名过长', field='file')
    if name in {'.', '..'} or '.' not in name.strip('.'):
        raise AssetInvalidError('MISSING_EXTENSION', '文件缺少扩展名', field='file')
    stem, extension = name.rsplit('.', 1)
    if not stem.strip():
        raise AssetInvalidError('INVALID_FILENAME', '文件名不合法', field='file')
    return name, f'.{extension.lower()}'
