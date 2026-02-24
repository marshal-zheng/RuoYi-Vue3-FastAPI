"""Config read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase


class ConfigListItemReadModel(CamelModelBase):
    """Read model for config list item."""

    config_id: int | None = Field(default=None, description='Config id')
    config_name: str | None = Field(default=None, description='Config name')
    config_key: str | None = Field(default=None, description='Config key')
    config_value: str | None = Field(default=None, description='Config value')
    config_type: Literal['Y', 'N'] | None = Field(default=None, description='Built-in flag')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: str | None = Field(default=None, description='Remark')


class ConfigPageReadModel(CamelModelBase):
    """Read model for paged config list."""

    rows: list[ConfigListItemReadModel] = Field(default_factory=list, description='Current page rows')
    page_num: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class ConfigDetailReadModel(ConfigListItemReadModel):
    """Read model for config detail."""


class ConfigValueReadModel(CamelModelBase):
    """Read model for config key lookup."""

    config_key: str = Field(description='Config key')
    config_value: str = Field(description='Config value from cache')
