"""Business-agnostic API response models shared across contexts."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar('T')


class SharedModelBase(BaseModel):
    """Base model using camelCase aliases for API boundaries."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class ResourceResponse(SharedModelBase, Generic[T]):
    """Typed resource response helper for internal service boundaries."""

    data: T | None = Field(default=None, description='Response payload')


class PageResponse(SharedModelBase, Generic[T]):
    """Offset paginated response aligned with the HTTP contract."""

    items: list[T] = Field(default_factory=list, description='Result items')
    total: int = Field(default=0, description='Total items')
    page: int = Field(default=1, description='Current page number')
    page_size: int = Field(default=10, description='Page size')


class SuccessResponse(ResourceResponse[Any]):
    """Shortcut for successful resource responses."""

    data: Any | None = Field(default=None, description='Response payload')


class ErrorResponse(SharedModelBase):
    """Internal error pointer; public HTTP errors use RFC 9457 Problem Details."""

    type: str = Field(default='about:blank', description='Problem type URI')
    title: str = Field(default='请求失败', description='Short summary')
    status: int = Field(default=500, description='HTTP status')
    detail: str = Field(default='请求失败', description='Detailed explanation')
