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


class ApiResponse(SharedModelBase, Generic[T]):
    """Standard API envelope."""

    code: int = Field(default=200, description='Response code')
    msg: str = Field(default='success', description='Response message')
    data: T | None = Field(default=None, description='Response payload')


class PageResponse(SharedModelBase, Generic[T]):
    """Standard paginated response."""

    rows: list[T] = Field(default_factory=list, description='Result rows')
    total: int = Field(default=0, description='Total rows')
    code: int = Field(default=200, description='Response code')
    msg: str = Field(default='success', description='Response message')


class SuccessResponse(ApiResponse[Any]):
    """Shortcut for successful operations."""

    code: int = Field(default=200, description='Response code')
    msg: str = Field(default='操作成功', description='Response message')


class ErrorResponse(ApiResponse[None]):
    """Shortcut for error operations."""

    code: int = Field(default=500, description='Response code')
    msg: str = Field(default='操作失败', description='Response message')
    data: None = Field(default=None, description='Response payload')
