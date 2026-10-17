"""Role command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.role_vo import AddRoleModel, DeleteRoleModel  # noqa: TC001
from module_admin.entity.vo.user_role_write_vo import (  # noqa: TC001
    RoleUserRevokeModel,
    RoleUsersGrantModel,
    RoleUsersRevokeModel,
)


class _RoleCommandContext(BaseModel):
    """Shared metadata for role write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _RoleDataScopeContext(_RoleCommandContext):
    """Shared data-scope context for role write commands."""

    enforce_data_scope: bool = Field(default=False, description='Whether to enforce role data-scope check')
    data_scope_sql: Any = Field(default='True', description='Role/Dept data-scope SQL expression')


class AddRoleCommand(_RoleCommandContext):
    """Create role entry."""

    role: AddRoleModel = Field(description='Role payload to create')


class EditRoleCommand(_RoleDataScopeContext):
    """Update role entry."""

    role: AddRoleModel = Field(description='Role payload to update')


class AssignRoleDataScopeCommand(_RoleDataScopeContext):
    """Assign role data scope."""

    role: AddRoleModel = Field(description='Role payload for data-scope update')


class DeleteRoleCommand(_RoleDataScopeContext):
    """Delete one or more role entries."""

    delete_role: DeleteRoleModel = Field(description='Delete payload for roles')


class ChangeRoleStatusCommand(_RoleDataScopeContext):
    """Change role status."""

    role: AddRoleModel = Field(description='Role payload for status update')


class _RoleUserScopeContext(_RoleCommandContext):
    enforce_scope_checks: bool = Field(description='Whether the actor is subject to user/role data scopes')
    user_data_scope_sql: Any = Field(description='User data-scope SQL')
    role_data_scope_sql: Any = Field(description='Role/Dept data-scope SQL')


class AddRoleUserCommand(_RoleUserScopeContext):
    role_user: RoleUsersGrantModel = Field(description='Users to grant this role')


class CancelRoleUserCommand(_RoleUserScopeContext):
    role_user: RoleUserRevokeModel = Field(description='Single role-user association to revoke')


class BatchCancelRoleUserCommand(_RoleUserScopeContext):
    role_user: RoleUsersRevokeModel = Field(description='Role-user associations to revoke together')
