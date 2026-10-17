"""Command handlers for system context."""

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

__all__ = [
    'AddConfigCommandHandler',
    'AddDeptCommandHandler',
    'AddDictDataCommandHandler',
    'AddDictTypeCommandHandler',
    'AddMenuCommandHandler',
    'AddNoticeCommandHandler',
    'AddPostCommandHandler',
    'AddRoleCommandHandler',
    'AddRoleUserCommandHandler',
    'AddUserCommandHandler',
    'AssignRoleDataScopeCommandHandler',
    'AssignUserRolesCommandHandler',
    'BatchCancelRoleUserCommandHandler',
    'CancelRoleUserCommandHandler',
    'ChangeRoleStatusCommandHandler',
    'DeleteConfigCommandHandler',
    'DeleteDeptCommandHandler',
    'DeleteDictDataCommandHandler',
    'DeleteDictTypeCommandHandler',
    'DeleteMenuCommandHandler',
    'DeleteNoticeCommandHandler',
    'DeletePostCommandHandler',
    'DeleteRoleCommandHandler',
    'DeleteUserCommandHandler',
    'EditConfigCommandHandler',
    'EditDeptCommandHandler',
    'EditDictDataCommandHandler',
    'EditDictTypeCommandHandler',
    'EditMenuCommandHandler',
    'EditNoticeCommandHandler',
    'EditPostCommandHandler',
    'EditRoleCommandHandler',
    'EditUserCommandHandler',
    'ImportUsersCommandHandler',
    'RefreshConfigCacheCommandHandler',
    'RefreshDictCacheCommandHandler',
    'ResetUserPasswordCommandHandler',
]
