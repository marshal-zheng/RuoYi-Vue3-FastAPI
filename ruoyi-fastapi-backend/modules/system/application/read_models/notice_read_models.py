"""Notice read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase


class NoticeItemReadModel(CamelModelBase):
    """Read model for notice list item."""

    notice_id: int | None = Field(default=None, description='Notice id')
    notice_title: str | None = Field(default=None, description='Notice title')
    notice_type: Literal['1', '2'] | None = Field(default=None, description='Notice type')
    notice_content: bytes | None = Field(default=None, description='Notice content')
    status: Literal['0', '1'] | None = Field(default=None, description='Notice status')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: str | None = Field(default=None, description='Remark')


class NoticePageReadModel(CamelModelBase):
    """Read model for paged notice list."""

    rows: list[NoticeItemReadModel] = Field(default_factory=list, description='Current page rows')
    page_num: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class NoticeDetailReadModel(NoticeItemReadModel):
    """Read model for notice detail."""
