from __future__ import annotations

import pytest

from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.config_query_handlers import (
    GetConfigDetailQueryHandler,
    GetConfigListQueryHandler,
    GetConfigValueByKeyQueryHandler,
)
from modules.system.application.queries import (
    GetConfigDetailQuery,
    GetConfigListQuery,
    GetConfigValueByKeyQuery,
)
from modules.system.application.read_models import (
    ConfigDetailReadModel,
    ConfigPageReadModel,
    ConfigValueReadModel,
)
from utils.page_util import PageResponseModel


class _ConfigServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.detail_called_with = None
        self.key_called_with = None

    async def get_config_list_services(self, query, is_page=False):
        self.list_called_with = (query, is_page)
        if is_page:
            return PageResponseModel(
                rows=[
                    {
                        'configId': 1,
                        'configName': '系统参数',
                        'configKey': 'sys.test.key',
                        'configValue': 'v1',
                        'configType': 'N',
                    }
                ],
                page_num=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'configId': 1,
                'configName': '系统参数',
                'configKey': 'sys.test.key',
                'configValue': 'v1',
                'configType': 'N',
            }
        ]

    async def config_detail_services(self, config_id):
        self.detail_called_with = config_id
        return ConfigModel(
            configId=config_id,
            configName='系统参数',
            configKey='sys.test.key',
            configValue='v1',
            configType='N',
        )

    async def query_config_list_from_cache_services(self, redis_client, config_key):
        self.key_called_with = (redis_client, config_key)
        return 'cached-value'


@pytest.mark.asyncio
async def test_config_query_handlers_success() -> None:
    config_service = _ConfigServiceStub()
    list_handler = GetConfigListQueryHandler(config_service)
    detail_handler = GetConfigDetailQueryHandler(config_service)
    key_handler = GetConfigValueByKeyQueryHandler(config_service)

    list_result = await list_handler.handle(
        GetConfigListQuery(
            query=ConfigPageQueryModel(pageNum=1, pageSize=10),
            is_page=True,
            operator='admin',
        )
    )
    detail_result = await detail_handler.handle(
        GetConfigDetailQuery(
            config_id=1,
            operator='admin',
        )
    )
    key_result = await key_handler.handle(
        GetConfigValueByKeyQuery(
            config_key='sys.test.key',
            redis_client=object(),
            operator='admin',
        )
    )

    assert isinstance(list_result, ConfigPageReadModel)
    assert list_result.total == 1
    assert list_result.rows[0].config_key == 'sys.test.key'
    assert isinstance(detail_result, ConfigDetailReadModel)
    assert detail_result.config_id == 1
    assert isinstance(key_result, ConfigValueReadModel)
    assert key_result.config_value == 'cached-value'
    assert config_service.list_called_with is not None
    assert config_service.detail_called_with == 1
    assert config_service.key_called_with is not None


@pytest.mark.asyncio
async def test_config_value_query_handler_returns_empty_when_redis_missing() -> None:
    config_service = _ConfigServiceStub()
    key_handler = GetConfigValueByKeyQueryHandler(config_service)

    key_result = await key_handler.handle(
        GetConfigValueByKeyQuery(
            config_key='sys.test.key',
            redis_client=None,
            operator='admin',
        )
    )

    assert key_result.config_value == ''
    assert config_service.key_called_with is None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_config_read_queries() -> None:
    config_service = _ConfigServiceStub()
    mediator = provide_system_mediator(config_service=config_service)

    list_result = await mediator.query(
        GetConfigListQuery(
            query=ConfigPageQueryModel(pageNum=1, pageSize=10),
            is_page=True,
        )
    )
    detail_result = await mediator.query(GetConfigDetailQuery(config_id=1))
    key_result = await mediator.query(
        GetConfigValueByKeyQuery(
            config_key='sys.test.key',
            redis_client=object(),
        )
    )

    assert isinstance(list_result, ConfigPageReadModel)
    assert isinstance(detail_result, ConfigDetailReadModel)
    assert isinstance(key_result, ConfigValueReadModel)
    assert list_result.rows[0].config_key == 'sys.test.key'
    assert detail_result.config_id == 1
    assert key_result.config_value == 'cached-value'
