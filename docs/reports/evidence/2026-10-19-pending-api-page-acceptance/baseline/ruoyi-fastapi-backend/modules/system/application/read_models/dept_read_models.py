"""Department read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase


class DeptItemReadModel(CamelModelBase):
    """Read model for department list item."""

    dept_id: int | None = Field(default=None, description='Department id')
    parent_id: int | None = Field(default=None, description='Parent department id')
    ancestors: str | None = Field(default=None, description='Ancestors path')
    dept_name: str | None = Field(default=None, description='Department name')
    order_num: int | None = Field(default=None, description='Order number')
    leader: str | None = Field(default=None, description='Leader')
    phone: str | None = Field(default=None, description='Phone number')
    email: str | None = Field(default=None, description='Email')
    status: Literal['0', '1'] | None = Field(default=None, description='Department status')
    del_flag: Literal['0', '2'] | None = Field(default=None, description='Delete flag')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')


class DeptDetailReadModel(DeptItemReadModel):
    """Read model for department detail."""


class DeptTreeNodeReadModel(CamelModelBase):
    """Read model for department tree node."""

    id: int | None = Field(default=None, description='Node id')
    label: str | None = Field(default=None, description='Node label')
    parent_id: int | None = Field(default=None, description='Parent node id')
    children: list[DeptTreeNodeReadModel] = Field(default_factory=list, description='Children nodes')


DeptTreeNodeReadModel.model_rebuild()
