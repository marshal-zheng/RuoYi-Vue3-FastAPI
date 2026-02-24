"""
Unit tests for DictTypeService and DictDataService runtime paths.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config.constant import CommonConstant
from module_admin.entity.vo.dict_vo import DictDataModel, DictTypeModel
from modules.system.application.services import DictDataService, DictTypeService


class FakeRedis:
    def __init__(self, payload=None):
        self._payload = payload
        self.get = AsyncMock(side_effect=self._get_impl)

    async def _get_impl(self, _key):
        return self._payload


def build_dict_type_service() -> tuple[DictTypeService, AsyncMock, AsyncMock, AsyncMock]:
    dict_type_repo = AsyncMock()
    dict_data_repo = AsyncMock()
    dict_data_service = AsyncMock()
    return (
        DictTypeService(
            dict_type_repo=dict_type_repo,
            dict_data_repo=dict_data_repo,
            dict_data_service=dict_data_service,
        ),
        dict_type_repo,
        dict_data_repo,
        dict_data_service,
    )


def build_dict_data_service() -> tuple[DictDataService, AsyncMock, AsyncMock]:
    dict_type_repo = AsyncMock()
    dict_data_repo = AsyncMock()
    return (
        DictDataService(
            dict_type_repo=dict_type_repo,
            dict_data_repo=dict_data_repo,
        ),
        dict_type_repo,
        dict_data_repo,
    )


class TestDictTypeService:
    @pytest.mark.asyncio
    async def test_check_dict_type_unique_not_unique(self):
        service, dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        dict_type_repo.find_by_type.return_value = SimpleNamespace(dict_id=2)
        page_object = DictTypeModel(dict_id=1, dict_type='sys_user_status')

        result = await service.check_dict_type_unique_services(page_object)

        assert result == CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_dict_type_unique_unique_when_missing(self):
        service, dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        dict_type_repo.find_by_type.return_value = None
        page_object = DictTypeModel(dict_id=1, dict_type='sys_user_status')

        result = await service.check_dict_type_unique_services(page_object)

        assert result == CommonConstant.UNIQUE

    @pytest.mark.asyncio
    async def test_dict_type_detail_returns_empty_model_when_not_found(self):
        service, dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        dict_type_repo.find_by_id.return_value = None

        result = await service.dict_type_detail_services(1)

        assert isinstance(result, DictTypeModel)
        assert result.dict_id is None

    @pytest.mark.asyncio
    async def test_export_dict_type_list_maps_status(self, monkeypatch):
        captured = {}

        def fake_export(rows, mapping):
            captured['rows'] = rows
            captured['mapping'] = mapping
            return b'dict-type-bytes'

        monkeypatch.setattr('modules.system.application.services.ExcelUtil.export_list2excel', fake_export)
        service, _dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        rows = [
            {'dictType': 'sys_user_status', 'status': '0'},
            {'dictType': 'sys_user_sex', 'status': '1'},
        ]

        data = await service.export_dict_type_list_services(rows)

        assert data == b'dict-type-bytes'
        assert captured['rows'][0]['status'] == '正常'
        assert captured['rows'][1]['status'] == '停用'
        assert 'dictType' in captured['mapping']


class TestDictDataService:
    @pytest.mark.asyncio
    async def test_check_dict_data_unique_not_unique(self):
        service, _dict_type_repo, dict_data_repo = build_dict_data_service()
        dict_data_repo.find_by_type_and_label.return_value = SimpleNamespace(dict_code=3)
        page_object = DictDataModel(dict_code=2, dict_type='sys_user_status', dict_label='正常')

        result = await service.check_dict_data_unique_services(page_object)

        assert result == CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_dict_data_unique_unique_when_missing(self):
        service, _dict_type_repo, dict_data_repo = build_dict_data_service()
        dict_data_repo.find_by_type_and_label.return_value = None
        page_object = DictDataModel(dict_code=2, dict_type='sys_user_status', dict_label='正常')

        result = await service.check_dict_data_unique_services(page_object)

        assert result == CommonConstant.UNIQUE

    @pytest.mark.asyncio
    async def test_query_dict_data_list_from_cache_hit(self, monkeypatch):
        payload = json.dumps([{'dictLabel': '正常', 'dictValue': '0'}], ensure_ascii=False)
        redis = FakeRedis(payload)
        service, _dict_type_repo, _dict_data_repo = build_dict_data_service()
        loader = AsyncMock()
        monkeypatch.setattr(service, '_load_dict_data_and_refresh_cache', loader)

        result = await service.query_dict_data_list_from_cache_services(redis, 'sys_user_status')

        assert result == [{'dictLabel': '正常', 'dictValue': '0'}]
        loader.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_dict_data_list_from_cache_miss_loads_and_refreshes(self, monkeypatch):
        redis = FakeRedis(None)
        service, _dict_type_repo, _dict_data_repo = build_dict_data_service()
        loader = AsyncMock(return_value=[{'dictLabel': '禁用', 'dictValue': '1'}])
        monkeypatch.setattr(service, '_load_dict_data_and_refresh_cache', loader)

        result = await service.query_dict_data_list_from_cache_services(redis, 'sys_user_status')

        assert result == [{'dictLabel': '禁用', 'dictValue': '1'}]
        loader.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_export_dict_data_list_maps_status_and_is_default(self, monkeypatch):
        captured = {}

        def fake_export(rows, mapping):
            captured['rows'] = rows
            captured['mapping'] = mapping
            return b'dict-data-bytes'

        monkeypatch.setattr('modules.system.application.services.ExcelUtil.export_list2excel', fake_export)
        service, _dict_type_repo, _dict_data_repo = build_dict_data_service()
        rows = [
            {'dictType': 'sys_user_status', 'status': '0', 'isDefault': 'Y'},
            {'dictType': 'sys_user_status', 'status': '1', 'isDefault': 'N'},
        ]

        data = await service.export_dict_data_list_services(rows)

        assert data == b'dict-data-bytes'
        assert captured['rows'][0]['status'] == '正常'
        assert captured['rows'][1]['status'] == '停用'
        assert captured['rows'][0]['isDefault'] == '是'
        assert captured['rows'][1]['isDefault'] == '否'
        assert 'isDefault' in captured['mapping']
