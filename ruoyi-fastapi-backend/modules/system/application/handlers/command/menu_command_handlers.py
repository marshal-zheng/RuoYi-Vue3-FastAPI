"""Command handlers for menu operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.system.application.commands.menu_commands import AddMenuCommand, DeleteMenuCommand, EditMenuCommand
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.handlers.command.result_data import command_result_data
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.menu_service import MenuService


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddMenuCommandHandler(ICommandHandler[AddMenuCommand, dict[str, str]]):
    """Handle menu create command."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: AddMenuCommand) -> CommandResult[dict[str, str]]:
        request.menu.validate_fields()
        create_result = await self._menu_service.add_menu_services(request.menu)
        event = build_system_event(
            event_type='system.menu.created',
            aggregate_type='menu',
            aggregate_id=str(request.menu.menu_id or request.menu.menu_name or 'unknown'),
            payload={
                'menuId': request.menu.menu_id,
                'menuName': request.menu.menu_name,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=create_result.is_success,
            status='created' if create_result.is_success else 'failed',
            data=command_result_data(create_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class EditMenuCommandHandler(ICommandHandler[EditMenuCommand, dict[str, str]]):
    """Handle menu update command."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: EditMenuCommand) -> CommandResult[dict[str, str]]:
        request.menu.validate_fields()
        update_result = await self._menu_service.edit_menu_services(request.menu)
        event = build_system_event(
            event_type='system.menu.updated',
            aggregate_type='menu',
            aggregate_id=str(request.menu.menu_id or request.menu.menu_name or 'unknown'),
            payload={
                'menuId': request.menu.menu_id,
                'menuName': request.menu.menu_name,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=update_result.is_success,
            status='updated' if update_result.is_success else 'failed',
            data=command_result_data(update_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class DeleteMenuCommandHandler(ICommandHandler[DeleteMenuCommand, dict[str, str]]):
    """Handle menu delete command."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: DeleteMenuCommand) -> CommandResult[dict[str, str]]:
        delete_result = await self._menu_service.delete_menu_services(request.delete_menu)
        event = build_system_event(
            event_type='system.menu.deleted',
            aggregate_type='menu',
            aggregate_id=str(request.delete_menu.menu_ids or 'unknown'),
            payload={'menuIds': request.delete_menu.menu_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )
