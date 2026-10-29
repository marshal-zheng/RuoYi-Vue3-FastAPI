"""PDF structure and UTF-8 text checks; nothing is rendered, executed or parsed as a spreadsheet."""

from __future__ import annotations

import codecs
from typing import TYPE_CHECKING

from modules.file_assets.domain.errors import AssetInvalidError, AssetUnsupportedTypeError

if TYPE_CHECKING:
    from pathlib import Path

_CHUNK = 64 * 1024
_ALLOWED_CONTROLS = frozenset('\t\n\r\f')


def check_pdf(path: Path, size: int) -> None:
    with path.open('rb') as handle:
        head = handle.read(1024)
        handle.seek(max(0, size - 2048))
        tail = handle.read(2048)
    if b'%PDF-' not in head:
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容不是 PDF')
    if b'%%EOF' not in tail or b'startxref' not in tail:
        raise AssetInvalidError('PDF_CORRUPT', 'PDF 文件结构不完整')


def check_utf8_text(path: Path) -> None:
    """Strict UTF-8 (optional BOM); NUL and other C0 controls mean binary content."""
    decoder = codecs.getincrementaldecoder('utf-8-sig')(errors='strict')
    with path.open('rb') as handle:
        while chunk := handle.read(_CHUNK):
            try:
                text = decoder.decode(chunk)
            except UnicodeDecodeError:
                raise AssetInvalidError('TEXT_NOT_UTF8', '文本文件必须是 UTF-8 编码') from None
            if any(ord(char) < 0x20 and char not in _ALLOWED_CONTROLS for char in text):
                raise AssetUnsupportedTypeError('TEXT_BINARY_CONTENT', '文本文件包含二进制内容')
        try:
            decoder.decode(b'', final=True)
        except UnicodeDecodeError:
            raise AssetInvalidError('TEXT_NOT_UTF8', '文本文件必须是 UTF-8 编码') from None
