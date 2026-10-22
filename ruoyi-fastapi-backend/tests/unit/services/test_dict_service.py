"""
Unit tests for DictTypeService and DictDataService runtime paths.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from common.remark_document_v1 import plain_to_remark
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from exceptions.exception import ResourceNotFoundException
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.vo.dict_vo import DeleteDictTypeModel, DictDataModel, DictTypeModel
from modules.system.application.services import DictDataService, DictTypeService
from modules.system.infrastructure.dict_repository import DictDataRepository, DictTypeRepository


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
    @pytest.mark.parametrize(
        ('rename', 'has_items', 'initial_status', 'new_status'),
        [(True, True, '0', '0'), (True, False, '0', '0'), (False, True, '0', '1'), (False, True, '1', '0')],
    )
    async def test_edit_refreshes_type_membership_and_status_cache(
        self, test_db, rename, has_items, initial_status, new_status
    ):
        source_type = 'cache_type_source'
        target_type = 'cache_type_target'
        dict_type = DictTypeDO(dict_type=source_type, dict_name='原类型', status=initial_status)
        rows = []
        if has_items:
            rows = [
                DictDataDO(dict_type=source_type, dict_label='启用项', dict_value='active', status='0'),
                DictDataDO(dict_type=source_type, dict_label='停用项', dict_value='disabled', status='1'),
            ]
        test_db.add_all([dict_type, *rows])
        await test_db.flush()
        type_repo = DictTypeRepository(test_db)
        data_repo = DictDataRepository(test_db)
        data_service = DictDataService(type_repo, data_repo)
        service = DictTypeService(type_repo, data_repo, data_service)
        cache = {}
        redis = SimpleNamespace(
            get=AsyncMock(side_effect=cache.get),
            set=AsyncMock(side_effect=lambda key, payload: cache.__setitem__(key, payload)),
            delete=AsyncMock(side_effect=lambda *keys: [cache.pop(key, None) for key in keys]),
        )
        for name in (source_type, target_type):
            await data_service.query_dict_data_list_from_cache_services(redis, name)

        destination_type = target_type if rename else source_type
        result = await service.edit_dict_type_services(
            redis,
            DictTypeModel(
                dict_id=dict_type.dict_id, dict_type=destination_type, dict_name='更新类型', status=new_status
            ),
        )

        assert result.is_success
        if rename:
            assert await data_service.query_dict_data_list_from_cache_services(redis, source_type) == []
        choices = await data_service.query_dict_data_list_from_cache_services(redis, destination_type)
        assert {row['dictValue'] for row in choices} == ({'active'} if has_items and new_status == '0' else set())
        for row in rows:
            await test_db.refresh(row)
            assert row.dict_type == destination_type

    @pytest.mark.asyncio
    async def test_delete_empty_type_removes_its_old_cache(self, test_db):
        dict_type = DictTypeDO(dict_type='cache_type_deleted', dict_name='待删除类型', status='0')
        test_db.add(dict_type)
        await test_db.flush()
        type_repo = DictTypeRepository(test_db)
        data_repo = DictDataRepository(test_db)
        data_service = DictDataService(type_repo, data_repo)
        service = DictTypeService(type_repo, data_repo, data_service)
        key = f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type.dict_type}'
        cache = {key: json.dumps([{'dictValue': 'old'}]), 'sys_dict:unrelated': 'unchanged'}
        redis = SimpleNamespace(
            get=AsyncMock(side_effect=cache.get),
            set=AsyncMock(side_effect=lambda name, payload: cache.__setitem__(name, payload)),
            delete=AsyncMock(side_effect=lambda *keys: [cache.pop(name, None) for name in keys]),
        )

        result = await service.delete_dict_type_services(redis, DeleteDictTypeModel(dict_ids=str(dict_type.dict_id)))

        assert result.is_success
        assert key not in cache
        assert await data_service.query_dict_data_list_from_cache_services(redis, dict_type.dict_type) == []
        assert cache['sys_dict:unrelated'] == 'unchanged'

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
    async def test_dict_type_detail_raises_404_when_not_found(self):
        service, dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        dict_type_repo.find_by_id.return_value = None

        with pytest.raises(ResourceNotFoundException):
            await service.dict_type_detail_services(1)

    @pytest.mark.asyncio
    async def test_export_dict_type_list_maps_status(self, monkeypatch):
        captured = {}

        def fake_export(rows, mapping, *, text_columns):
            captured['rows'] = rows
            captured['mapping'] = mapping
            captured['text_columns'] = text_columns
            return b'dict-type-bytes'

        monkeypatch.setattr('modules.system.application.services.ExcelUtil.export_list2excel', fake_export)
        service, _dict_type_repo, _dict_data_repo, _dict_data_service = build_dict_type_service()
        rows = [
            {
                'dictType': 'sys_user_status',
                'status': '0',
                'remark': plain_to_remark('type note', identity_key='sys_dict_type:1:remark'),
            },
            {'dictType': 'sys_user_sex', 'status': '1', 'remark': None},
        ]

        data = await service.export_dict_type_list_services(rows)

        assert data == b'dict-type-bytes'
        assert captured['rows'][0]['status'] == '正常'
        assert captured['rows'][1]['status'] == '停用'
        assert 'dictType' in captured['mapping']
        assert captured['rows'][0]['remark'] == 'type note'
        assert captured['rows'][1]['remark'] == ''
        assert captured['text_columns'] == {'remark'}


class TestDictDataService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(('move_type', 'keep_old_item'), [(True, False), (True, True), (False, False)])
    async def test_edit_refreshes_each_affected_type_cache(self, test_db, move_type, keep_old_item):
        source_type = 'cache_edit_source'
        target_type = 'cache_edit_target'
        moved = DictDataDO(dict_type=source_type, dict_label='原标签', dict_value='moved', dict_sort=1, status='0')
        target_item = DictDataDO(
            dict_type=target_type, dict_label='目标已有项', dict_value='target', dict_sort=2, status='0'
        )
        rows = [
            DictTypeDO(dict_type=source_type, dict_name='原类型', status='0'),
            DictTypeDO(dict_type=target_type, dict_name='目标类型', status='0'),
            moved,
            target_item,
        ]
        if keep_old_item:
            rows.append(DictDataDO(dict_type=source_type, dict_label='原类型保留项', dict_value='kept', status='0'))
        test_db.add_all(rows)
        await test_db.flush()
        service = DictDataService(DictTypeRepository(test_db), DictDataRepository(test_db))
        cache = {}
        redis = SimpleNamespace(
            get=AsyncMock(side_effect=cache.get),
            set=AsyncMock(side_effect=lambda key, payload: cache.__setitem__(key, payload)),
        )
        for dict_type in (source_type, target_type):
            await service.query_dict_data_list_from_cache_services(redis, dict_type)
        redis.set.reset_mock()

        destination_type = target_type if move_type else source_type
        result = await service.edit_dict_data_services(
            redis,
            DictDataModel(
                dict_code=moved.dict_code,
                dict_type=destination_type,
                dict_label='更新标签',
                dict_value='moved',
                status='0',
            ),
        )

        assert result.is_success
        source = await service.query_dict_data_list_from_cache_services(redis, source_type)
        target = await service.query_dict_data_list_from_cache_services(redis, target_type)
        assert {row['dictValue'] for row in source} == (
            {'kept'} if keep_old_item else set() if move_type else {'moved'}
        )
        assert {row['dictValue'] for row in target} == ({'target', 'moved'} if move_type else {'target'})
        edited = target if move_type else source
        assert next(row for row in edited if row['dictValue'] == 'moved')['dictLabel'] == '更新标签'
        assert [call.args[0] for call in redis.set.await_args_list] == [
            f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}'
            for dict_type in dict.fromkeys((source_type, destination_type))
        ]

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
        payload = json.dumps(
            [{'dictLabel': '正常', 'dictValue': '0', 'remark': None, 'remarkText': ''}], ensure_ascii=False
        )
        redis = FakeRedis(payload)
        service, _dict_type_repo, _dict_data_repo = build_dict_data_service()
        loader = AsyncMock()
        monkeypatch.setattr(service, '_load_dict_data_and_refresh_cache', loader)

        result = await service.query_dict_data_list_from_cache_services(redis, 'sys_user_status')

        assert result[0]['dictLabel'] == '正常'
        assert result[0]['dictValue'] == '0'
        assert result[0]['remark'] is None
        assert result[0]['remarkText'] == ''
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

        def fake_export(rows, mapping, *, text_columns):
            captured['rows'] = rows
            captured['mapping'] = mapping
            captured['text_columns'] = text_columns
            return b'dict-data-bytes'

        monkeypatch.setattr('modules.system.application.services.ExcelUtil.export_list2excel', fake_export)
        service, _dict_type_repo, _dict_data_repo = build_dict_data_service()
        rows = [
            {
                'dictType': 'sys_user_status',
                'status': '0',
                'isDefault': 'Y',
                'remark': plain_to_remark('data note', identity_key='sys_dict_data:1:remark'),
            },
            {'dictType': 'sys_user_status', 'status': '1', 'isDefault': 'N', 'remark': None},
        ]

        data = await service.export_dict_data_list_services(rows)

        assert data == b'dict-data-bytes'
        assert captured['rows'][0]['status'] == '正常'
        assert captured['rows'][1]['status'] == '停用'
        assert captured['rows'][0]['isDefault'] == '是'
        assert captured['rows'][1]['isDefault'] == '否'
        assert 'isDefault' in captured['mapping']
        assert captured['rows'][0]['remark'] == 'data note'
        assert captured['rows'][1]['remark'] == ''
        assert captured['text_columns'] == {'remark'}
