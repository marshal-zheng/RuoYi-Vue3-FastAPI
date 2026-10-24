"""Config query models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.config_vo import ConfigPageQueryModel  # noqa: TC001


class _ConfigQueryContext(BaseModel):
    """Shared metadata for config read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetConfigListQuery(_ConfigQueryContext):
    """Query paged config list."""

    query: ConfigPageQueryModel = Field(description='List query payload')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetConfigDetailQuery(_ConfigQueryContext):
    """Query config detail by id."""

    config_id: int = Field(description='Config id')


class GetConfigValueByKeyQuery(_ConfigQueryContext):
    """Query config value from cache by key."""

    config_key: str = Field(description='Config key')
    redis_client: Any = Field(description='Redis client from request context')
