"""Menu command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuModel  # noqa: TC001


class _MenuCommandContext(BaseModel):
    """Shared runtime context for menu write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddMenuCommand(_MenuCommandContext):
    """Create menu entry."""

    menu: MenuModel = Field(description='Menu payload to create')


class EditMenuCommand(_MenuCommandContext):
    """Update menu entry."""

    menu: MenuModel = Field(description='Menu payload to update')


class DeleteMenuCommand(_MenuCommandContext):
    """Delete one or more menu entries."""

    delete_menu: DeleteMenuModel = Field(description='Delete payload for menus')
