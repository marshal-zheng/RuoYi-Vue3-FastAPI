"""Department command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel  # noqa: TC001


class _DeptCommandContext(BaseModel):
    """Shared runtime context for department write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _DeptDataScopeCommandContext(_DeptCommandContext):
    """Shared data-scope context for department write commands."""

    enforce_data_scope: bool = Field(default=False, description='Whether to enforce department data-scope check')
    data_scope_sql: Any = Field(default='True', description='Department data-scope SQL expression')


class AddDeptCommand(_DeptDataScopeCommandContext):
    """Create department entry."""

    dept: DeptModel = Field(description='Department payload to create')


class EditDeptCommand(_DeptDataScopeCommandContext):
    """Update department entry."""

    dept: DeptModel = Field(description='Department payload to update')


class DeleteDeptCommand(_DeptDataScopeCommandContext):
    """Delete one or more department entries."""

    delete_dept: DeleteDeptModel = Field(description='Delete payload for departments')
