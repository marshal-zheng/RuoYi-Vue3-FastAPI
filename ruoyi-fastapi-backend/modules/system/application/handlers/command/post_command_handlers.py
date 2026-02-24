"""Command handlers for post operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.system.application.commands.post_commands import AddPostCommand, DeletePostCommand, EditPostCommand
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.post_service import PostService


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddPostCommandHandler(ICommandHandler[AddPostCommand, dict[str, str]]):
    """Handle post create command."""

    def __init__(self, post_service: PostService):
        self._post_service = post_service

    async def handle(self, request: AddPostCommand) -> CommandResult[dict[str, str]]:
        request.post.validate_fields()
        create_result = await self._post_service.add_post_services(request.post)
        event = build_system_event(
            event_type='system.post.created',
            aggregate_type='post',
            aggregate_id=str(request.post.post_id or request.post.post_name or 'unknown'),
            payload={
                'postId': request.post.post_id,
                'postName': request.post.post_name,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=create_result.is_success,
            status='created' if create_result.is_success else 'failed',
            data={'message': create_result.message},
            events=(event,),
            metadata=_build_metadata(request),
        )


class EditPostCommandHandler(ICommandHandler[EditPostCommand, dict[str, str]]):
    """Handle post update command."""

    def __init__(self, post_service: PostService):
        self._post_service = post_service

    async def handle(self, request: EditPostCommand) -> CommandResult[dict[str, str]]:
        request.post.validate_fields()
        update_result = await self._post_service.edit_post_services(request.post)
        event = build_system_event(
            event_type='system.post.updated',
            aggregate_type='post',
            aggregate_id=str(request.post.post_id or request.post.post_name or 'unknown'),
            payload={
                'postId': request.post.post_id,
                'postName': request.post.post_name,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=update_result.is_success,
            status='updated' if update_result.is_success else 'failed',
            data={'message': update_result.message},
            events=(event,),
            metadata=_build_metadata(request),
        )


class DeletePostCommandHandler(ICommandHandler[DeletePostCommand, dict[str, str]]):
    """Handle post delete command."""

    def __init__(self, post_service: PostService):
        self._post_service = post_service

    async def handle(self, request: DeletePostCommand) -> CommandResult[dict[str, str]]:
        delete_result = await self._post_service.delete_post_services(request.delete_post)
        event = build_system_event(
            event_type='system.post.deleted',
            aggregate_type='post',
            aggregate_id=str(request.delete_post.post_ids or 'unknown'),
            payload={'postIds': request.delete_post.post_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data={'message': delete_result.message},
            events=(event,),
            metadata=_build_metadata(request),
        )
