"""Bounded Office container and macro checks (OOXML via zipfile/defusedxml, OLE via olefile/oletools).

These checks reject corrupt, disguised, macro-bearing and unverifiable encrypted documents. They are
not antivirus scanning and do not prove a document harmless. Every unsupported structure, parser
exception or exceeded budget fails closed. Nothing is executed, emulated, deobfuscated or decrypted.
"""

from __future__ import annotations

import io
import logging
import posixpath
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import msoffcrypto
import olefile
from defusedxml import ElementTree as SafeElementTree
from oletools import ppt_parser
from oletools.olevba import VBA_Parser
from oletools.thirdparty.oledump.plugin_biff import cBIFF

from modules.file_assets.domain.errors import AssetInvalidError, AssetTooLargeError, AssetUnsupportedTypeError
from modules.file_assets.domain.types import MIB, FileTypeSpec

if TYPE_CHECKING:
    from modules.file_assets.application.validation.common import Deadline

for _name in ('olevba', 'ppt', 'crypto', 'olefile', 'msoffcrypto', 'oletools'):
    # Parser diagnostics may quote document bytes or macro source; keep them out of application logs.
    _logger = logging.getLogger(_name)
    _logger.setLevel(logging.CRITICAL + 1)
    _logger.propagate = False

OOXML_MAX_ENTRIES = 2048
OOXML_MAX_TOTAL_BYTES = 200 * MIB
OOXML_MAX_XML_BYTES = 1 * MIB
OLE_MAX_BYTES = 20 * MIB
EMBEDDED_MAX_DEPTH = 2
_READ_CHUNK = 256 * 1024
_ZIP_MAGIC = b'PK\x03\x04'

_MACRO_MAIN_TYPES = frozenset(
    {
        'application/vnd.ms-word.document.macroenabled.main+xml',
        'application/vnd.ms-word.template.macroenabledtemplate.main+xml',
        'application/vnd.ms-excel.sheet.macroenabled.main+xml',
        'application/vnd.ms-excel.template.macroenabled.main+xml',
        'application/vnd.ms-excel.addin.macroenabled.main+xml',
        'application/vnd.ms-excel.sheet.binary.macroenabled.main',
        'application/vnd.ms-powerpoint.presentation.macroenabled.main+xml',
        'application/vnd.ms-powerpoint.slideshow.macroenabled.main+xml',
        'application/vnd.ms-powerpoint.template.macroenabled.main+xml',
        'application/vnd.ms-powerpoint.addin.macroenabled.main+xml',
    }
)
_MACRO_PART_TYPES = frozenset(
    {
        'application/vnd.ms-office.vbaproject',
        'application/vnd.ms-office.vbaprojectsignature',
        'application/vnd.ms-word.vbadata+xml',
        'application/vnd.ms-excel.macrosheet+xml',
        'application/vnd.ms-excel.intlmacrosheet+xml',
    }
)
_MACRO_RELATIONSHIP_MARKERS = ('vbaproject', 'macrosheet', 'intlmacrosheet', 'vbadata')
_OFFICE_DOCUMENT_REL_SUFFIX = '/officedocument'
_OLE_SUBTYPE_STREAMS = {'doc': ('WordDocument',), 'xls': ('Workbook', 'Book'), 'ppt': ('PowerPoint Document',)}
_ENCRYPTION_STREAMS = ('EncryptedPackage', 'EncryptionInfo')
_OFFICE_MAIN_STREAMS = frozenset(stream for streams in _OLE_SUBTYPE_STREAMS.values() for stream in streams)


def _macro(reason: str = 'MACRO_DETECTED') -> AssetInvalidError:
    return AssetInvalidError(reason, '文件包含宏或宏结构，不允许上传')


def _unverifiable(reason: str) -> AssetInvalidError:
    return AssetInvalidError(reason, '文件已加密或结构无法完成必要校验')


def _corrupt() -> AssetInvalidError:
    return AssetInvalidError('OFFICE_CORRUPT', 'Office 文件已损坏或结构无效')


# ---------------------------------------------------------------- OOXML ---------


def _safe_entry_name(name: str) -> str:
    normalized = name.replace('\\', '/')
    parts = PurePosixPath(normalized).parts
    absolute = normalized.startswith('/') or bool(parts and ':' in parts[0])
    if absolute or '..' in parts:
        raise AssetInvalidError('ARCHIVE_UNSAFE_PATH', '压缩结构包含不安全路径')
    return normalized


def _parse_xml(data: bytes):
    try:
        # defusedxml forbids DTDs, entity expansion and external resources.
        return SafeElementTree.fromstring(data, forbid_dtd=True)
    except Exception:
        raise AssetInvalidError('OFFICE_CORRUPT', 'Office 包元数据无法解析') from None


