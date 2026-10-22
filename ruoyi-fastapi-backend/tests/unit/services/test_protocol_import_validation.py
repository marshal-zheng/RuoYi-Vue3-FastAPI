"""Malformed protocol files are input failures and must never reach persistence."""

import io
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from openpyxl import Workbook

from config.error_codes import ErrorCode
from exceptions.exception import ValidationException
from module_admin.service.protocol_service import ProtocolService


def workbook_bytes():
    workbook = Workbook()
    workbook.active.title = '字段列表'
    workbook.active.append(['信息名称', '字节数', '数据类型'])
    workbook.active.append(['Temperature', 2, 'UINT16'])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
@pytest.mark.parametrize('entrypoint', ['preview', 'import'])
@pytest.mark.parametrize(
    ('filename', 'contents'),
    [
        ('empty.xlsx', b''),
        ('renamed.xlsx', b'not a workbook'),
        ('truncated.xlsx', workbook_bytes()[:120]),
        ('unsupported.txt', b'contents'),
        ('invalid.json', b'{'),
        ('root.json', b'[]'),
        ('fields.json', b'{"fields": [1]}'),
    ],
    ids=['empty', 'renamed-text', 'truncated-zip', 'unsupported', 'invalid-json', 'array-root', 'invalid-fields'],
)
async def test_invalid_file_is_422_before_repository_access(entrypoint, filename, contents):
    repository = SimpleNamespace(find_by_name=AsyncMock(), add=AsyncMock())
    service = ProtocolService(protocol_repo=repository)
    upload = UploadFile(io.BytesIO(contents), filename=filename)
    try:
        with pytest.raises(ValidationException) as failure:
            if entrypoint == 'preview':
                await service.protocol_import_preview_services(upload)
            else:
                await service.import_protocol_services(upload, None, 'operator')
        assert failure.value.http_status == 422
        assert failure.value.error_code == ErrorCode.INVALID_INPUT
        repository.find_by_name.assert_not_awaited()
        repository.add.assert_not_awaited()
    finally:
        await upload.close()


@pytest.mark.asyncio
async def test_valid_workbook_still_previews_real_fields():
    service = ProtocolService(protocol_repo=SimpleNamespace())
    upload = UploadFile(io.BytesIO(workbook_bytes()), filename='valid.xlsx')
    try:
        result = await service.protocol_import_preview_services(upload)
        assert result['fields'][0]['fieldName'] == 'Temperature'
        assert result['fields'][0]['byteCount'] == 2
    finally:
        await upload.close()
