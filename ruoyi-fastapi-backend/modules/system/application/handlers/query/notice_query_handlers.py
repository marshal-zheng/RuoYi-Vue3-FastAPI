"""Query handlers for notice operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.notice_queries import GetNoticeDetailQuery, GetNoticeListQuery
from modules.system.application.read_models.notice_read_models import (
    NoticeDetailReadModel,
    NoticeItemReadModel,
    NoticePageReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.notice_service import NoticeService


def _to_notice_item(raw: Any) -> NoticeItemReadModel:
    if hasattr(raw, 'model_dump'):
        payload = raw.model_dump(by_alias=False)
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    return NoticeItemReadModel.model_validate(payload)


class GetNoticeListQueryHandler(IQueryHandler[GetNoticeListQuery, NoticePageReadModel]):
    """Handle paged notice list query."""

    def __init__(self, notice_service: NoticeService):
        self._notice_service = notice_service

    async def handle(self, request: GetNoticeListQuery) -> NoticePageReadModel:
        list_result = await self._notice_service.get_notice_list_services(request.query, is_page=request.is_page)

        if request.is_page:
            items = [_to_notice_item(row) for row in list_result.items]
            return NoticePageReadModel(
                items=items,
                page=list_result.page,
                page_size=list_result.page_size,
                total=list_result.total,
                has_next=list_result.has_next,
            )

        items = [_to_notice_item(row) for row in list_result]
        return NoticePageReadModel(
            items=items,
            page=1,
            page_size=len(items),
            total=len(items),
            has_next=False,
        )


class GetNoticeDetailQueryHandler(IQueryHandler[GetNoticeDetailQuery, NoticeDetailReadModel]):
    """Handle notice detail query."""

    def __init__(self, notice_service: NoticeService):
        self._notice_service = notice_service

    async def handle(self, request: GetNoticeDetailQuery) -> NoticeDetailReadModel:
        detail_result = await self._notice_service.notice_detail_services(request.notice_id)

        if hasattr(detail_result, 'model_dump'):
            payload = detail_result.model_dump(by_alias=False)
        elif isinstance(detail_result, dict):
            payload = detail_result
        else:
            payload = {}

        return NoticeDetailReadModel.model_validate(payload)
