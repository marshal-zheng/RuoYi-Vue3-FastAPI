"""User read models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, Literal

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkReadProjection, RemarkValue
from modules.system.application.read_models.post_read_models import PostItemReadModel  # noqa: TC001 - Pydantic schema
from modules.system.application.read_models.role_read_models import RoleItemReadModel  # noqa: TC001 - Pydantic schema


class UserInfoReadModel(CamelModelBase, RemarkReadProjection):
    """Read model for user info payload."""

    user_id: int | None = Field(default=None, description='User id')
    dept_id: int | None = Field(default=None, description='Department id')
    user_name: str | None = Field(default=None, description='User account')
    nick_name: str | None = Field(default=None, description='Nick name')
    user_type: str | None = Field(default=None, description='User type')
    email: str | None = Field(default=None, description='Email')
    phonenumber: str | None = Field(default=None, description='Phone number')
    id_card: str | None = Field(default=None, description='ID card')
    sex: Literal['0', '1', '2'] | None = Field(default=None, description='Sex')
    avatar: str | None = Field(default=None, description='Avatar URL')
    status: Literal['0', '1'] | None = Field(default=None, description='User status')
    del_flag: Literal['0', '2'] | None = Field(default=None, description='Delete flag')
    login_ip: str | None = Field(default=None, description='Last login IP')
    login_date: datetime | None = Field(default=None, description='Last login time')
    create_by: str | None = Field(default=None, description='Creator')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_by: str | None = Field(default=None, description='Updater')
    update_time: datetime | None = Field(default=None, description='Update time')
    remark: RemarkValue = Field(default=None, description='Remark')
    role_ids: str | None = Field(default=None, description='Role id string')
    post_ids: str | None = Field(default=None, description='Post id string')
    dept: dict[str, Any] | None = Field(default=None, description='Department detail')
    role: list[RoleItemReadModel] = Field(default_factory=list, description='Role list')


class UserListItemReadModel(UserInfoReadModel):
    """Read model for user list item."""


class UserPageReadModel(CamelModelBase):
    """Read model for paged user list."""

    items: list[UserListItemReadModel] = Field(default_factory=list, description='Current page items')
    page: int | None = Field(default=None, description='Current page number')
    page_size: int | None = Field(default=None, description='Page size')
    total: int = Field(default=0, description='Total records')
    has_next: bool | None = Field(default=None, description='Whether next page exists')


class UserProfileReadModel(CamelModelBase):
    """Read model for current user profile."""

    data: UserInfoReadModel | None = Field(default=None, description='User info')
    post_group: str | None = Field(default=None, description='Post display group')
    role_group: str | None = Field(default=None, description='Role display group')


class UserDetailReadModel(CamelModelBase):
    """Read model for user detail page."""

    data: UserInfoReadModel | None = Field(default=None, description='User info')
    post_ids: list[int] | None = Field(default=None, description='Selected post ids')
    posts: list[PostItemReadModel] = Field(default_factory=list, description='Post options')
    role_ids: list[int] | None = Field(default=None, description='Selected role ids')
    roles: list[RoleItemReadModel] = Field(default_factory=list, description='Role options')


class UserAllocatedRoleReadModel(CamelModelBase):
    """Read model for user allocated role row."""

    role_id: int | None = Field(default=None, description='Role id')
    role_name: str | None = Field(default=None, description='Role name')
    role_key: str | None = Field(default=None, description='Role key')
    role_sort: int | None = Field(default=None, description='Role sort')
    data_scope: str | None = Field(default=None, description='Data scope')
    status: Literal['0', '1'] | None = Field(default=None, description='Role status')
    create_time: datetime | None = Field(default=None, description='Create time')
    flag: bool | None = Field(default=None, description='Whether allocated')


class UserRoleResponseReadModel(CamelModelBase):
    """Read model for user-role response."""

    roles: list[UserAllocatedRoleReadModel] = Field(default_factory=list, description='Role options')
    user: UserInfoReadModel | None = Field(default=None, description='User info')
