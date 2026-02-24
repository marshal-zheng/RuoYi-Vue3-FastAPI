"""Department query models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.dept_vo import DeptModel, DeptQueryModel


class _DeptQueryContext(BaseModel):
    """Shared metadata for department read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetDeptEditOptionQuery(_DeptQueryContext):
    """Query department list for edit option with excluded node."""

    dept_id: int = Field(description='Department id to exclude')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for permission filtering')


class GetDeptListQuery(_DeptQueryContext):
    """Query department list."""

    query: DeptQueryModel = Field(description='Department list query payload')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for permission filtering')


class GetDeptTreeSelectQuery(_DeptQueryContext):
    """Query department tree selection options."""

    data_scope_sql: Any = Field(default='True', description='Data scope SQL for permission filtering')
    query: DeptModel = Field(default_factory=DeptModel, description='Department tree query payload')


class GetDeptDetailQuery(_DeptQueryContext):
    """Query department detail by id."""

    dept_id: int = Field(description='Department id')
    data_scope_sql: Any = Field(default='True', description='Data scope SQL for permission filtering')
    require_scope_check: bool = Field(default=False, description='Whether to enforce department data scope check')