def _local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


class _OoxmlScan:
    """One bounded pass over every entry: CRC verified, sizes counted, small parts retained."""

    def __init__(self, archive: zipfile.ZipFile, deadline: Deadline, depth: int, budget: list[int]):
        self.archive = archive
        self.deadline = deadline
        self.depth = depth
        self.budget = budget  # shared remaining-decompressed-bytes counter across nesting
        self.metadata: dict[str, bytes] = {}
        self.embedded: list[str] = []

    def run(self) -> None:
        infos = self.archive.infolist()
        if len(infos) > OOXML_MAX_ENTRIES:
            raise AssetTooLargeError('ARCHIVE_TOO_MANY_ENTRIES', 'Office 文件包含的条目过多')
        if sum(info.file_size for info in infos) > OOXML_MAX_TOTAL_BYTES:
            raise AssetTooLargeError('ARCHIVE_TOO_LARGE', 'Office 文件解压后过大')
        seen: set[str] = set()
        for info in infos:
            self.deadline.check()
            name = _safe_entry_name(info.filename)
            folded = name.casefold()
            if folded in seen:
                raise AssetInvalidError('ARCHIVE_DUPLICATE_ENTRY', '压缩结构包含重复条目')
            seen.add(folded)
            if info.flag_bits & 0x1:
                raise _unverifiable('ENCRYPTED_UNVERIFIABLE')
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise AssetInvalidError('ARCHIVE_UNSUPPORTED_COMPRESSION', 'Office 文件使用了不支持的压缩方式')
            if name.endswith('/'):
                continue
            self._read_entry(info, name)

    def _read_entry(self, info: zipfile.ZipInfo, name: str) -> None:
        keep = name == '[Content_Types].xml' or name.lower().endswith('.rels')
        retained = bytearray()
        head = b''
        try:
            with self.archive.open(info) as handle:
                while chunk := handle.read(_READ_CHUNK):
                    self.budget[0] -= len(chunk)
                    if self.budget[0] < 0:
                        raise AssetTooLargeError('ARCHIVE_TOO_LARGE', 'Office 文件解压后过大')
                    if len(head) < 8:
                        head = (head + chunk)[:8]
                    if keep:
                        retained.extend(chunk)
                        if len(retained) > OOXML_MAX_XML_BYTES:
                            raise AssetTooLargeError('XML_PART_TOO_LARGE', 'Office 包元数据过大')
                    self.deadline.check()
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, ValueError, NotImplementedError):
            # CRC mismatch, truncated stream or invalid compression data.
            raise _corrupt() from None
        except RuntimeError:
            raise _unverifiable('ENCRYPTED_UNVERIFIABLE') from None
        if keep:
            self.metadata[name] = bytes(retained)
        if head.startswith(olefile.MAGIC) or head.startswith(_ZIP_MAGIC):
            self.embedded.append(name)


def _content_types(scan: _OoxmlScan) -> tuple[dict[str, str], dict[str, str]]:
    raw = scan.metadata.get('[Content_Types].xml')
    if raw is None:
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容不是 Office 文档')
    root = _parse_xml(raw)
    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    for element in root:
        kind = _local(element.tag)
        content_type = (element.get('ContentType') or '').strip().lower()
        if kind == 'Default':
            defaults[(element.get('Extension') or '').lower()] = content_type
        elif kind == 'Override':
            overrides[(element.get('PartName') or '').lower()] = content_type
    return defaults, overrides


def _check_macro_markers(scan: _OoxmlScan, defaults: dict[str, str], overrides: dict[str, str]) -> None:
    for content_type in (*defaults.values(), *overrides.values()):
        if content_type in _MACRO_PART_TYPES or content_type in _MACRO_MAIN_TYPES:
            raise _macro()
    for info in scan.archive.infolist():
        lowered = info.filename.replace('\\', '/').lower()
        base = posixpath.basename(lowered)
        if base.startswith('vbaproject') or base.startswith('vbadata') or '/macrosheets/' in f'/{lowered}':
            raise _macro()
    for name, raw in scan.metadata.items():
        if not name.lower().endswith('.rels'):
            continue
        for relationship in _parse_xml(raw):
            rel_type = (relationship.get('Type') or '').lower()
            if any(marker in rel_type for marker in _MACRO_RELATIONSHIP_MARKERS):
                raise _macro()


