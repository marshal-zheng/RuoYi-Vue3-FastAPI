"""Role query models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.role_vo import RolePageQueryModel  # noqa: TC001
from module_admin.entity.vo.user_vo import UserRolePageQueryModel  # noqa: TC001


class _RoleQueryContext(BaseModel):
    """Shared metadata for role read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetRoleDeptTreeQuery(_RoleQueryContext):
    """Query role department tree."""

    role_id: int = Field(description='Role id')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for dept filtering')


class GetRoleListQuery(_RoleQueryContext):
    """Query paged role list."""

    query: RolePageQueryModel = Field(description='Role list query payload')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for role filtering')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetRoleDetailQuery(_RoleQueryContext):
    """Query role detail by id."""

    role_id: int = Field(description='Role id')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for role filtering')
    require_scope_check: bool = Field(default=False, description='Whether to enforce data-scope check')


class GetRoleAllocatedUsersQuery(_RoleQueryContext):
    """Query users allocated to a role."""

    query: UserRolePageQueryModel = Field(description='Role-user page query payload')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for user filtering')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetRoleUnallocatedUsersQuery(_RoleQueryContext):
    """Query users not allocated to a role."""

    query: UserRolePageQueryModel = Field(description='Role-user page query payload')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for user filtering')
    is_page: bool = Field(default=True, description='Whether to return paged result')
