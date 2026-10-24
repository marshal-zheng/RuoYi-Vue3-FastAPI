from __future__ import annotations

from dataclasses import dataclass

import pytest

from module_admin.entity.vo.post_vo import DeletePostModel, PostModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddPostCommand, DeletePostCommand, EditPostCommand
from modules.system.application.handlers.command.post_command_handlers import (
    AddPostCommandHandler,
    DeletePostCommandHandler,
    EditPostCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _PostServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None

    async def add_post_services(self, payload):
        self.add_called_with = payload
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_post_services(self, payload):
        self.edit_called_with = payload
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_post_services(self, payload):
        self.delete_called_with = payload
        return _CrudResponse(is_success=True, message='删除成功')


@pytest.mark.asyncio
async def test_post_command_handlers_success() -> None:
    post_service = _PostServiceStub()
    add_handler = AddPostCommandHandler(post_service)
    edit_handler = EditPostCommandHandler(post_service)
    delete_handler = DeletePostCommandHandler(post_service)
    redis_client = object()

    add_result = await add_handler.handle(
        AddPostCommand(
            post=PostModel(postCode='dev', postName='开发工程师', postSort=1, status='0'),
            redis_client=redis_client,
            operator='admin',
        )
    )
    edit_result = await edit_handler.handle(
        EditPostCommand(
            post=PostModel(postId=1, postCode='dev', postName='开发工程师', postSort=1, status='0'),
            redis_client=redis_client,
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeletePostCommand(
            delete_post=DeletePostModel(postIds='1'),
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert post_service.add_called_with is not None
    assert post_service.edit_called_with is not None
    assert post_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_post_write_commands() -> None:
    post_service = _PostServiceStub()
    mediator = provide_system_mediator(post_service=post_service)
    redis_client = object()

    add_result = await mediator.send(
        AddPostCommand(
            post=PostModel(postCode='dev', postName='开发工程师', postSort=1, status='0'),
            redis_client=redis_client,
        )
    )
    delete_result = await mediator.send(
        DeletePostCommand(
            delete_post=DeletePostModel(postIds='1'),
            redis_client=redis_client,
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert post_service.add_called_with is not None
    assert post_service.delete_called_with is not None
