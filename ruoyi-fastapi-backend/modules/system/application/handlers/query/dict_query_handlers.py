"""Query handlers for dictionary operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from module_admin.entity.vo.dict_vo import DictTypePageQueryModel
from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.dict_queries import (
    GetDictDataByTypeQuery,
    GetDictDataDetailQuery,
    GetDictDataListQuery,
    GetDictTypeDetailQuery,
    GetDictTypeListQuery,
    GetDictTypeOptionsQuery,
)
from modules.system.application.read_models.dict_read_models import (
    DictDataDetailReadModel,
    DictDataItemReadModel,
    DictDataPageReadModel,
    DictTypeDetailReadModel,
    DictTypeItemReadModel,
    DictTypePageReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services import DictDataService, DictTypeService


def _to_dict_type_item(raw: Any) -> DictTypeItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return DictTypeItemReadModel.model_validate(payload)


def _to_dict_data_item(raw: Any) -> DictDataItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return DictDataItemReadModel.model_validate(payload)


class GetDictTypeListQueryHandler(IQueryHandler[GetDictTypeListQuery, DictTypePageReadModel]):
    """Handle paged dictionary-type list query."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: GetDictTypeListQuery) -> DictTypePageReadModel:
        list_result = await self._dict_type_service.get_dict_type_list_services(request.query, is_page=request.is_page)

        if request.is_page:
            items = [_to_dict_type_item(row) for row in list_result.items]
            return DictTypePageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_dict_type_item(row) for row in list_result]
        return DictTypePageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetDictTypeOptionsQueryHandler(IQueryHandler[GetDictTypeOptionsQuery, list[DictTypeItemReadModel]]):
    """Handle dictionary-type options query."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: GetDictTypeOptionsQuery) -> list[DictTypeItemReadModel]:
        _ = request
        list_result = await self._dict_type_service.get_dict_type_list_services(
            DictTypePageQueryModel(),
            is_page=False,
        )
        return [_to_dict_type_item(row) for row in list_result]


class GetDictTypeDetailQueryHandler(IQueryHandler[GetDictTypeDetailQuery, DictTypeDetailReadModel]):
    """Handle dictionary-type detail query."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: GetDictTypeDetailQuery) -> DictTypeDetailReadModel:
        detail_result = await self._dict_type_service.dict_type_detail_services(request.dict_id)
        if detail_result is None:
            return DictTypeDetailReadModel()

        if hasattr(detail_result, 'model_dump'):
            payload = detail_result.model_dump(by_alias=False)
        elif isinstance(detail_result, dict):
            payload = detail_result
        else:
            payload = {}

        return DictTypeDetailReadModel.model_validate(payload)


class GetDictDataByTypeQueryHandler(IQueryHandler[GetDictDataByTypeQuery, list[DictDataItemReadModel]]):
    """Handle dictionary-data by type query."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: GetDictDataByTypeQuery) -> list[DictDataItemReadModel]:
        if request.redis_client is None:
            return []

        list_result = await self._dict_data_service.query_dict_data_list_from_cache_services(
            request.redis_client,
            request.dict_type,
        )
        return [_to_dict_data_item(row) for row in list_result]


class GetDictDataListQueryHandler(IQueryHandler[GetDictDataListQuery, DictDataPageReadModel]):
    """Handle paged dictionary-data list query."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: GetDictDataListQuery) -> DictDataPageReadModel:
        list_result = await self._dict_data_service.get_dict_data_list_services(request.query, is_page=request.is_page)

        if request.is_page:
            items = [_to_dict_data_item(row) for row in list_result.items]
            return DictDataPageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_dict_data_item(row) for row in list_result]
        return DictDataPageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetDictDataDetailQueryHandler(IQueryHandler[GetDictDataDetailQuery, DictDataDetailReadModel]):
    """Handle dictionary-data detail query."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: GetDictDataDetailQuery) -> DictDataDetailReadModel:
        detail_result = await self._dict_data_service.dict_data_detail_services(request.dict_code)
        if detail_result is None:
            return DictDataDetailReadModel()

        if hasattr(detail_result, 'model_dump'):
            payload = detail_result.model_dump(by_alias=False)
        elif isinstance(detail_result, dict):
            payload = detail_result
        else:
            payload = {}

        return DictDataDetailReadModel.model_validate(payload)
