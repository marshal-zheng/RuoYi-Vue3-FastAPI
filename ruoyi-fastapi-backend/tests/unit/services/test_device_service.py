import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from module_admin.entity.vo.device_vo import DeviceInterfaceModel, DeviceModel
from module_admin.service.device_service import DeviceService


@pytest.mark.asyncio
async def test_edit_device_uses_repositories_without_direct_flush(monkeypatch):
    query_db = AsyncMock()
    query_db.flush = AsyncMock()

    existing = type(
        'DeviceEntity',
        (),
        {
            'device_id': 1,
            'device_name': '旧设备',
            'device_category_id': None,
            'category_name': None,
            'device_type': None,
            'manufacturer': None,
            'model': None,
            'version': None,
            'bus_type': None,
            'remark': None,
            'update_by': None,
            'update_time': None,
        },
    )()

    fake_device_repo = type(
        'FakeDeviceRepo',
        (),
        {
            'get_by_id_with_interfaces': AsyncMock(return_value=existing),
            'update': AsyncMock(return_value=existing),
        },
    )()
    fake_interface_repo = type(
        'FakeDeviceInterfaceRepo',
        (),
        {
            'delete_by_device_id': AsyncMock(return_value=1),
            'add_all': AsyncMock(return_value=[]),
        },
    )()
    fake_category_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {
            'find_by_id': AsyncMock(return_value=None),
            'find_by_name': AsyncMock(return_value=None),
        },
    )()
    service = DeviceService(
        device_repo=fake_device_repo,
        interface_repo=fake_interface_repo,
        category_repo=fake_category_repo,
        query_db=query_db,
    )
    monkeypatch.setattr(service, '_resolve_category_info', AsyncMock(return_value=(2, '分类B')))

    payload = DeviceModel(
        deviceId=1,
        deviceName='新设备',
        interfaces=[DeviceInterfaceModel(interfaceName='if-1', interfaceType='CAN')],
    )
    result = await service.edit_device_services(payload, 'tester')

    assert result.is_success is True
    assert existing.device_name == '新设备'
    assert existing.device_category_id == 2
    fake_device_repo.update.assert_awaited_once_with(existing)
    fake_interface_repo.delete_by_device_id.assert_awaited_once_with(1)
    fake_interface_repo.add_all.assert_awaited_once()
    query_db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_single_device_uses_repository_commit(monkeypatch):
    query_db = AsyncMock()
    query_db.commit = AsyncMock()

    fake_device_repo = type(
        'FakeDeviceRepo',
        (),
        {
            'add': AsyncMock(return_value=SimpleNamespace(device_id=99)),
            'commit': AsyncMock(return_value=None),
            'find_by_name': AsyncMock(return_value=None),
        },
    )()
    fake_interface_repo = type(
        'FakeDeviceInterfaceRepo',
        (),
        {
            'delete_by_device_id': AsyncMock(return_value=0),
            'add_all': AsyncMock(return_value=[]),
            'find_by_device_id': AsyncMock(return_value=[]),
        },
    )()
    fake_category_repo = type(
        'FakeDeviceCategoryRepo',
        (),
        {
            'find_by_id': AsyncMock(return_value=None),
            'find_by_name': AsyncMock(return_value=None),
        },
    )()
    service = DeviceService(
        device_repo=fake_device_repo,
        interface_repo=fake_interface_repo,
        category_repo=fake_category_repo,
        query_db=query_db,
    )
    monkeypatch.setattr(service, '_resolve_category_info', AsyncMock(return_value=(1, '分类A')))
    monkeypatch.setattr(service, '_ensure_unique_device_name', AsyncMock(return_value='导入设备'))

    payload = json.dumps(
        {
            'device': {
                'deviceName': '导入设备',
                'interfaces': [
                    {
                        'interfaceName': 'eth0',
                        'interfaceType': 'LAN',
                    }
                ],
            }
        },
        ensure_ascii=False,
    )
    result = await service._import_single_device(payload, 'tester')

    assert result['deviceId'] == 99
    fake_device_repo.add.assert_awaited_once()
    fake_device_repo.commit.assert_awaited_once()
    query_db.commit.assert_not_awaited()
