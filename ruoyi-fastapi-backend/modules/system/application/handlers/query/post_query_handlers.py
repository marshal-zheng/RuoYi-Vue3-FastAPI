"""Query handlers for post operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.post_queries import GetPostDetailQuery, GetPostListQuery
from modules.system.application.read_models.post_read_models import (
    PostDetailReadModel,
    PostItemReadModel,
    PostPageReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.post_service import PostService


def _to_post_item(raw: Any) -> PostItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return PostItemReadModel.model_validate(payload)


class GetPostListQueryHandler(IQueryHandler[GetPostListQuery, PostPageReadModel]):
    """Handle paged post list query."""

    def __init__(self, post_service: PostService):
        self._post_service = post_service

    async def handle(self, request: GetPostListQuery) -> PostPageReadModel:
        list_result = await self._post_service.get_post_list_services(request.query, is_page=request.is_page)

        if request.is_page:
            items = [_to_post_item(row) for row in list_result.items]
            return PostPageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_post_item(row) for row in list_result]
        return PostPageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetPostDetailQueryHandler(IQueryHandler[GetPostDetailQuery, PostDetailReadModel]):
    """Handle post detail query."""

    def __init__(self, post_service: PostService):
        self._post_service = post_service

    async def handle(self, request: GetPostDetailQuery) -> PostDetailReadModel:
        detail_result = await self._post_service.post_detail_services(request.post_id)
        if detail_result is None:
            return PostDetailReadModel()

        if hasattr(detail_result, 'model_dump'):
            payload = detail_result.model_dump(by_alias=False)
        elif isinstance(detail_result, dict):
            payload = detail_result
        else:
            payload = {}

        return PostDetailReadModel.model_validate(payload)
