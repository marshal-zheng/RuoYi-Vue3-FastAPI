"""Menu read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase


class MenuItemReadModel(CamelModelBase):
    """Read model for menu list item and detail."""

    menu_id: int | None = Field(default=None, description='Menu id')
    menu_name: str | None = Field(default=None, description='Menu name')
    parent_id: int | None = Field(default=None, description='Parent menu id')
    order_num: int | None = Field(default=None, description='Order number')
    path: str | None = Field(default=None, description='Route path')
    component: str | None = Field(default=None, description='Component path')
    query: str | None = Field(default=None, description='Route query')
    route_name: str | None = Field(default=None, description='Route name')
    is_frame: Literal['0', '1', 0, 1] | None = Field(default=None, description='External-link flag')
    is_cache: Literal['0', '1', 0, 1] | None = Field(default=None, description='Cache flag')
    menu_type: Literal['M', 'C', 'F'] | None = Field(default=None, description='Menu type')
    visible: Literal['0', '1'] | None = Field(default=None, description='Visible status')
    status: Literal['0', '1'] | None = Field(default=None, description='Enable status')
    perms: str | None = Field(default=None, description='Permission code')
    icon: str | None = Field(default=None, description='Icon')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: str | None = Field(default=None, description='Remark')


class MenuTreeNodeReadModel(CamelModelBase):
    """Read model for menu tree node."""

    id: int | None = Field(default=None, description='Node id')
    label: str | None = Field(default=None, description='Node label')
    parent_id: int | None = Field(default=None, description='Parent node id')
    children: list[MenuTreeNodeReadModel] = Field(default_factory=list, description='Children nodes')


class RoleMenuTreeReadModel(CamelModelBase):
    """Read model for role menu tree view."""

    menus: list[MenuTreeNodeReadModel] = Field(default_factory=list, description='Menu tree')
    checked_keys: list[int] = Field(default_factory=list, description='Checked menu ids')


MenuTreeNodeReadModel.model_rebuild()
