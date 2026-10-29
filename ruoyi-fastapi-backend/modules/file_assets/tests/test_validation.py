"""Content validation: parser probes on real and synthesized samples (static parsing only)."""

from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageCms

from modules.file_assets.application.validation.common import Deadline, safe_display_name
from modules.file_assets.application.validation.documents import check_pdf, check_utf8_text
from modules.file_assets.application.validation.images import inspect_image, normalize_image
from modules.file_assets.application.validation.office import check_ole, check_ooxml
from modules.file_assets.application.validation.pipeline import precheck_upload, prepare_upload
from modules.file_assets.domain.errors import (
    AssetInvalidError,
    AssetTooLargeError,
    AssetUnsupportedTypeError,
    FileAssetError,
)
from modules.file_assets.domain.models import AssetKind, ImageProfile, PurposeSpec
from modules.file_assets.domain.types import FILE_TYPES, MIB, accept_attribute, validate_type_ids
from modules.file_assets.tests.conftest import png_bytes
from modules.system.application.file_asset_policies import USER_AVATAR
from scripts import export_file_asset_types

FIXTURES = Path(__file__).parent / 'fixtures' / 'office'

ATTACHMENTS = PurposeSpec(
    purpose='test.attachments',
    owner_type='test.owner',
    field_key='files',
    kind=AssetKind.FILE,
    allowed_type_ids=('doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt', 'csv', 'png'),
    max_bytes=20 * MIB,
    max_count=10,
)
IMAGES = PurposeSpec(
    purpose='test.images',
    owner_type='test.owner',
    field_key='images',
    kind=AssetKind.IMAGE,
    allowed_type_ids=('jpeg', 'png', 'webp'),
    max_bytes=5 * MIB,
    max_count=5,
    image_profile=ImageProfile.STANDARD,
)


def reason(callable_, *args, **kwargs) -> tuple[int, str]:
    with pytest.raises(FileAssetError) as info:
        callable_(*args, **kwargs)
    return info.value.http_status, info.value.reason


# ---------------------------------------------------------------- names / types ---


@pytest.mark.parametrize(
    ('name', 'expected'),
    [('报告.PDF', ('报告.PDF', '.pdf')), (' a.b.docx ', ('a.b.docx', '.docx'))],
)
def test_display_name_is_normalized(name, expected):
    assert safe_display_name(name) == expected


@pytest.mark.parametrize(
    'name', ['', '../etc/passwd.txt', 'a\\b.txt', 'evil\r\nX-Header: 1.txt', 'quote".txt', '.txt', 'noext']
)
def test_unsafe_or_extensionless_names_are_rejected(name):
    with pytest.raises(AssetInvalidError):
        safe_display_name(name)


def test_registry_subsets_and_accept_attribute_share_one_declaration():
    assert validate_type_ids(['PDF', 'pdf', 'docx']) == ('pdf', 'docx')
    assert accept_attribute(('jpeg', 'png')) == '.jpg,.jpeg,.png'
    with pytest.raises(ValueError):
        validate_type_ids([])
    with pytest.raises(ValueError):
        validate_type_ids(['exe'])
    with pytest.raises(ValueError):
        validate_type_ids(['pdf'], image_only=True)


@pytest.mark.parametrize(
    ('filename', 'declared', 'size', 'expected'),
    [
        ('a.zip', None, 10, (415, 'UNSUPPORTED_TYPE')),
        ('a.jpg', None, 10, (415, 'TYPE_NOT_ALLOWED')),
        ('a.pdf', 'application/msword', 10, (415, 'MIME_MISMATCH')),
        ('a.pdf', None, 0, (422, 'EMPTY_FILE')),
        ('a.pdf', None, 20 * MIB + 1, (413, 'FILE_TOO_LARGE')),
    ],
)
def test_precheck_rejects_before_any_row(filename, declared, size, expected):
    assert reason(precheck_upload, ATTACHMENTS, filename=filename, declared_type=declared, size=size) == expected


@pytest.mark.parametrize(
    'declared', [None, '', 'application/octet-stream', 'application/pdf; charset=binary', 'application/x-pdf']
)
def test_missing_generic_or_aliased_mime_is_accepted_for_content_check(declared):
    assert precheck_upload(ATTACHMENTS, filename='a.pdf', declared_type=declared, size=10).type_id == 'pdf'


