"""One blocking pass from an uploaded temp file to the exact bytes that will be stored."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.file_assets.application.validation.common import Deadline, safe_display_name
from modules.file_assets.application.validation.documents import check_pdf, check_utf8_text
from modules.file_assets.application.validation.images import inspect_image, normalize_image
from modules.file_assets.application.validation.office import check_ole, check_ooxml
from modules.file_assets.domain.errors import AssetInvalidError, AssetTooLargeError, AssetUnsupportedTypeError
from modules.file_assets.domain.models import AssetKind, ImageProfile
from modules.file_assets.domain.types import (
    FILE_TYPES,
    TypeFamily,
    normalize_declared_media_type,
    type_for_extension,
)

if TYPE_CHECKING:
    from pathlib import Path

    from modules.file_assets.application.validation.images import NormalizedImage
    from modules.file_assets.domain.models import PurposeSpec

OFFICE_PARSE_SECONDS = 5.0
_HASH_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class PreparedFile:
    path: Path
    size: int
    sha256: str
    media_type: str
    type_id: str
    original_name: str
    display_name: str
    normalized: NormalizedImage | None = None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _with_extension(name: str, extension: str) -> str:
    stem = name.rsplit('.', 1)[0]
    return f'{stem}{extension}'[-255:]


@dataclass(frozen=True)
class UploadPrecheck:
    """Name, extension, purpose type set, declared MIME and size: decided before any row exists."""

    type_id: str
    original_name: str
    size: int


def precheck_upload(
    purpose: PurposeSpec, *, filename: str | None, declared_type: str | None, size: int
) -> UploadPrecheck:
    original_name, extension = safe_display_name(filename)
    spec = type_for_extension(extension)
    if spec is None:
        raise AssetUnsupportedTypeError('UNSUPPORTED_TYPE', '不支持的文件类型', field='file')
    if spec.type_id not in purpose.allowed_type_ids:
        raise AssetUnsupportedTypeError('TYPE_NOT_ALLOWED', '该字段不允许此类文件', field='file')
    if not spec.accepts_declared(normalize_declared_media_type(declared_type)):
        raise AssetUnsupportedTypeError('MIME_MISMATCH', '文件声明的类型与内容不符', field='file')
    if size == 0:
        raise AssetInvalidError('EMPTY_FILE', '不能上传空文件', field='file')
    if size > purpose.max_bytes:
        raise AssetTooLargeError('FILE_TOO_LARGE', '文件大小超出允许范围', field='file')
    return UploadPrecheck(type_id=spec.type_id, original_name=original_name, size=size)


def prepare_upload(
    purpose: PurposeSpec,
    source: Path,
    precheck: UploadPrecheck,
    *,
    workdir: Path,
    office_seconds: float = OFFICE_PARSE_SECONDS,
) -> PreparedFile:
    """Validate actual content against the prechecked type; images of image purposes are re-encoded."""
    spec = FILE_TYPES[precheck.type_id]
    original_name = precheck.original_name
    size = source.stat().st_size
    if size != precheck.size:
        raise AssetInvalidError('SIZE_MISMATCH', '上传内容不完整', field='file')

    normalized = None
    stored_path, media_type, type_id, display_name = source, spec.media_type, spec.type_id, original_name
    if spec.family is TypeFamily.IMAGE:
        inspection = inspect_image(source)
        if inspection.type_id != spec.type_id:
            raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '图片实际格式与扩展名不符', field='file')
        if purpose.kind is AssetKind.IMAGE:
            normalized = normalize_image(source, workdir / 'normalized', purpose.image_profile or ImageProfile.STANDARD)
            stored_path, media_type, type_id = normalized.path, normalized.media_type, normalized.type_id
            if type_id != spec.type_id:
                display_name = _with_extension(original_name, FILE_TYPES[type_id].extensions[0])
    elif spec.family is TypeFamily.OOXML:
        check_ooxml(source, spec, Deadline(office_seconds))
    elif spec.family is TypeFamily.OLE:
        check_ole(source, spec, Deadline(office_seconds))
    elif spec.family is TypeFamily.PDF:
        check_pdf(source, size)
    else:
        check_utf8_text(source)

    return PreparedFile(
        path=stored_path,
        size=stored_path.stat().st_size,
        sha256=sha256_of(stored_path),
        media_type=media_type,
        type_id=type_id,
        original_name=original_name,
        display_name=display_name,
        normalized=normalized,
    )
