"""Dictionary command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.dict_vo import (  # noqa: TC001
    DeleteDictDataModel,
    DeleteDictTypeModel,
    DictDataModel,
    DictTypeModel,
)


class _DictCommandContext(BaseModel):
    """Shared runtime context for dict write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddDictTypeCommand(_DictCommandContext):
    """Create dictionary type entry."""

    dict_type: DictTypeModel = Field(description='Dictionary type payload to create')


class EditDictTypeCommand(_DictCommandContext):
    """Update dictionary type entry."""

    dict_type: DictTypeModel = Field(description='Dictionary type payload to update')


class DeleteDictTypeCommand(_DictCommandContext):
    """Delete one or more dictionary type entries."""

    delete_dict_type: DeleteDictTypeModel = Field(description='Delete payload for dictionary types')


class RefreshDictCacheCommand(_DictCommandContext):
    """Refresh dictionary cache."""


class AddDictDataCommand(_DictCommandContext):
    """Create dictionary data entry."""

    dict_data: DictDataModel = Field(description='Dictionary data payload to create')


class EditDictDataCommand(_DictCommandContext):
    """Update dictionary data entry."""

    dict_data: DictDataModel = Field(description='Dictionary data payload to update')


class DeleteDictDataCommand(_DictCommandContext):
    """Delete one or more dictionary data entries."""

    delete_dict_data: DeleteDictDataModel = Field(description='Delete payload for dictionary data')