def test_csv_accepts_the_windows_excel_alias_but_content_must_be_utf8_text(tmp_path):
    assert (
        precheck_upload(ATTACHMENTS, filename='x.csv', declared_type='application/vnd.ms-excel', size=5).type_id
        == 'csv'
    )
    source = tmp_path / 'x.csv'
    source.write_bytes('名称,值\n=1+1,2\n'.encode())
    prepared = prepare_upload(
        ATTACHMENTS,
        source,
        precheck_upload(ATTACHMENTS, filename='x.csv', declared_type=None, size=source.stat().st_size),
        workdir=tmp_path,
    )
    assert prepared.media_type == 'text/csv'
    assert prepared.path.read_bytes() == source.read_bytes()


def test_docx_accepts_zip_container_alias_but_not_plain_zip(tmp_path):
    assert precheck_upload(ATTACHMENTS, filename='x.docx', declared_type='application/zip', size=5).type_id == 'docx'
    plain = tmp_path / 'plain.docx'
    with zipfile.ZipFile(plain, 'w') as archive:
        archive.writestr('readme.txt', 'hello')
    assert reason(check_ooxml, plain, FILE_TYPES['docx'], Deadline(5))[0] == 415


# ----------------------------------------------------------------------- text/pdf ---


@pytest.mark.parametrize(
    ('data', 'expected'),
    [
        ('中文'.encode('gbk'), (422, 'TEXT_NOT_UTF8')),
        (b'abc\x00def', (415, 'TEXT_BINARY_CONTENT')),
        (b'\xe4\xb8', (422, 'TEXT_NOT_UTF8')),
    ],
)
def test_text_rejects_non_utf8_and_binary(tmp_path, data, expected):
    path = tmp_path / 'x.txt'
    path.write_bytes(data)
    assert reason(check_utf8_text, path) == expected


def test_text_accepts_utf8_with_bom(tmp_path):
    path = tmp_path / 'x.txt'
    path.write_bytes(b'\xef\xbb\xbf\xe4\xb8\xad\xe6\x96\x87\r\n\tok')
    check_utf8_text(path)


def test_pdf_structure(tmp_path):
    good = tmp_path / 'good.pdf'
    good.write_bytes(b'%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 1\ntrailer<<>>\nstartxref\n9\n%%EOF\n')
    check_pdf(good, good.stat().st_size)
    truncated = tmp_path / 'bad.pdf'
    truncated.write_bytes(b'%PDF-1.4\n1 0 obj<<>>endobj\n')
    assert reason(check_pdf, truncated, truncated.stat().st_size) == (422, 'PDF_CORRUPT')
    disguised = tmp_path / 'html.pdf'
    disguised.write_bytes(b'<html><script>alert(1)</script></html>%%EOF startxref')
    assert reason(check_pdf, disguised, disguised.stat().st_size)[0] == 415


# ------------------------------------------------------------------------ images ---


def _jpeg_with_metadata(size=(64, 48)) -> bytes:
    image = Image.new('RGB', size, (200, 30, 30))
    exif = image.getexif()
    exif[0x0112] = 6  # orientation: rotate 90 CW
    exif[0x010F] = 'SecretCam'
    exif[0x8825] = {2: (40.0, 1.0, 1.0)}  # GPS IFD pointer content (latitude)
    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', exif=exif, comment=b'private comment')
    data = buffer.getvalue()
    xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF/></x:xmpmeta>'
    app1 = b'\xff\xe1' + (len(xmp) + 31).to_bytes(2, 'big') + b'http://ns.adobe.com/xap/1.0/\x00' + xmp
    return data[:2] + app1 + data[2:]


def test_images_are_transposed_and_stripped_of_exif_xmp_gps_comments(tmp_path):
    source = tmp_path / 'photo.jpg'
    source.write_bytes(_jpeg_with_metadata())
    assert b'SecretCam' in source.read_bytes() and b'xmpmeta' in source.read_bytes()
    result = normalize_image(source, tmp_path / 'out', ImageProfile.STANDARD)
    stored = result.path.read_bytes()
    assert b'SecretCam' not in stored and b'xmpmeta' not in stored and b'private comment' not in stored
    with Image.open(result.path) as image:
        assert image.size == (48, 64)  # orientation applied to pixels
        assert dict(image.getexif()) == {}
        assert 'comment' not in image.info
    assert result.media_type == 'image/jpeg'


