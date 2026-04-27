"""User command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.user_vo import (  # noqa: TC001
    AddUserModel,
    CrudUserRoleModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    ResetUserModel,
)


class _UserCommandContext(BaseModel):
    """Shared metadata for user write commands."""

    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _UserDbCommandContext(_UserCommandContext):
    """Shared request-scoped DB context for user commands."""

    query_db: Any = Field(description='Request-scoped database session')


class AddUserCommand(_UserDbCommandContext):
    """Create user entry."""

    user: AddUserModel = Field(description='User payload to create')
    enforce_scope_checks: bool = Field(default=False, description='Whether to enforce dept/role scope checks')
    dept_data_scope_sql: Any = Field(default='True', description='Dept data-scope SQL')
    role_data_scope_sql: Any = Field(default='True', description='Role data-scope SQL')


class EditUserCommand(_UserDbCommandContext):
    """Update user entry."""

    user: EditUserModel = Field(description='User payload to update')
    enforce_scope_checks: bool = Field(default=False, description='Whether to enforce user/dept/role scope checks')
    user_data_scope_sql: Any = Field(default='True', description='User data-scope SQL')
    dept_data_scope_sql: Any = Field(default='True', description='Dept data-scope SQL')
    role_data_scope_sql: Any = Field(default='True', description='Role data-scope SQL')


class DeleteUserCommand(_UserDbCommandContext):
    """Delete user entries."""

    delete_user: DeleteUserModel = Field(description='Delete payload for users')
    enforce_scope_checks: bool = Field(default=False, description='Whether to enforce user scope checks')
    user_data_scope_sql: Any = Field(default='True', description='User data-scope SQL')
    current_user_id: int | None = Field(default=None, description='Current login user id')


class ResetUserPasswordCommand(_UserDbCommandContext):
    """Reset current-user password."""

    reset_user: ResetUserModel = Field(description='Reset password payload')


class ImportUsersCommand(_UserDbCommandContext):
    """Batch import users from file."""

    request: Any = Field(description='FastAPI request object')
    file: Any = Field(description='Uploaded file object')
    update_support: bool = Field(description='Whether to update existing users')
    current_user: CurrentUserModel = Field(description='Current login user context')
    user_data_scope_sql: Any = Field(description='User data-scope SQL')
    dept_data_scope_sql: Any = Field(description='Dept data-scope SQL')


class AssignUserRolesCommand(_UserDbCommandContext):
    """Assign roles to a user."""

    user_role: CrudUserRoleModel = Field(description='User-role assignment payload')
    enforce_scope_checks: bool = Field(default=False, description='Whether to enforce user/role scope checks')
    user_data_scope_sql: Any = Field(default='True', description='User data-scope SQL')
    role_data_scope_sql: Any = Field(default='True', description='Role data-scope SQL')
