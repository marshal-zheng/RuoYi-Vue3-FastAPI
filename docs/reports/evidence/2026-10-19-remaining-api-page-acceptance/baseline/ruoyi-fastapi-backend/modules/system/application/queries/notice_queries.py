"""Notice query models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.notice_vo import NoticePageQueryModel  # noqa: TC001


class _NoticeQueryContext(BaseModel):
    """Shared metadata for notice read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetNoticeListQuery(_NoticeQueryContext):
    """Query paged notice list."""

    query: NoticePageQueryModel = Field(description='Notice list query payload')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetNoticeDetailQuery(_NoticeQueryContext):
    """Query notice detail by id."""

    notice_id: int = Field(description='Notice id')
