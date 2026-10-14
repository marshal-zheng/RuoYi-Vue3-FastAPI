from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from module_admin.entity.vo.device_category_vo import DeviceCategoryModel
from module_admin.service.device_category_service import DeviceCategoryService


@pytest.mark.asyncio
async def test_add_device_category_does_not_call_db_commit():
    query_db = AsyncMock()
    query_db.commit = AsyncMock()

    fake_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {
            'find_by_name': AsyncMock(return_value=None),
            'add': AsyncMock(return_value=SimpleNamespace(device_category_id=9)),
        },
    )()
    fake_device_repo = type('FakeDeviceRepo', (), {'count_by_category_ids': AsyncMock(return_value=0)})()
    service = DeviceCategoryService(
        category_repo=fake_repo,
        device_repo=fake_device_repo,
        query_db=query_db,
    )

    payload = DeviceCategoryModel(name='分类A')
    result = await service.add_device_category_services(payload, 'tester')

    assert result.is_success is True
    assert result.result == {'deviceCategoryId': 9}
    fake_repo.add.assert_awaited_once()
    query_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_device_category_uses_repository_update():
    query_db = AsyncMock()
    query_db.flush = AsyncMock()
    query_db.commit = AsyncMock()

    category = type(
        'DeviceCategoryEntity',
        (),
        {
            'device_category_id': 1,
            'name': '分类A',
            'descr': 'old',
            'status': '0',
            'remark': None,
            'update_by': None,
            'update_time': None,
        },
    )()

    fake_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {
            'find_by_id': AsyncMock(return_value=category),
            'find_by_name': AsyncMock(return_value=None),
            'update': AsyncMock(return_value=category),
        },
    )()
    fake_device_repo = type('FakeDeviceRepo', (), {'count_by_category_ids': AsyncMock(return_value=0)})()
    service = DeviceCategoryService(
        category_repo=fake_repo,
        device_repo=fake_device_repo,
        query_db=query_db,
    )

    payload = DeviceCategoryModel(deviceCategoryId=1, name='分类A-新', descr='new', status='0')
    result = await service.edit_device_category_services(payload, 'tester')

    assert result.is_success is True
    assert category.name == '分类A-新'
    assert category.descr == 'new'
    fake_repo.update.assert_awaited_once_with(category)
    query_db.flush.assert_not_awaited()
    query_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_device_category_does_not_call_db_commit():
    query_db = AsyncMock()
    query_db.commit = AsyncMock()

    fake_device_repo = type(
        'FakeDeviceRepo',
        (),
        {'count_by_category_ids': AsyncMock(return_value=0)},
    )()
    fake_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {'delete_by_ids': AsyncMock(return_value=2)},
    )()
    service = DeviceCategoryService(
        category_repo=fake_repo,
        device_repo=fake_device_repo,
        query_db=query_db,
    )

    result = await service.delete_device_category_services('1,2')

    assert result.is_success is True
    assert '2' in result.message
    fake_device_repo.count_by_category_ids.assert_awaited_once_with([1, 2])
    fake_repo.delete_by_ids.assert_awaited_once_with([1, 2])
    query_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_device_category_rejected_when_referenced():
    query_db = AsyncMock()
    query_db.commit = AsyncMock()

    fake_device_repo = type(
        'FakeDeviceRepo',
        (),
        {'count_by_category_ids': AsyncMock(return_value=3)},
    )()
    fake_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {'delete_by_ids': AsyncMock(return_value=0)},
    )()
    service = DeviceCategoryService(
        category_repo=fake_repo,
        device_repo=fake_device_repo,
        query_db=query_db,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_device_category_services('1,2')

    assert exc_info.value.status_code == 400
    assert '已被设备引用' in str(exc_info.value.detail)
    fake_repo.delete_by_ids.assert_not_awaited()
    query_db.commit.assert_not_awaited()