def test_icc_profile_is_kept(tmp_path):
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    source = tmp_path / 'icc.png'
    Image.new('RGB', (10, 10), 'blue').save(source, 'PNG', icc_profile=icc)
    result = normalize_image(source, tmp_path / 'out', ImageProfile.STANDARD)
    with Image.open(result.path) as image:
        assert image.info.get('icc_profile') == icc


def test_avatar_is_scaled_to_512_and_encoded_as_png(tmp_path):
    source = tmp_path / 'big.jpg'
    Image.new('RGB', (2000, 1000), 'green').save(source, 'JPEG')
    result = normalize_image(source, tmp_path / 'out', ImageProfile.AVATAR)
    with Image.open(result.path) as image:
        assert image.format == 'PNG' and max(image.size) == 512 and image.size == (512, 256)
    assert result.media_type == 'image/png'


def test_avatar_rename_keeps_display_name_consistent_with_png(tmp_path):
    source = tmp_path / 'source'
    Image.new('RGB', (20, 20), 'green').save(source, 'JPEG')
    precheck = precheck_upload(USER_AVATAR, filename='me.jpg', declared_type='image/jpeg', size=source.stat().st_size)
    prepared = prepare_upload(USER_AVATAR, source, precheck, workdir=tmp_path)
    assert prepared.display_name == 'me.png' and prepared.media_type == 'image/png'


def test_normalized_output_over_limit_degrades_then_rejects(tmp_path):
    source = tmp_path / 'noise.png'
    Image.frombytes('RGB', (2600, 2600), os.urandom(2600 * 2600 * 3)).save(source, 'PNG', compress_level=0)
    assert reason(normalize_image, source, tmp_path / 'out', ImageProfile.STANDARD) == (
        422,
        'IMAGE_NORMALIZED_TOO_LARGE',
    )


def test_large_photo_degrades_quality_instead_of_failing(tmp_path):
    # Calibrated texture: about 5.9 MiB at quality 90, about 4 MiB at quality 80.
    pixels = np.random.default_rng(1).integers(0, 112, size=(3200, 3200, 3), dtype=np.uint8)
    source = tmp_path / 'texture.jpg'
    Image.fromarray(pixels, 'RGB').save(source, 'JPEG', quality=97)
    result = normalize_image(source, tmp_path / 'out', ImageProfile.STANDARD)
    assert result.degraded and not result.downscaled
    assert result.path.stat().st_size <= 5 * MIB


