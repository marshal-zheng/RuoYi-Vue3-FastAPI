"""Post command models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from module_admin.entity.vo.post_vo import DeletePostModel, PostModel  # noqa: TC001


class _PostCommandContext(BaseModel):
    """Shared runtime context for post write commands."""

    query_db: Any = Field(default=None, description='Request-scoped database session')
    redis_client: Any = Field(description='Redis client from application runtime context')
    operator: str | None = Field(default=None, description='Operator who triggers the command')
    trace_id: str | None = Field(default=None, description='Trace id for correlation')
    request_id: str | None = Field(default=None, description='Request id for correlation')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddPostCommand(_PostCommandContext):
    """Create post entry."""

    post: PostModel = Field(description='Post payload to create')


class EditPostCommand(_PostCommandContext):
    """Update post entry."""

    post: PostModel = Field(description='Post payload to update')


class DeletePostCommand(_PostCommandContext):
    """Delete one or more post entries."""

    delete_post: DeletePostModel = Field(description='Delete payload for posts')
