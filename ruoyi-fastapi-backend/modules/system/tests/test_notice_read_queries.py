from __future__ import annotations

import pytest

from module_admin.entity.vo.notice_vo import NoticePageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.notice_query_handlers import (
    GetNoticeDetailQueryHandler,
    GetNoticeListQueryHandler,
)
from modules.system.application.queries import GetNoticeDetailQuery, GetNoticeListQuery
from modules.system.application.read_models import (
    NoticeDetailReadModel,
    NoticeItemReadModel,
    NoticePageReadModel,
)
from utils.page_util import PageResponseModel


class _NoticeServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.detail_called_with = None

    async def get_notice_list_services(self, query, is_page=True):
        self.list_called_with = (query, is_page)
        if is_page:
            return PageResponseModel(
                items=[
                    {
                        'noticeId': 1,
                        'noticeTitle': '系统公告',
                        'noticeType': '1',
                        'status': '0',
                    }
                ],
                page=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'noticeId': 1,
                'noticeTitle': '系统公告',
                'noticeType': '1',
                'status': '0',
            }
        ]

    async def notice_detail_services(self, notice_id):
        self.detail_called_with = notice_id
        return {
            'noticeId': notice_id,
            'noticeTitle': '系统公告',
            'noticeType': '1',
            'status': '0',
        }


@pytest.mark.asyncio
async def test_notice_query_handlers_success() -> None:
    notice_service = _NoticeServiceStub()
    list_handler = GetNoticeListQueryHandler(notice_service)
    detail_handler = GetNoticeDetailQueryHandler(notice_service)

    list_result = await list_handler.handle(
        GetNoticeListQuery(
            query=NoticePageQueryModel(page=1, pageSize=10),
            is_page=True,
            operator='admin',
        )
    )
    detail_result = await detail_handler.handle(GetNoticeDetailQuery(notice_id=1, operator='admin'))

    assert isinstance(list_result, NoticePageReadModel)
    assert isinstance(list_result.items[0], NoticeItemReadModel)
    assert isinstance(detail_result, NoticeDetailReadModel)
    assert list_result.items[0].notice_title == '系统公告'
    assert detail_result.notice_id == 1


@pytest.mark.asyncio
async def test_system_mediator_dispatches_notice_read_queries() -> None:
    notice_service = _NoticeServiceStub()
    mediator = provide_system_mediator(notice_service=notice_service)

    list_result = await mediator.query(
        GetNoticeListQuery(
            query=NoticePageQueryModel(page=1, pageSize=10),
            is_page=True,
        )
    )
    detail_result = await mediator.query(GetNoticeDetailQuery(notice_id=1))

    assert isinstance(list_result, NoticePageReadModel)
    assert isinstance(detail_result, NoticeDetailReadModel)
    assert list_result.items[0].notice_title == '系统公告'
