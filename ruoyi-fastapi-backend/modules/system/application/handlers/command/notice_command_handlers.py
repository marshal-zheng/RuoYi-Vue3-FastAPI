"""Command handlers for notice operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.system.application.commands.notice_commands import AddNoticeCommand, DeleteNoticeCommand, EditNoticeCommand
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.notice_service import NoticeService


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddNoticeCommandHandler(ICommandHandler[AddNoticeCommand, dict[str, str]]):
    """Handle notice create command."""

    def __init__(self, notice_service: NoticeService):
        self._notice_service = notice_service

    async def handle(self, request: AddNoticeCommand) -> CommandResult[dict[str, str]]:
        request.notice.validate_fields()
        create_result = await self._notice_service.add_notice_services(request.notice)
        event = build_system_event(
            event_type='system.notice.created',
            aggregate_type='notice',
            aggregate_id=str(request.notice.notice_id or request.notice.notice_title or 'unknown'),
            payload={
                'noticeId': request.notice.notice_id,
                'noticeTitle': request.notice.notice_title,
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


class EditNoticeCommandHandler(ICommandHandler[EditNoticeCommand, dict[str, str]]):
    """Handle notice update command."""

    def __init__(self, notice_service: NoticeService):
        self._notice_service = notice_service

    async def handle(self, request: EditNoticeCommand) -> CommandResult[dict[str, str]]:
        request.notice.validate_fields()
        update_result = await self._notice_service.edit_notice_services(request.notice)
        event = build_system_event(
            event_type='system.notice.updated',
            aggregate_type='notice',
            aggregate_id=str(request.notice.notice_id or request.notice.notice_title or 'unknown'),
            payload={
                'noticeId': request.notice.notice_id,
                'noticeTitle': request.notice.notice_title,
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


class DeleteNoticeCommandHandler(ICommandHandler[DeleteNoticeCommand, dict[str, str]]):
    """Handle notice delete command."""

    def __init__(self, notice_service: NoticeService):
        self._notice_service = notice_service

    async def handle(self, request: DeleteNoticeCommand) -> CommandResult[dict[str, str]]:
        delete_result = await self._notice_service.delete_notice_services(request.delete_notice)
        event = build_system_event(
            event_type='system.notice.deleted',
            aggregate_type='notice',
            aggregate_id=str(request.delete_notice.notice_ids or 'unknown'),
            payload={'noticeIds': request.delete_notice.notice_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data={'message': delete_result.message},
            events=(event,),
            metadata=_build_metadata(request),
        )
