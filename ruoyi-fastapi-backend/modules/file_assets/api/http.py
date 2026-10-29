"""HTTP helpers shared by the generic upload and business upload endpoints."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote

from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

from modules.file_assets.application.asset_service import IncomingFile
from modules.file_assets.domain.errors import AssetInvalidError, AssetTooLargeError, FileAssetError

if TYPE_CHECKING:
    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession

MAX_TEXT_FIELDS = 4
MAX_TEXT_FIELD_BYTES = 256
_ASCII_FALLBACK = re.compile(r'[^A-Za-z0-9._()\- ]+')


@dataclass
class ParsedUpload:
    incoming: IncomingFile
    fields: dict[str, str]


async def release_request_transaction(session: AsyncSession) -> None:
    """End the auth lookup transaction so no connection is held during file or storage I/O."""
    if session.in_transaction():
        await session.commit()


async def read_upload_form(request: Request, file_field: str) -> ParsedUpload:
    """Parse after authentication; the ASGI body cap already bounds bytes and receive time."""
    try:
        form = await request.form(max_files=1, max_fields=MAX_TEXT_FIELDS, max_part_size=MAX_TEXT_FIELD_BYTES)
    except FileAssetError:
        raise  # body cap (413) and receive deadline (408) raised from the ASGI receive wrapper
    except HTTPException as exc:
        message = str(exc.detail or '')
        if 'maximum size' in message:
            raise AssetInvalidError('FORM_FIELD_TOO_LONG', '上传参数过长') from None
        if 'Too many files' in message:
            raise AssetInvalidError('TOO_MANY_FILES', '一次只能上传一个文件', field=file_field) from None
        if 'Too many fields' in message:
            raise AssetInvalidError('TOO_MANY_FIELDS', '上传参数过多') from None
        raise AssetInvalidError('MULTIPART_INVALID', '上传请求格式不正确') from None
    except Exception:
        # Malformed multipart framing surfaces from the parser library itself.
        raise AssetInvalidError('MULTIPART_INVALID', '上传请求格式不正确') from None
    files = [value for value in form.multi_items() if isinstance(value[1], UploadFile)]
    upload = form.get(file_field)
    if len(files) != 1 or not isinstance(upload, UploadFile):
        await form.close()
        raise AssetInvalidError('FILE_REQUIRED', '请选择一个文件', field=file_field)
    fields: dict[str, str] = {}
    for key, value in form.multi_items():
        if isinstance(value, UploadFile):
            continue
        if key in fields:
            await form.close()
            raise AssetInvalidError('DUPLICATE_FIELD', '上传参数重复', field=key)
        fields[key] = value
    return ParsedUpload(
        incoming=IncomingFile(
            stream=upload.file, filename=upload.filename, content_type=upload.content_type, close=form.close
        ),
        fields=fields,
    )


def etag_for(sha256: str) -> str:
    return f'"{sha256}"'


def etag_matches(header: str | None, sha256: str) -> bool:
    """RFC 9110 weak comparison: lists, `*` and `W/` (gzip gateways weaken validators)."""
    if not header or not sha256:
        return False
    expected = etag_for(sha256)
    for candidate in header.split(','):
        tag = candidate.strip()
        if tag == '*':
            return True
        if tag.startswith('W/'):
            tag = tag[2:]
        if tag == expected:
            return True
    return False


def _ascii(text: str) -> str:
    return _ASCII_FALLBACK.sub('_', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()).strip(' ._')


def content_disposition(inline: bool, name: str) -> str:
    """Safe ASCII fallback plus RFC 5987 UTF-8 name; no raw header characters are echoed."""
    stem, dot, extension = name.rpartition('.')
    if not dot:
        stem, extension = name, ''
    fallback = (_ascii(stem) or 'download')[:120]
    if _ascii(extension):
        fallback = f'{fallback}.{_ascii(extension)[:16]}'
    kind = 'inline' if inline else 'attachment'
    return f'{kind}; filename="{fallback}"; filename*=UTF-8\'\'{quote(name, safe="")}'


def content_headers(*, media_type: str, size: int, sha256: str, name: str, inline: bool) -> dict[str, str]:
    return {
        'Content-Type': media_type,
        'Content-Length': str(size),
        'ETag': etag_for(sha256),
        'Cache-Control': 'private, no-cache',
        'Content-Disposition': content_disposition(inline, name),
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; sandbox",
        'Referrer-Policy': 'no-referrer',
    }


def not_modified_headers(sha256: str) -> dict[str, str]:
    return {'ETag': etag_for(sha256), 'Cache-Control': 'private, no-cache'}


def too_large(limit: int) -> AssetTooLargeError:
    return AssetTooLargeError('REQUEST_TOO_LARGE', f'上传请求超过 {limit // (1024 * 1024)} MiB 限制')
