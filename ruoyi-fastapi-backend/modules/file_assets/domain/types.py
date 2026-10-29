"""Versioned registry of supported file types; fields select subsets, never free-form MIME."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

MIB = 1024 * 1024
GENERIC_MEDIA_TYPES = frozenset({'', 'application/octet-stream'})


class TypeFamily(StrEnum):
    IMAGE = 'image'
    OOXML = 'ooxml'
    OLE = 'ole'
    PDF = 'pdf'
    TEXT = 'text'


@dataclass(frozen=True)
class FileTypeSpec:
    type_id: str
    extensions: tuple[str, ...]
    media_type: str
    aliases: frozenset[str]
    family: TypeFamily
    # OOXML main part content type, or the OLE stream identifying the Office subtype.
    marker: str = ''

    def accepts_declared(self, declared: str) -> bool:
        return declared in GENERIC_MEDIA_TYPES or declared == self.media_type or declared in self.aliases


_OOXML_ZIP_ALIASES = frozenset({'application/zip', 'application/x-zip-compressed'})

FILE_TYPES: dict[str, FileTypeSpec] = {
    spec.type_id: spec
    for spec in (
        FileTypeSpec('doc', ('.doc',), 'application/msword', frozenset(), TypeFamily.OLE, marker='WordDocument'),
        FileTypeSpec(
            'xls',
            ('.xls',),
            'application/vnd.ms-excel',
            frozenset({'application/msexcel', 'application/x-msexcel'}),
            TypeFamily.OLE,
            marker='Workbook',
        ),
        FileTypeSpec(
            'ppt',
            ('.ppt',),
            'application/vnd.ms-powerpoint',
            frozenset({'application/mspowerpoint', 'application/x-mspowerpoint'}),
            TypeFamily.OLE,
            marker='PowerPoint Document',
        ),
        FileTypeSpec(
            'docx',
            ('.docx',),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            _OOXML_ZIP_ALIASES,
            TypeFamily.OOXML,
            marker='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
        ),
        FileTypeSpec(
            'xlsx',
            ('.xlsx',),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            _OOXML_ZIP_ALIASES,
            TypeFamily.OOXML,
            marker='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml',
        ),
        FileTypeSpec(
            'pptx',
            ('.pptx',),
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            _OOXML_ZIP_ALIASES,
            TypeFamily.OOXML,
            marker='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml',
        ),
        FileTypeSpec('pdf', ('.pdf',), 'application/pdf', frozenset({'application/x-pdf'}), TypeFamily.PDF),
        FileTypeSpec('txt', ('.txt',), 'text/plain', frozenset(), TypeFamily.TEXT),
        # Windows browsers commonly report CSV as the Excel MIME; content still has to be UTF-8 text.
        FileTypeSpec(
            'csv',
            ('.csv',),
            'text/csv',
            frozenset({'application/csv', 'text/x-csv', 'application/vnd.ms-excel'}),
            TypeFamily.TEXT,
        ),
        FileTypeSpec(
            'jpeg', ('.jpg', '.jpeg'), 'image/jpeg', frozenset({'image/jpg', 'image/pjpeg'}), TypeFamily.IMAGE
        ),
        FileTypeSpec('png', ('.png',), 'image/png', frozenset({'image/x-png'}), TypeFamily.IMAGE),
        FileTypeSpec('webp', ('.webp',), 'image/webp', frozenset(), TypeFamily.IMAGE),
    )
}

IMAGE_TYPE_IDS = ('jpeg', 'png', 'webp')
OFFICE_BASELINE_TYPE_IDS = ('doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'pdf')
_BY_EXTENSION = {extension: spec for spec in FILE_TYPES.values() for extension in spec.extensions}
_BY_MEDIA_TYPE = {spec.media_type: spec for spec in FILE_TYPES.values()}

# Upper bounds that every purpose and generated field must respect.
MAX_IMAGE_BYTES = 5 * MIB
MAX_ATTACHMENT_BYTES = 20 * MIB


def type_for_extension(extension: str) -> FileTypeSpec | None:
    return _BY_EXTENSION.get(extension.lower())


def type_for_media_type(media_type: str) -> FileTypeSpec | None:
    return _BY_MEDIA_TYPE.get(media_type)


def normalize_declared_media_type(value: str | None) -> str:
    return (value or '').split(';', 1)[0].strip().lower()


def validate_type_ids(type_ids: object, *, image_only: bool = False) -> tuple[str, ...]:
    """Validate a declared subset against the registry; raises ValueError on unknown or empty sets."""
    if not isinstance(type_ids, (list, tuple)) or not type_ids:
        raise ValueError('at least one registered file type must be selected')
    result: list[str] = []
    for item in type_ids:
        type_id = str(item).strip().lower()
        if type_id not in FILE_TYPES:
            raise ValueError(f'unknown file type id: {type_id}')
        if image_only and FILE_TYPES[type_id].family is not TypeFamily.IMAGE:
            raise ValueError(f'image fields only accept image types: {type_id}')
        if type_id not in result:
            result.append(type_id)
    return tuple(result)


def accept_attribute(type_ids: tuple[str, ...]) -> str:
    """The `accept` attribute the frontend derives from the same declaration."""
    return ','.join(extension for type_id in type_ids for extension in FILE_TYPES[type_id].extensions)
