from __future__ import annotations

import pytest

from module_admin.entity.vo.dict_vo import DictDataPageQueryModel, DictTypePageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.dict_query_handlers import (
    GetDictDataByTypeQueryHandler,
    GetDictDataDetailQueryHandler,
    GetDictDataListQueryHandler,
    GetDictTypeDetailQueryHandler,
    GetDictTypeListQueryHandler,
    GetDictTypeOptionsQueryHandler,
)
from modules.system.application.queries import (
    GetDictDataByTypeQuery,
    GetDictDataDetailQuery,
    GetDictDataListQuery,
    GetDictTypeDetailQuery,
    GetDictTypeListQuery,
    GetDictTypeOptionsQuery,
)
from modules.system.application.read_models import (
    DictDataDetailReadModel,
    DictDataItemReadModel,
    DictDataPageReadModel,
    DictTypeDetailReadModel,
    DictTypeItemReadModel,
    DictTypePageReadModel,
)
from utils.page_util import PageResponseModel


class _DictTypeServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.detail_called_with = None

    async def get_dict_type_list_services(self, query, is_page=False):
        self.list_called_with = (query, is_page)
        if is_page:
            return PageResponseModel(
                items=[
                    {
                        'dictId': 1,
                        'dictName': '状态',
                        'dictType': 'sys_status',
                        'status': '0',
                    }
                ],
                page=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'dictId': 1,
                'dictName': '状态',
                'dictType': 'sys_status',
                'status': '0',
            }
        ]

    async def dict_type_detail_services(self, dict_id):
        self.detail_called_with = dict_id
        return {
            'dictId': dict_id,
            'dictName': '状态',
            'dictType': 'sys_status',
            'status': '0',
        }


class _DictDataServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.detail_called_with = None
        self.by_type_called_with = None

    async def get_dict_data_list_services(self, query, is_page=False):
        self.list_called_with = (query, is_page)
        if is_page:
            return PageResponseModel(
                items=[
                    {
                        'dictCode': 1,
                        'dictLabel': '正常',
                        'dictValue': '0',
                        'dictType': 'sys_status',
                        'status': '0',
                    }
                ],
                page=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'dictCode': 1,
                'dictLabel': '正常',
                'dictValue': '0',
                'dictType': 'sys_status',
                'status': '0',
            }
        ]

    async def dict_data_detail_services(self, dict_code):
        self.detail_called_with = dict_code
        return {
            'dictCode': dict_code,
            'dictLabel': '正常',
            'dictValue': '0',
            'dictType': 'sys_status',
            'status': '0',
        }

    async def query_dict_data_list_from_cache_services(self, redis_client, dict_type):
        self.by_type_called_with = (redis_client, dict_type)
        return [
            {
                'dictCode': 1,
                'dictLabel': '正常',
                'dictValue': '0',
                'dictType': dict_type,
                'status': '0',
            }
        ]


@pytest.mark.asyncio
async def test_dict_query_handlers_success() -> None:
    dict_type_service = _DictTypeServiceStub()
    dict_data_service = _DictDataServiceStub()

    type_list_handler = GetDictTypeListQueryHandler(dict_type_service)
    type_options_handler = GetDictTypeOptionsQueryHandler(dict_type_service)
    type_detail_handler = GetDictTypeDetailQueryHandler(dict_type_service)
    data_type_handler = GetDictDataByTypeQueryHandler(dict_data_service)
    data_list_handler = GetDictDataListQueryHandler(dict_data_service)
    data_detail_handler = GetDictDataDetailQueryHandler(dict_data_service)

    type_page_result = await type_list_handler.handle(
        GetDictTypeListQuery(
            query=DictTypePageQueryModel(page=1, pageSize=10),
            is_page=True,
            operator='admin',
        )
    )
    type_options_result = await type_options_handler.handle(GetDictTypeOptionsQuery(operator='admin'))
    type_detail_result = await type_detail_handler.handle(GetDictTypeDetailQuery(dict_id=1, operator='admin'))
    data_by_type_result = await data_type_handler.handle(
        GetDictDataByTypeQuery(dict_type='sys_status', redis_client=object(), operator='admin')
    )
    data_page_result = await data_list_handler.handle(
        GetDictDataListQuery(
            query=DictDataPageQueryModel(page=1, pageSize=10),
            is_page=True,
            operator='admin',
        )
    )
    data_detail_result = await data_detail_handler.handle(GetDictDataDetailQuery(dict_code=1, operator='admin'))

    assert isinstance(type_page_result, DictTypePageReadModel)
    assert isinstance(type_options_result[0], DictTypeItemReadModel)
    assert isinstance(type_detail_result, DictTypeDetailReadModel)
    assert isinstance(data_by_type_result[0], DictDataItemReadModel)
    assert isinstance(data_page_result, DictDataPageReadModel)
    assert isinstance(data_detail_result, DictDataDetailReadModel)
    assert type_page_result.items[0].dict_type == 'sys_status'
    assert data_page_result.items[0].dict_type == 'sys_status'


@pytest.mark.asyncio
async def test_dict_data_by_type_query_returns_empty_when_redis_missing() -> None:
    dict_data_service = _DictDataServiceStub()
    data_type_handler = GetDictDataByTypeQueryHandler(dict_data_service)

    data_by_type_result = await data_type_handler.handle(
        GetDictDataByTypeQuery(dict_type='sys_status', redis_client=None, operator='admin')
    )

    assert data_by_type_result == []
    assert dict_data_service.by_type_called_with is None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_dict_read_queries() -> None:
    dict_type_service = _DictTypeServiceStub()
    dict_data_service = _DictDataServiceStub()
    mediator = provide_system_mediator(dict_type_service=dict_type_service, dict_data_service=dict_data_service)

    type_page_result = await mediator.query(
        GetDictTypeListQuery(query=DictTypePageQueryModel(page=1, pageSize=10), is_page=True)
    )
    type_options_result = await mediator.query(GetDictTypeOptionsQuery())
    type_detail_result = await mediator.query(GetDictTypeDetailQuery(dict_id=1))
    data_by_type_result = await mediator.query(GetDictDataByTypeQuery(dict_type='sys_status', redis_client=object()))
    data_page_result = await mediator.query(
        GetDictDataListQuery(query=DictDataPageQueryModel(page=1, pageSize=10), is_page=True)
    )
    data_detail_result = await mediator.query(GetDictDataDetailQuery(dict_code=1))

    assert isinstance(type_page_result, DictTypePageReadModel)
    assert isinstance(type_options_result[0], DictTypeItemReadModel)
    assert isinstance(type_detail_result, DictTypeDetailReadModel)
    assert isinstance(data_by_type_result[0], DictDataItemReadModel)
    assert isinstance(data_page_result, DictDataPageReadModel)
    assert isinstance(data_detail_result, DictDataDetailReadModel)
    assert type_page_result.items[0].dict_type == 'sys_status'
    assert data_page_result.items[0].dict_type == 'sys_status'
