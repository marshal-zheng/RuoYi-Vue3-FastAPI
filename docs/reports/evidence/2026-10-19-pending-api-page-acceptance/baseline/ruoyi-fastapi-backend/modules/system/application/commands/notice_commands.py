"""Notice command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel  # noqa: TC001


class _NoticeCommandContext(BaseModel):
    """Shared runtime context for notice write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddNoticeCommand(_NoticeCommandContext):
    """Create notice entry."""

    notice: NoticeModel = Field(description='Notice payload to create')


class EditNoticeCommand(_NoticeCommandContext):
    """Update notice entry."""

    notice: NoticeModel = Field(description='Notice payload to update')


class DeleteNoticeCommand(_NoticeCommandContext):
    """Delete one or more notice entries."""

    delete_notice: DeleteNoticeModel = Field(description='Delete payload for notices')
