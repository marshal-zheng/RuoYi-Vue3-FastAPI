"""Post query models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.post_vo import PostPageQueryModel  # noqa: TC001


class _PostQueryContext(BaseModel):
    """Shared metadata for post read queries."""

    operator: str | None = Field(default=None, description='Operator who triggers the query')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetPostListQuery(_PostQueryContext):
    """Query paged post list."""

    query: PostPageQueryModel = Field(description='Post list query payload')
    is_page: bool = Field(default=True, description='Whether to return paged result')


class GetPostDetailQuery(_PostQueryContext):
    """Query post detail by id."""

    post_id: int = Field(description='Post id')
