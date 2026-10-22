"""Post read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkReadProjection, RemarkValue


class PostItemReadModel(CamelModelBase, RemarkReadProjection):
    """Read model for post list item."""

    post_id: int | None = Field(default=None, description='Post id')
    post_code: str | None = Field(default=None, description='Post code')
    post_name: str | None = Field(default=None, description='Post name')
    post_sort: int | None = Field(default=None, description='Post sort')
    status: Literal['0', '1'] | None = Field(default=None, description='Post status')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: RemarkValue = Field(default=None, description='Remark')


class PostPageReadModel(CamelModelBase):
    """Read model for paged post list."""

    items: list[PostItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class PostDetailReadModel(PostItemReadModel):
    """Read model for post detail."""
