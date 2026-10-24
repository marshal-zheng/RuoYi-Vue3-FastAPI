"""Query handlers for config operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.config_queries import (
    GetConfigDetailQuery,
    GetConfigListQuery,
    GetConfigValueByKeyQuery,
)
from modules.system.application.read_models.config_read_models import (
    ConfigDetailReadModel,
    ConfigListItemReadModel,
    ConfigPageReadModel,
    ConfigValueReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.config_service import ConfigService


def _to_config_list_item(raw: Any) -> ConfigListItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return ConfigListItemReadModel.model_validate(payload)


class GetConfigListQueryHandler(IQueryHandler[GetConfigListQuery, ConfigPageReadModel]):
    """Handle paged config list query."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: GetConfigListQuery) -> ConfigPageReadModel:
        list_result = await self._config_service.get_config_list_services(request.query, is_page=request.is_page)

        if request.is_page:
            items = [_to_config_list_item(row) for row in list_result.items]
            return ConfigPageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_config_list_item(row) for row in list_result]
        return ConfigPageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetConfigDetailQueryHandler(IQueryHandler[GetConfigDetailQuery, ConfigDetailReadModel]):
    """Handle config detail query."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: GetConfigDetailQuery) -> ConfigDetailReadModel:
        detail_result = await self._config_service.config_detail_services(request.config_id)
        return ConfigDetailReadModel.model_validate(detail_result.model_dump(by_alias=False))


class GetConfigValueByKeyQueryHandler(IQueryHandler[GetConfigValueByKeyQuery, ConfigValueReadModel]):
    """Handle config value lookup query."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: GetConfigValueByKeyQuery) -> ConfigValueReadModel:
        if request.redis_client is None:
            return ConfigValueReadModel(config_key=request.config_key, config_value='')

        config_value = await self._config_service.query_config_list_from_cache_services(
            request.redis_client,
            request.config_key,
        )
        return ConfigValueReadModel(
            config_key=request.config_key,
            config_value='' if config_value is None else str(config_value),
        )