def _main_part(scan: _OoxmlScan) -> str:
    raw = scan.metadata.get('_rels/.rels')
    if raw is None:
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容不是 Office 文档')
    for relationship in _parse_xml(raw):
        if (relationship.get('Type') or '').lower().endswith(_OFFICE_DOCUMENT_REL_SUFFIX):
            if (relationship.get('TargetMode') or '').lower() == 'external':
                break
            target = (relationship.get('Target') or '').replace('\\', '/')
            return '/' + posixpath.normpath(target.lstrip('/'))
    raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容不是 Office 文档')


def _scan_ooxml(
    archive: zipfile.ZipFile, deadline: Deadline, depth: int, budget: list[int]
) -> tuple[_OoxmlScan, dict[str, str], dict[str, str]]:
    scan = _OoxmlScan(archive, deadline, depth, budget)
    scan.run()
    defaults, overrides = _content_types(scan)
    _check_macro_markers(scan, defaults, overrides)
    for name in scan.embedded:
        if depth >= EMBEDDED_MAX_DEPTH:
            raise _unverifiable('EMBEDDED_TOO_DEEP')
        info = archive.getinfo(name)
        if info.file_size > OLE_MAX_BYTES:
            raise _unverifiable('EMBEDDED_TOO_LARGE')
        with archive.open(info) as handle:
            data = handle.read(OLE_MAX_BYTES + 1)
        _check_embedded(data, deadline, depth + 1, budget)
    return scan, defaults, overrides


def check_ooxml(path: Path, spec: FileTypeSpec, deadline: Deadline) -> None:
    if not zipfile.is_zipfile(path):
        if olefile.isOleFile(str(path)):
            with olefile.OleFileIO(str(path)) as ole:
                if any(ole.exists(stream) for stream in _ENCRYPTION_STREAMS):
                    raise _unverifiable('ENCRYPTED_UNVERIFIABLE')
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容与扩展名不符')
    budget = [OOXML_MAX_TOTAL_BYTES]
    try:
        with zipfile.ZipFile(path) as archive:
            scan, defaults, overrides = _scan_ooxml(archive, deadline, 0, budget)
            main = _main_part(scan)
            main_type = overrides.get(main.lower()) or defaults.get(posixpath.splitext(main)[1][1:].lower(), '')
    except zipfile.BadZipFile:
        raise _corrupt() from None
    if main_type in _MACRO_MAIN_TYPES:
        raise _macro()
    if main_type != spec.marker:
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容与扩展名不符')


# ------------------------------------------------------------------ OLE ---------


def _open_ole(data: bytes) -> olefile.OleFileIO:
    try:
        return olefile.OleFileIO(data, raise_defects=olefile.DEFECT_INCORRECT)
    except Exception:
        raise _corrupt() from None


def _root_streams(ole: olefile.OleFileIO) -> set[str]:
    return {entry[0] for entry in ole.listdir(streams=True, storages=False) if len(entry) == 1}


def _check_encryption(ole: olefile.OleFileIO, data: bytes, roots: set[str]) -> None:
    if any(ole.exists(stream) for stream in _ENCRYPTION_STREAMS):
        raise _unverifiable('ENCRYPTED_UNVERIFIABLE')
    if not roots & _OFFICE_MAIN_STREAMS:
        # Generic embedded OLE objects (e.g. Ole10Native packages) have no Office encryption header.
        return
    try:
        encrypted = msoffcrypto.OfficeFile(io.BytesIO(data)).is_encrypted()
    except Exception:
        # Unknown structure: encryption cannot be ruled out, so the file is unverifiable.
        raise _unverifiable('OFFICE_VALIDATION_FAILED') from None
    if encrypted:
        raise _unverifiable('ENCRYPTED_UNVERIFIABLE')


def _check_vba(data: bytes) -> None:
    try:
        parser = VBA_Parser('upload', data=data, relaxed=False)
        try:
            # VBA projects only: XLM detection is a separate structural check, never emulation.
            found = parser.detect_vba_macros()
        finally:
            parser.close()
    except Exception:
        raise AssetInvalidError('OFFICE_VALIDATION_FAILED', 'Office 文件无法完成宏检测') from None
    if found:
        raise _macro()


def _check_biff_macro_sheets(ole: olefile.OleFileIO) -> None:
    for stream in ('Workbook', 'Book'):
        if not ole.exists(stream):
            continue
        data = ole.openstream(stream).read()
        try:
            # Structural BOUNDSHEET listing: sheet type 1 = Excel 4.0 macro sheet, 6 = VB module.
            output = '\n'.join(cBIFF(name=[stream], stream=data, options='-o BOUNDSHEET').Analyze())
        except Exception:
            raise AssetInvalidError('OFFICE_VALIDATION_FAILED', 'Excel 文件无法完成宏检测') from None
        if 'Excel 4.0 macro sheet' in output or 'Visual Basic module' in output:
            raise _macro('XLM_MACRO_DETECTED')


