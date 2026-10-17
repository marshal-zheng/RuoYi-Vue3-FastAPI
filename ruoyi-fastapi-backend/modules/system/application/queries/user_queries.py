"""User query models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.user_vo import UserPageQueryModel  # noqa: TC001


class _UserQueryContext(BaseModel):
    """Shared metadata for user read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _UserDbQueryContext(_UserQueryContext):
    """Shared DB context for user read queries."""

    query_db: Any = Field(description='Request-scoped database session')


class GetUserDeptTreeQuery(_UserQueryContext):
    """Query department tree for user operations."""

    data_scope_sql: Any = Field(default='True', description='Data scope SQL for dept filtering')


class GetUserListQuery(_UserDbQueryContext):
    """Query paged user list."""

    query: UserPageQueryModel = Field(description='User list query payload')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for user filtering')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetUserProfileQuery(_UserDbQueryContext):
    """Query current user profile."""

    user_id: int = Field(description='Current user id')


class GetUserDetailQuery(_UserDbQueryContext):
    """Query user detail and role/post options."""

    user_id: int | Literal[''] | None = Field(default='', description='Target user id')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for user filtering')
    require_scope_check: bool = Field(default=False, description='Whether to enforce data-scope check')


class GetUserAuthRoleQuery(_UserDbQueryContext):
    """Query roles allocated to a user."""

    user_id: int = Field(description='Target user id')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for user filtering')
    require_scope_check: bool = Field(default=False, description='Whether to enforce target user data scope')
