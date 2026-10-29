from __future__ import annotations

from dataclasses import dataclass

import pytest

from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddNoticeCommand, DeleteNoticeCommand, EditNoticeCommand
from modules.system.application.handlers.command.notice_command_handlers import (
    AddNoticeCommandHandler,
    DeleteNoticeCommandHandler,
    EditNoticeCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _NoticeServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None
        self.actors: list[object] = []

    async def add_notice_services(self, payload, *, actor):
        self.add_called_with = payload
        self.actors.append(actor)
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_notice_services(self, payload, *, actor):
        self.edit_called_with = payload
        self.actors.append(actor)
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_notice_services(self, payload):
        self.delete_called_with = payload
        return _CrudResponse(is_success=True, message='删除成功')


@pytest.mark.asyncio
async def test_notice_command_handlers_success() -> None:
    notice_service = _NoticeServiceStub()
    add_handler = AddNoticeCommandHandler(notice_service)
    edit_handler = EditNoticeCommandHandler(notice_service)
    delete_handler = DeleteNoticeCommandHandler(notice_service)
    redis_client = object()
    actor = object()

    add_result = await add_handler.handle(
        AddNoticeCommand(
            notice=NoticeModel(noticeTitle='系统通知', noticeType='1', noticeContent='<p>hello</p>', status='0'),
            redis_client=redis_client,
            operator='admin',
            actor=actor,
        )
    )
    edit_result = await edit_handler.handle(
        EditNoticeCommand(
            notice=NoticeModel(
                noticeId=1, noticeTitle='系统通知', noticeType='1', noticeContent='<p>world</p>', status='0'
            ),
            redis_client=redis_client,
            operator='admin',
            actor=actor,
        )
    )
    delete_result = await delete_handler.handle(
        DeleteNoticeCommand(
            delete_notice=DeleteNoticeModel(noticeIds='1'),
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert notice_service.add_called_with is not None
    assert notice_service.edit_called_with is not None
    assert notice_service.delete_called_with is not None
    # The authorization snapshot reaches the service, which binds uploaded image drafts in its transaction.
    assert notice_service.actors == [actor, actor]


@pytest.mark.asyncio
async def test_system_mediator_dispatches_notice_write_commands() -> None:
    notice_service = _NoticeServiceStub()
    mediator = provide_system_mediator(notice_service=notice_service)
    redis_client = object()

    add_result = await mediator.send(
        AddNoticeCommand(
            notice=NoticeModel(noticeTitle='系统通知', noticeType='1', noticeContent='<p>hello</p>', status='0'),
            redis_client=redis_client,
        )
    )
    delete_result = await mediator.send(
        DeleteNoticeCommand(
            delete_notice=DeleteNoticeModel(noticeIds='1'),
            redis_client=redis_client,
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert notice_service.add_called_with is not None
    assert notice_service.delete_called_with is not None
