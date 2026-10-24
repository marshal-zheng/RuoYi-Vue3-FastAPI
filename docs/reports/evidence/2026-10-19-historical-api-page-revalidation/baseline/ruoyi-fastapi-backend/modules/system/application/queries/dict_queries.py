"""Dictionary query models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.dict_vo import DictDataPageQueryModel, DictTypePageQueryModel  # noqa: TC001


class _DictQueryContext(BaseModel):
    """Shared metadata for dictionary read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetDictTypeListQuery(_DictQueryContext):
    """Query paged dictionary-type list."""

    query: DictTypePageQueryModel = Field(description='Dict type list query payload')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetDictTypeOptionsQuery(_DictQueryContext):
    """Query dictionary-type options."""


class GetDictTypeDetailQuery(_DictQueryContext):
    """Query dictionary-type detail by id."""

    dict_id: int = Field(description='Dictionary type id')


class GetDictDataByTypeQuery(_DictQueryContext):
    """Query dictionary-data by dictionary type from cache."""

    dict_type: str = Field(description='Dictionary type key')
    redis_client: Any = Field(description='Redis client from request context')


class GetDictDataListQuery(_DictQueryContext):
    """Query paged dictionary-data list."""

    query: DictDataPageQueryModel = Field(description='Dict data list query payload')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetDictDataDetailQuery(_DictQueryContext):
    """Query dictionary-data detail by code."""

    dict_code: int = Field(description='Dictionary data code')
