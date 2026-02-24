"""Notice service unit tests for the repository-based architecture."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config.constant import CommonConstant
from module_admin.entity.vo.notice_vo import NoticeModel
from modules.system.application.services.notice_service import NoticeService


@pytest.mark.asyncio
async def test_check_notice_unique_returns_true_when_not_found():
    notice = NoticeModel(noticeTitle="Title", noticeType="1", noticeContent=b"content")
    notice_repo = AsyncMock()
    notice_repo.find_by_content.return_value = None
    service = NoticeService(notice_repo=notice_repo, query_db=AsyncMock())
    result = await service.check_notice_unique_services(notice)

    assert result is CommonConstant.UNIQUE


@pytest.mark.asyncio
async def test_check_notice_unique_returns_false_when_conflict_found():
    notice = NoticeModel(noticeId=10, noticeTitle="Title", noticeType="1", noticeContent=b"content")
    notice_repo = AsyncMock()
    notice_repo.find_by_content.return_value = SimpleNamespace(notice_id=20)
    service = NoticeService(notice_repo=notice_repo, query_db=AsyncMock())
    result = await service.check_notice_unique_services(notice)

    assert result is CommonConstant.NOT_UNIQUE


def test_notice_service_contract_methods_exist():
    assert callable(NoticeService.get_notice_list_services)
    assert callable(NoticeService.add_notice_services)
    assert callable(NoticeService.edit_notice_services)
    assert callable(NoticeService.delete_notice_services)