@pytest.mark.parametrize(
    ('maker', 'expected'),
    [
        (lambda p: p.write_bytes(b'GIF89a' + b'\x00' * 20), (415, 'CONTENT_NOT_IMAGE')),
        (lambda p: p.write_bytes(png_bytes((64, 64), 'red')[:-40]), (422, 'IMAGE_CORRUPT')),
        (lambda p: p.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>'), (415, 'CONTENT_NOT_IMAGE')),
    ],
)
def test_corrupt_and_non_raster_images(tmp_path, maker, expected):
    path = tmp_path / 'x.png'
    maker(path)
    assert reason(inspect_image, path) == expected


def test_animated_webp_is_rejected(tmp_path):
    path = tmp_path / 'anim.webp'
    frames = [Image.new('RGB', (8, 8), color) for color in ('red', 'blue')]
    frames[0].save(path, 'WEBP', save_all=True, append_images=frames[1:], duration=100)
    assert reason(inspect_image, path) == (415, 'ANIMATED_IMAGE_UNSUPPORTED')


def test_pixel_bomb_header_is_rejected_before_decoding(tmp_path):
    path = tmp_path / 'bomb.png'
    Image.new('1', (9000, 9000)).save(path, 'PNG')  # tiny file, huge canvas
    assert path.stat().st_size < 200_000
    assert reason(inspect_image, path) == (422, 'IMAGE_DIMENSIONS_EXCEEDED')


def test_image_content_must_match_extension(tmp_path):
    source = tmp_path / 'source'
    Image.new('RGB', (4, 4)).save(source, 'JPEG')
    precheck = precheck_upload(IMAGES, filename='x.png', declared_type='image/png', size=source.stat().st_size)
    assert reason(prepare_upload, IMAGES, source, precheck, workdir=tmp_path) == (415, 'CONTENT_TYPE_MISMATCH')


def test_images_in_attachment_fields_keep_original_bytes(tmp_path):
    source = tmp_path / 'source'
    source.write_bytes(_jpeg_with_metadata())
    attachments = PurposeSpec(**{**ATTACHMENTS.__dict__, 'allowed_type_ids': ('jpeg',)})
    precheck = precheck_upload(attachments, filename='p.jpg', declared_type=None, size=source.stat().st_size)
    prepared = prepare_upload(attachments, source, precheck, workdir=tmp_path)
    assert prepared.path.read_bytes() == source.read_bytes() and prepared.normalized is None


# ------------------------------------------------------------------------ office ---

OFFICE_CASES = [
    ('msodde_harmless-clean.doc', 'doc', None),
    ('oleobj_embedded-simple-2007.doc', 'doc', None),
    ('oleobj_embedded-simple-2007.xls', 'xls', None),
    ('oleobj_embedded-simple-2007.ppt', 'ppt', None),
    ('msodde_harmless-clean.docx', 'docx', None),
    ('oleobj_embedded-simple-2007.docx', 'docx', None),
    ('oleobj_embedded-simple-2007.xlsx', 'xlsx', None),
    ('oleobj_embedded-simple-2007.pptx', 'pptx', None),
    ('olevba_sample_with_vba.ppt', 'ppt', 'MACRO_DETECTED'),
    ('decrypted-autostart.xls', 'xls', 'MACRO_DETECTED'),
    ('excel4-macros_excel4_sample_macro.xls', 'xls', 'XLM_MACRO_DETECTED'),
    ('oleform_oleform-PR314.docm', 'docx', 'MACRO_DETECTED'),
    ('msodde_harmless-clean.docm', 'docx', 'MACRO_DETECTED'),
    ('decrypted-autostart.xlsm', 'xlsx', 'MACRO_DETECTED'),
    ('excel4-macros_excel4_sample_macro.xlsm', 'xlsx', 'MACRO_DETECTED'),
    ('oleobj_embedded-simple-2007.xlsm', 'xlsx', 'MACRO_DETECTED'),
    ('encrypted_encrypted.doc', 'doc', 'ENCRYPTED_UNVERIFIABLE'),
    ('encrypted_encrypted.xls', 'xls', 'ENCRYPTED_UNVERIFIABLE'),
    ('encrypted_encrypted.ppt', 'ppt', 'ENCRYPTED_UNVERIFIABLE'),
    ('encrypted_encrypted.docx', 'docx', 'ENCRYPTED_UNVERIFIABLE'),
    ('encrypted_encrypted.xlsx', 'xlsx', 'ENCRYPTED_UNVERIFIABLE'),
    ('encrypted_encrypted.pptx', 'pptx', 'ENCRYPTED_UNVERIFIABLE'),
    ('msodde_harmless-clean.docx', 'xlsx', 'CONTENT_TYPE_MISMATCH'),
    ('msodde_harmless-clean.doc', 'xls', 'CONTENT_TYPE_MISMATCH'),
    ('msodde_harmless-clean.docx', 'doc', 'CONTENT_TYPE_MISMATCH'),
    ('oleobj_embedded-simple-2007.ppt', 'doc', 'CONTENT_TYPE_MISMATCH'),
]


@pytest.mark.parametrize(('sample', 'type_id', 'expected'), OFFICE_CASES)
def test_office_samples(sample, type_id, expected):
    spec = FILE_TYPES[type_id]
    check = check_ole if spec.family.value == 'ole' else check_ooxml
    if expected is None:
        check(FIXTURES / sample, spec, Deadline(5))
    else:
        assert reason(check, FIXTURES / sample, spec, Deadline(5))[1] == expected


def _docx(tmp_path: Path, extra: dict[str, bytes] | None = None, *, content_types: bytes | None = None) -> Path:
    source = FIXTURES / 'msodde_harmless-clean.docx'
    target = tmp_path / 'built.docx'
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for info in original.infolist():
            data = original.read(info)
            if info.filename == '[Content_Types].xml' and content_types is not None:
                data = content_types
            archive.writestr(info.filename, data)
        for name, data in (extra or {}).items():
            archive.writestr(name, data)
    return target


def test_ooxml_with_vba_part_is_rejected(tmp_path):
    path = _docx(tmp_path, {'word/vbaProject.bin': b'\xd0\xcf\x11\xe0junk'})
    assert reason(check_ooxml, path, FILE_TYPES['docx'], Deadline(5))[1] in {'MACRO_DETECTED', 'OFFICE_CORRUPT'}


def test_ooxml_with_macrosheet_relationship_is_rejected(tmp_path):
    rels = (
        b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="r9" Type="http://schemas.microsoft.com/office/2006/relationships/xlMacrosheet" '
        b'Target="macrosheets/sheet1.xml"/></Relationships>'
    )
    path = _docx(tmp_path, {'word/_rels/extra.xml.rels': rels})
    assert reason(check_ooxml, path, FILE_TYPES['docx'], Deadline(5))[1] == 'MACRO_DETECTED'


def test_ooxml_xml_entity_expansion_is_refused(tmp_path):
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE t [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">]>'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">&b;</Types>'
    )
    path = _docx(tmp_path, content_types=bomb)
    assert reason(check_ooxml, path, FILE_TYPES['docx'], Deadline(5)) == (422, 'OFFICE_CORRUPT')


def test_ooxml_entry_count_and_size_limits(tmp_path):
    many = tmp_path / 'many.docx'
    with zipfile.ZipFile(many, 'w') as archive:
        for index in range(2049):
            archive.writestr(f'f/{index}', b'')
    assert reason(check_ooxml, many, FILE_TYPES['docx'], Deadline(5)) == (413, 'ARCHIVE_TOO_MANY_ENTRIES')
    bomb = tmp_path / 'bomb.docx'
    with zipfile.ZipFile(bomb, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', b'<Types/>')
        archive.writestr('big.bin', b'\x00' * (201 * MIB))
    assert bomb.stat().st_size < 2 * MIB
    assert reason(check_ooxml, bomb, FILE_TYPES['docx'], Deadline(5)) == (413, 'ARCHIVE_TOO_LARGE')


def test_ooxml_crc_corruption_and_unsafe_paths(tmp_path):
    path = _docx(tmp_path)
    data = bytearray(path.read_bytes())
    offset = data.find(b'word/document.xml') + len(b'word/document.xml') + 40
    data[offset] ^= 0xFF
    corrupt = tmp_path / 'crc.docx'
    corrupt.write_bytes(bytes(data))
    assert reason(check_ooxml, corrupt, FILE_TYPES['docx'], Deadline(5))[0] == 422
    traversal = _docx(tmp_path / 'sub' if (tmp_path / 'sub').mkdir() is None else tmp_path, {'../evil.txt': b'x'})
    assert reason(check_ooxml, traversal, FILE_TYPES['docx'], Deadline(5)) == (422, 'ARCHIVE_UNSAFE_PATH')


def test_office_parse_deadline_fails_closed():
    deadline = Deadline(-1)
    assert reason(check_ooxml, FIXTURES / 'msodde_harmless-clean.docx', FILE_TYPES['docx'], deadline) == (
        422,
        'PARSE_TIMEOUT',
    )


def test_ole_size_limit(tmp_path):
    big = tmp_path / 'big.doc'
    big.write_bytes(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * (20 * MIB))
    assert reason(check_ole, big, FILE_TYPES['doc'], Deadline(5)) == (413, 'OFFICE_TOO_LARGE')


def test_parser_logs_never_reach_application_handlers():
    for name in ('olevba', 'ppt', 'crypto', 'olefile', 'msoffcrypto'):
        assert logging.getLogger(name).propagate is False


def test_full_pipeline_for_each_attachment_type(tmp_path):
    samples = {
        'doc': 'msodde_harmless-clean.doc',
        'docx': 'msodde_harmless-clean.docx',
        'xls': 'oleobj_embedded-simple-2007.xls',
        'xlsx': 'oleobj_embedded-simple-2007.xlsx',
        'ppt': 'oleobj_embedded-simple-2007.ppt',
        'pptx': 'oleobj_embedded-simple-2007.pptx',
    }
    for type_id, sample in samples.items():
        source = tmp_path / f'{type_id}.source'
        source.write_bytes((FIXTURES / sample).read_bytes())
        precheck = precheck_upload(
            ATTACHMENTS, filename=f'file.{type_id}', declared_type=None, size=source.stat().st_size
        )
        prepared = prepare_upload(ATTACHMENTS, source, precheck, workdir=tmp_path)
        assert prepared.media_type == FILE_TYPES[type_id].media_type
        assert prepared.path.read_bytes() == source.read_bytes()  # attachments keep original bytes


def test_too_large_error_is_413_type():
    assert AssetTooLargeError('X').http_status == 413
    assert AssetUnsupportedTypeError('X').http_status == 415


def test_frontend_type_registry_is_generated_from_backend_registry(capsys):
    """Frontend accept/hints read a generated artifact; any backend registry change must regenerate it."""

    assert export_file_asset_types.main(['--check']) == 0, capsys.readouterr().err
