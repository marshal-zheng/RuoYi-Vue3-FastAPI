"""Only the affected dictionary cache key is rebuilt from authoritative JSON records."""

import json
from unittest.mock import AsyncMock

import pytest

from common.remark_document_v1 import plain_to_remark
from modules.system.application.services.dict_data_service import DictDataService


@pytest.mark.parametrize(
    'cached',
    [
        'broken-json',
        json.dumps([{'remark': 'legacy'}]),
        json.dumps([{'remark': {'bad': True}, 'remarkText': 'forged'}]),
    ],
)
async def test_bad_dictionary_cache_rebuilds_one_key_and_preserves_document(cached):
    doc = plain_to_remark('中文😀', identity_key='sys_dict_data:7:remark')
    repository = AsyncMock()
    repository.find_by_type.return_value = [
        {'dictCode': 7, 'dictType': 'one', 'dictLabel': 'Label', 'dictValue': 'value', 'remark': doc, 'status': '0'}
    ]
    redis = AsyncMock()
    redis.get.return_value = cached
    service = DictDataService(AsyncMock(), repository)
    result = await service.query_dict_data_list_from_cache_services(redis, 'one')
    assert result[0]['remark'] == doc
    assert result[0]['remarkText'] == '中文😀'
    assert result[0]['dictLabel'] == 'Label'
    assert result[0]['dictValue'] == 'value'
    redis.delete.assert_awaited_once_with('sys_dict:one')
    key, payload = redis.set.await_args.args
    assert key == 'sys_dict:one'
    assert json.loads(payload) == result
    repository.find_by_type.assert_awaited_once_with('one')
