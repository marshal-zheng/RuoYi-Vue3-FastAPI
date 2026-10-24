"""System configuration command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.config_vo import ConfigModel, DeleteConfigModel  # noqa: TC001


class _ConfigCommandContext(BaseModel):
    """Shared runtime context for config write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddConfigCommand(_ConfigCommandContext):
    """Create system configuration entry."""

    config: ConfigModel = Field(description='Configuration payload to create')


class EditConfigCommand(_ConfigCommandContext):
    """Update system configuration entry."""

    config: ConfigModel = Field(description='Configuration payload to update')


class DeleteConfigCommand(_ConfigCommandContext):
    """Delete one or more system configuration entries."""

    delete_config: DeleteConfigModel = Field(description='Delete payload including config ids')


class RefreshConfigCacheCommand(_ConfigCommandContext):
    """Refresh system configuration cache command."""