def _check_embedded_streams(ole: olefile.OleFileIO, deadline: Deadline, depth: int, budget: list[int]) -> None:
    """Embedded OOXML packages (e.g. ObjectPool/*/Package) get the same macro scan."""
    for entry in ole.listdir(streams=True, storages=False):
        deadline.check()
        if ole.get_size(entry) < len(_ZIP_MAGIC):
            continue
        with ole.openstream(entry) as handle:
            head = handle.read(len(_ZIP_MAGIC))
        if head != _ZIP_MAGIC:
            continue
        if depth >= EMBEDDED_MAX_DEPTH:
            raise _unverifiable('EMBEDDED_TOO_DEEP')
        _check_embedded(ole.openstream(entry).read(), deadline, depth + 1, budget)


def _bounded_inflate(data: bytes, limit: int) -> bytes:
    decompressor = zlib.decompressobj()
    try:
        output = decompressor.decompress(data, limit + 1)
    except zlib.error:
        raise _corrupt() from None
    if len(output) > limit or decompressor.unconsumed_tail:
        raise _unverifiable('EMBEDDED_TOO_LARGE')
    return output


def _check_ppt(ole: olefile.OleFileIO, deadline: Deadline, depth: int, budget: list[int]) -> None:
    """PowerPoint VBA lives in compressed ExOleObjStg records; oletools inflates those without a bound,
    so detection uses the VBAInfo flag and inflates embedded storages here with an explicit limit."""
    try:
        parser = ppt_parser.PptParser(ole, fast_fail=True)
        infos = list(parser.search_vba_info())
        storages = list(parser.search_vba_storage())
    except Exception:
        raise AssetInvalidError('OFFICE_VALIDATION_FAILED', 'PowerPoint 文件无法完成宏检测') from None
    if any(container.vba_info_atom.f_has_macros for container in infos):
        raise _macro()
    if not storages:
        return
    if depth >= EMBEDDED_MAX_DEPTH:
        raise _unverifiable('EMBEDDED_TOO_DEEP')
    with ole.openstream(ppt_parser.MAIN_STREAM_NAME) as stream:
        for storage in storages:
            deadline.check()
            stream.seek(storage.data_offset)
            raw = stream.read(storage.data_size)
            data = _bounded_inflate(raw, OLE_MAX_BYTES) if storage.is_compressed else raw
            if data.startswith(olefile.MAGIC):
                _check_embedded(data, deadline, depth + 1, budget)


def _check_ole_bytes(data: bytes, deadline: Deadline, depth: int, budget: list[int], expected: str | None) -> None:
    if len(data) > OLE_MAX_BYTES:
        raise AssetTooLargeError('OFFICE_TOO_LARGE', 'Office 文件过大')
    with _open_ole(data) as ole:
        roots = _root_streams(ole)
        _check_encryption(ole, data, roots)
        is_ppt = 'PowerPoint Document' in roots
        if expected is not None:
            markers = _OLE_SUBTYPE_STREAMS[expected]
            if not any(marker in roots for marker in markers) or (expected != 'ppt' and is_ppt):
                raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容与扩展名不符')
        deadline.check()
        if is_ppt:
            _check_ppt(ole, deadline, depth, budget)
        else:
            _check_vba(data)
        if 'Workbook' in roots or 'Book' in roots:
            _check_biff_macro_sheets(ole)
        deadline.check()
        _check_embedded_streams(ole, deadline, depth, budget)


def _check_embedded(data: bytes, deadline: Deadline, depth: int, budget: list[int]) -> None:
    if data.startswith(olefile.MAGIC):
        _check_ole_bytes(data, deadline, depth, budget, expected=None)
        return
    if data.startswith(_ZIP_MAGIC):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                _scan_ooxml(archive, deadline, depth, budget)
        except zipfile.BadZipFile:
            raise _corrupt() from None


def check_ole(path: Path, spec: FileTypeSpec, deadline: Deadline) -> None:
    size = path.stat().st_size
    if size > OLE_MAX_BYTES:
        raise AssetTooLargeError('OFFICE_TOO_LARGE', 'Office 文件过大')
    data = path.read_bytes()
    if not data.startswith(olefile.MAGIC):
        if data.startswith(_ZIP_MAGIC):
            raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容与扩展名不符')
        raise AssetUnsupportedTypeError('CONTENT_TYPE_MISMATCH', '文件内容不是 Office 文档')
    _check_ole_bytes(data, deadline, 0, [OOXML_MAX_TOTAL_BYTES], expected=spec.type_id)
