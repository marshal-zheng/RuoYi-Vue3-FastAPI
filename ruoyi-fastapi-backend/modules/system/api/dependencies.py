"""System context API dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends

from container.dependencies import service_provider
from modules.system.application.behaviors import build_default_command_behaviors, build_default_query_behaviors
from modules.system.application.commands.config_commands import (
    AddConfigCommand,
    DeleteConfigCommand,
    EditConfigCommand,
    RefreshConfigCacheCommand,
)
from modules.system.application.commands.dept_commands import AddDeptCommand, DeleteDeptCommand, EditDeptCommand
from modules.system.application.commands.dict_commands import (
    AddDictDataCommand,
    AddDictTypeCommand,
    DeleteDictDataCommand,
    DeleteDictTypeCommand,
    EditDictDataCommand,
    EditDictTypeCommand,
    RefreshDictCacheCommand,
)
from modules.system.application.commands.menu_commands import AddMenuCommand, DeleteMenuCommand, EditMenuCommand
from modules.system.application.commands.notice_commands import AddNoticeCommand, DeleteNoticeCommand, EditNoticeCommand
from modules.system.application.commands.post_commands import AddPostCommand, DeletePostCommand, EditPostCommand
from modules.system.application.commands.role_commands import (
    AddRoleCommand,
    AddRoleUserCommand,
    AssignRoleDataScopeCommand,
    BatchCancelRoleUserCommand,
    CancelRoleUserCommand,
    ChangeRoleStatusCommand,
    DeleteRoleCommand,
    EditRoleCommand,
)
from modules.system.application.commands.user_commands import (
    AddUserCommand,
    AssignUserRolesCommand,
    DeleteUserCommand,
    EditUserCommand,
    ImportUsersCommand,
    ResetUserPasswordCommand,
)
from modules.system.application.handler_registry import HandlerRegistry
from modules.system.application.handlers.command.config_command_handlers import (
    AddConfigCommandHandler,
    DeleteConfigCommandHandler,
    EditConfigCommandHandler,
    RefreshConfigCacheCommandHandler,
)
from modules.system.application.handlers.command.dept_command_handlers import (
    AddDeptCommandHandler,
    DeleteDeptCommandHandler,
    EditDeptCommandHandler,
)
from modules.system.application.handlers.command.dict_command_handlers import (
    AddDictDataCommandHandler,
    AddDictTypeCommandHandler,
    DeleteDictDataCommandHandler,
    DeleteDictTypeCommandHandler,
    EditDictDataCommandHandler,
    EditDictTypeCommandHandler,
    RefreshDictCacheCommandHandler,
)
from modules.system.application.handlers.command.menu_command_handlers import (
    AddMenuCommandHandler,
    DeleteMenuCommandHandler,
    EditMenuCommandHandler,
)
from modules.system.application.handlers.command.notice_command_handlers import (
    AddNoticeCommandHandler,
    DeleteNoticeCommandHandler,
    EditNoticeCommandHandler,
)
from modules.system.application.handlers.command.post_command_handlers import (
    AddPostCommandHandler,
    DeletePostCommandHandler,
    EditPostCommandHandler,
)
from modules.system.application.handlers.command.role_command_handlers import (
    AddRoleCommandHandler,
    AddRoleUserCommandHandler,
    AssignRoleDataScopeCommandHandler,
    BatchCancelRoleUserCommandHandler,
    CancelRoleUserCommandHandler,
    ChangeRoleStatusCommandHandler,
    DeleteRoleCommandHandler,
    EditRoleCommandHandler,
)
from modules.system.application.handlers.command.user_command_handlers import (
    AddUserCommandHandler,
    AssignUserRolesCommandHandler,
    DeleteUserCommandHandler,
    EditUserCommandHandler,
    ImportUsersCommandHandler,
    ResetUserPasswordCommandHandler,
)
from modules.system.application.handlers.query.config_query_handlers import (
    GetConfigDetailQueryHandler,
    GetConfigListQueryHandler,
    GetConfigValueByKeyQueryHandler,
)
from modules.system.application.handlers.query.dept_query_handlers import (
    GetDeptDetailQueryHandler,
    GetDeptEditOptionQueryHandler,
    GetDeptListQueryHandler,
    GetDeptTreeSelectQueryHandler,
)
from modules.system.application.handlers.query.dict_query_handlers import (
    GetDictDataByTypeQueryHandler,
    GetDictDataDetailQueryHandler,
    GetDictDataListQueryHandler,
    GetDictTypeDetailQueryHandler,
    GetDictTypeListQueryHandler,
    GetDictTypeOptionsQueryHandler,
)
from modules.system.application.handlers.query.menu_query_handlers import (
    GetMenuDetailQueryHandler,
    GetMenuListQueryHandler,
    GetMenuTreeQueryHandler,
    GetRoleMenuTreeQueryHandler,
)
from modules.system.application.handlers.query.notice_query_handlers import (
    GetNoticeDetailQueryHandler,
    GetNoticeListQueryHandler,
)
from modules.system.application.handlers.query.post_query_handlers import (
    GetPostDetailQueryHandler,
    GetPostListQueryHandler,
)
from modules.system.application.handlers.query.role_query_handlers import (
    GetRoleAllocatedUsersQueryHandler,
    GetRoleDeptTreeQueryHandler,
    GetRoleDetailQueryHandler,
    GetRoleListQueryHandler,
    GetRoleUnallocatedUsersQueryHandler,
)
from modules.system.application.handlers.query.user_query_handlers import (
    GetUserAuthRoleQueryHandler,
    GetUserDeptTreeQueryHandler,
    GetUserDetailQueryHandler,
    GetUserListQueryHandler,
    GetUserProfileQueryHandler,
)
from modules.system.application.mediator import Mediator
from modules.system.application.queries.config_queries import (
    GetConfigDetailQuery,
    GetConfigListQuery,
    GetConfigValueByKeyQuery,
)
from modules.system.application.queries.dept_queries import (
    GetDeptDetailQuery,
    GetDeptEditOptionQuery,
    GetDeptListQuery,
    GetDeptTreeSelectQuery,
)
from modules.system.application.queries.dict_queries import (
    GetDictDataByTypeQuery,
    GetDictDataDetailQuery,
    GetDictDataListQuery,
    GetDictTypeDetailQuery,
    GetDictTypeListQuery,
    GetDictTypeOptionsQuery,
)
from modules.system.application.queries.menu_queries import (
    GetMenuDetailQuery,
    GetMenuListQuery,
    GetMenuTreeQuery,
    GetRoleMenuTreeQuery,
)
from modules.system.application.queries.notice_queries import GetNoticeDetailQuery, GetNoticeListQuery
from modules.system.application.queries.post_queries import GetPostDetailQuery, GetPostListQuery
from modules.system.application.queries.role_queries import (
    GetRoleAllocatedUsersQuery,
    GetRoleDeptTreeQuery,
    GetRoleDetailQuery,
    GetRoleListQuery,
    GetRoleUnallocatedUsersQuery,
)
from modules.system.application.queries.user_queries import (
    GetUserAuthRoleQuery,
    GetUserDeptTreeQuery,
    GetUserDetailQuery,
    GetUserListQuery,
    GetUserProfileQuery,
)
from modules.system.application.services.user_role_service import UserRoleService

if TYPE_CHECKING:
    from modules.system.application.services import DictDataService, DictTypeService
    from modules.system.application.services.config_service import ConfigService
    from modules.system.application.services.dept_service import DeptService
    from modules.system.application.services.menu_service import MenuService
    from modules.system.application.services.notice_service import NoticeService
    from modules.system.application.services.post_service import PostService
    from modules.system.application.services.role_service import RoleService
    from modules.system.application.services.user_service import UserService


def provide_system_mediator(  # noqa: PLR0915
    config_service: ConfigService = Depends(service_provider('config_service')),
    dept_service: DeptService = Depends(service_provider('dept_service')),
    dict_type_service: DictTypeService = Depends(service_provider('dict_type_service')),
    dict_data_service: DictDataService = Depends(service_provider('dict_data_service')),
    menu_service: MenuService = Depends(service_provider('menu_service')),
    notice_service: NoticeService = Depends(service_provider('notice_service')),
    post_service: PostService = Depends(service_provider('post_service')),
    role_service: RoleService = Depends(service_provider('role_service')),
    user_service: UserService = Depends(service_provider('user_service')),
) -> Mediator:
    """Build request-scoped mediator with explicit system handlers."""
    registry = HandlerRegistry()
    user_role_service = UserRoleService(user_service, role_service)
    registry.register_command(
        AddConfigCommand,
        AddConfigCommandHandler(config_service),
    )
    registry.register_command(
        EditConfigCommand,
        EditConfigCommandHandler(config_service),
    )
    registry.register_command(
        DeleteConfigCommand,
        DeleteConfigCommandHandler(config_service),
    )
    registry.register_command(
        AddDeptCommand,
        AddDeptCommandHandler(dept_service),
    )
    registry.register_command(
        EditDeptCommand,
        EditDeptCommandHandler(dept_service),
    )
    registry.register_command(
        DeleteDeptCommand,
        DeleteDeptCommandHandler(dept_service),
    )
    registry.register_command(
        RefreshConfigCacheCommand,
        RefreshConfigCacheCommandHandler(config_service),
    )
    registry.register_command(
        AddDictTypeCommand,
        AddDictTypeCommandHandler(dict_type_service),
    )
    registry.register_command(
        EditDictTypeCommand,
        EditDictTypeCommandHandler(dict_type_service),
    )
    registry.register_command(
        DeleteDictTypeCommand,
        DeleteDictTypeCommandHandler(dict_type_service),
    )
    registry.register_command(
        RefreshDictCacheCommand,
        RefreshDictCacheCommandHandler(dict_type_service),
    )
    registry.register_command(
        AddDictDataCommand,
        AddDictDataCommandHandler(dict_data_service),
    )
    registry.register_command(
        EditDictDataCommand,
        EditDictDataCommandHandler(dict_data_service),
    )
    registry.register_command(
        DeleteDictDataCommand,
        DeleteDictDataCommandHandler(dict_data_service),
    )
    registry.register_command(
        AddMenuCommand,
        AddMenuCommandHandler(menu_service),
    )
    registry.register_command(
        EditMenuCommand,
        EditMenuCommandHandler(menu_service),
    )
    registry.register_command(
        DeleteMenuCommand,
        DeleteMenuCommandHandler(menu_service),
    )
    registry.register_command(
        AddNoticeCommand,
        AddNoticeCommandHandler(notice_service),
    )
    registry.register_command(
        EditNoticeCommand,
        EditNoticeCommandHandler(notice_service),
    )
    registry.register_command(
        DeleteNoticeCommand,
        DeleteNoticeCommandHandler(notice_service),
    )
    registry.register_command(
        AddPostCommand,
        AddPostCommandHandler(post_service),
    )
    registry.register_command(
        EditPostCommand,
        EditPostCommandHandler(post_service),
    )
    registry.register_command(
        DeletePostCommand,
        DeletePostCommandHandler(post_service),
    )
    registry.register_command(
        AddRoleCommand,
        AddRoleCommandHandler(role_service),
    )
    registry.register_command(
        EditRoleCommand,
        EditRoleCommandHandler(role_service),
    )
    registry.register_command(
        AssignRoleDataScopeCommand,
        AssignRoleDataScopeCommandHandler(role_service),
    )
    registry.register_command(
        DeleteRoleCommand,
        DeleteRoleCommandHandler(role_service),
    )
    registry.register_command(
        ChangeRoleStatusCommand,
        ChangeRoleStatusCommandHandler(role_service),
    )
    registry.register_command(
        AddRoleUserCommand,
        AddRoleUserCommandHandler(user_role_service),
    )
    registry.register_command(
        CancelRoleUserCommand,
        CancelRoleUserCommandHandler(user_role_service),
    )
    registry.register_command(BatchCancelRoleUserCommand, BatchCancelRoleUserCommandHandler(user_role_service))
    registry.register_command(
        AddUserCommand,
        AddUserCommandHandler(user_service, dept_service, role_service),
    )
    registry.register_command(
        EditUserCommand,
        EditUserCommandHandler(user_service, dept_service, role_service),
    )
    registry.register_command(
        DeleteUserCommand,
        DeleteUserCommandHandler(user_service),
    )
    registry.register_command(
        ResetUserPasswordCommand,
        ResetUserPasswordCommandHandler(user_service),
    )
    registry.register_command(
        ImportUsersCommand,
        ImportUsersCommandHandler(user_service),
    )
    registry.register_command(
        AssignUserRolesCommand,
        AssignUserRolesCommandHandler(user_role_service),
    )
    registry.register_query(
        GetConfigListQuery,
        GetConfigListQueryHandler(config_service),
    )
    registry.register_query(
        GetConfigDetailQuery,
        GetConfigDetailQueryHandler(config_service),
    )
    registry.register_query(
        GetConfigValueByKeyQuery,
        GetConfigValueByKeyQueryHandler(config_service),
    )
    registry.register_query(
        GetDeptEditOptionQuery,
        GetDeptEditOptionQueryHandler(dept_service),
    )
    registry.register_query(
        GetDeptListQuery,
        GetDeptListQueryHandler(dept_service),
    )
    registry.register_query(
        GetDeptTreeSelectQuery,
        GetDeptTreeSelectQueryHandler(dept_service),
    )
    registry.register_query(
        GetDeptDetailQuery,
        GetDeptDetailQueryHandler(dept_service),
    )
    registry.register_query(
        GetDictTypeListQuery,
        GetDictTypeListQueryHandler(dict_type_service),
    )
    registry.register_query(
        GetDictTypeOptionsQuery,
        GetDictTypeOptionsQueryHandler(dict_type_service),
    )
    registry.register_query(
        GetDictTypeDetailQuery,
        GetDictTypeDetailQueryHandler(dict_type_service),
    )
    registry.register_query(
        GetDictDataByTypeQuery,
        GetDictDataByTypeQueryHandler(dict_data_service),
    )
    registry.register_query(
        GetDictDataListQuery,
        GetDictDataListQueryHandler(dict_data_service),
    )
    registry.register_query(
        GetDictDataDetailQuery,
        GetDictDataDetailQueryHandler(dict_data_service),
    )
    registry.register_query(
        GetMenuTreeQuery,
        GetMenuTreeQueryHandler(menu_service),
    )
    registry.register_query(
        GetRoleMenuTreeQuery,
        GetRoleMenuTreeQueryHandler(menu_service),
    )
    registry.register_query(
        GetMenuListQuery,
        GetMenuListQueryHandler(menu_service),
    )
    registry.register_query(
        GetMenuDetailQuery,
        GetMenuDetailQueryHandler(menu_service),
    )
    registry.register_query(
        GetNoticeListQuery,
        GetNoticeListQueryHandler(notice_service),
    )
    registry.register_query(
        GetNoticeDetailQuery,
        GetNoticeDetailQueryHandler(notice_service),
    )
    registry.register_query(
        GetPostListQuery,
        GetPostListQueryHandler(post_service),
    )
    registry.register_query(
        GetPostDetailQuery,
        GetPostDetailQueryHandler(post_service),
    )
    registry.register_query(
        GetRoleDeptTreeQuery,
        GetRoleDeptTreeQueryHandler(role_service, dept_service),
    )
    registry.register_query(
        GetRoleListQuery,
        GetRoleListQueryHandler(role_service),
    )
    registry.register_query(
        GetRoleDetailQuery,
        GetRoleDetailQueryHandler(role_service),
    )
    registry.register_query(
        GetRoleAllocatedUsersQuery,
        GetRoleAllocatedUsersQueryHandler(role_service),
    )
    registry.register_query(
        GetRoleUnallocatedUsersQuery,
        GetRoleUnallocatedUsersQueryHandler(role_service),
    )
    registry.register_query(
        GetUserDeptTreeQuery,
        GetUserDeptTreeQueryHandler(dept_service),
    )
    registry.register_query(
        GetUserListQuery,
        GetUserListQueryHandler(user_service),
    )
    registry.register_query(
        GetUserProfileQuery,
        GetUserProfileQueryHandler(user_service),
    )
    registry.register_query(
        GetUserDetailQuery,
        GetUserDetailQueryHandler(user_service, role_service, post_service),
    )
    registry.register_query(
        GetUserAuthRoleQuery,
        GetUserAuthRoleQueryHandler(user_service),
    )
    return Mediator(
        registry,
        command_behaviors=build_default_command_behaviors(),
        query_behaviors=build_default_query_behaviors(),
    )
