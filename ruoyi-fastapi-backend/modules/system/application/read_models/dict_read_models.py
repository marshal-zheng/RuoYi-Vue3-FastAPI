"""Dictionary read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkReadProjection, RemarkValue


class DictTypeItemReadModel(CamelModelBase, RemarkReadProjection):
    """Read model for dictionary-type list item."""

    dict_id: int | None = Field(default=None, description='Dictionary type id')
    dict_name: str | None = Field(default=None, description='Dictionary type name')
    dict_type: str | None = Field(default=None, description='Dictionary type key')
    status: Literal['0', '1'] | None = Field(default=None, description='Status')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: RemarkValue = Field(default=None, description='Remark')


class DictTypePageReadModel(CamelModelBase):
    """Read model for paged dictionary-type list."""

    items: list[DictTypeItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class DictTypeDetailReadModel(DictTypeItemReadModel):
    """Read model for dictionary-type detail."""


class DictDataItemReadModel(CamelModelBase, RemarkReadProjection):
    """Read model for dictionary-data item."""

    dict_code: int | None = Field(default=None, description='Dictionary data code')
    dict_sort: int | None = Field(default=None, description='Sort order')
    dict_label: str | None = Field(default=None, description='Label')
    dict_value: str | None = Field(default=None, description='Value')
    dict_type: str | None = Field(default=None, description='Dictionary type key')
    css_class: str | None = Field(default=None, description='CSS class')
    list_class: str | None = Field(default=None, description='List class')
    is_default: Literal['Y', 'N'] | None = Field(default=None, description='Default flag')
    status: Literal['0', '1'] | None = Field(default=None, description='Status')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: RemarkValue = Field(default=None, description='Remark')


class DictDataPageReadModel(CamelModelBase):
    """Read model for paged dictionary-data list."""

    items: list[DictDataItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class DictDataDetailReadModel(DictDataItemReadModel):
    """Read model for dictionary-data detail."""
