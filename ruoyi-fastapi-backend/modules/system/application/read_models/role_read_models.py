"""Role read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase
from modules.system.application.read_models.dept_read_models import DeptTreeNodeReadModel


class RoleItemReadModel(CamelModelBase):
    """Read model for role list item."""

    role_id: int | None = Field(default=None, description='Role id')
    role_name: str | None = Field(default=None, description='Role name')
    role_key: str | None = Field(default=None, description='Role key')
    role_sort: int | None = Field(default=None, description='Role sort')
    data_scope: str | None = Field(default=None, description='Data scope')
    menu_check_strictly: int | bool | None = Field(default=None, description='Menu check strictly')
    dept_check_strictly: int | bool | None = Field(default=None, description='Dept check strictly')
    status: Literal['0', '1'] | None = Field(default=None, description='Role status')
    del_flag: Literal['0', '2'] | None = Field(default=None, description='Delete flag')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: str | None = Field(default=None, description='Remark')
    admin: bool | None = Field(default=None, description='Admin role flag')


class RolePageReadModel(CamelModelBase):
    """Read model for paged role list."""

    items: list[RoleItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class RoleDetailReadModel(RoleItemReadModel):
    """Read model for role detail."""


class RoleDeptTreeReadModel(CamelModelBase):
    """Read model for role department tree view."""

    depts: list[DeptTreeNodeReadModel] = Field(default_factory=list, description='Department tree')
    checked_keys: list[int] = Field(default_factory=list, description='Checked dept ids')


class RoleUserItemReadModel(CamelModelBase):
    """Read model for role-user list item."""

    user_id: int | None = Field(default=None, description='User id')
    user_name: str | None = Field(default=None, description='User name')
    nick_name: str | None = Field(default=None, description='Nick name')
    email: str | None = Field(default=None, description='Email')
    phonenumber: str | None = Field(default=None, description='Phone number')
    status: Literal['0', '1'] | None = Field(default=None, description='User status')
    dept: dict[str, Any] | None = Field(default=None, description='Department info')


class RoleUserPageReadModel(CamelModelBase):
    """Read model for paged role-user list."""

    items: list[RoleUserItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')
