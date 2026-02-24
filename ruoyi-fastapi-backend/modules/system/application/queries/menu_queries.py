"""Menu query models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.menu_vo import MenuQueryModel  # noqa: TC001
from module_admin.entity.vo.user_vo import CurrentUserModel  # noqa: TC001


class _MenuQueryContext(BaseModel):
    """Shared metadata for menu read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetMenuTreeQuery(_MenuQueryContext):
    """Query menu tree for current user."""

    current_user: CurrentUserModel = Field(description='Current user context')


class GetRoleMenuTreeQuery(_MenuQueryContext):
    """Query role-bound menu tree for current user."""

    role_id: int = Field(description='Role id')
    current_user: CurrentUserModel = Field(description='Current user context')


class GetMenuListQuery(_MenuQueryContext):
    """Query menu list."""

    query: MenuQueryModel = Field(description='Menu list query payload')
    current_user: CurrentUserModel = Field(description='Current user context')


class GetMenuDetailQuery(_MenuQueryContext):
    """Query menu detail by id."""

    menu_id: int = Field(description='Menu id')
