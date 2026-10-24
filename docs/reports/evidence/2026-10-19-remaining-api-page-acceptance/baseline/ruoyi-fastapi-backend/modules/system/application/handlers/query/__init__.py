"""Query handlers for system context."""

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

__all__ = [
    'GetConfigDetailQueryHandler',
    'GetConfigListQueryHandler',
    'GetConfigValueByKeyQueryHandler',
    'GetDeptDetailQueryHandler',
    'GetDeptEditOptionQueryHandler',
    'GetDeptListQueryHandler',
    'GetDeptTreeSelectQueryHandler',
    'GetDictDataByTypeQueryHandler',
    'GetDictDataDetailQueryHandler',
    'GetDictDataListQueryHandler',
    'GetDictTypeDetailQueryHandler',
    'GetDictTypeListQueryHandler',
    'GetDictTypeOptionsQueryHandler',
    'GetMenuDetailQueryHandler',
    'GetMenuListQueryHandler',
    'GetMenuTreeQueryHandler',
    'GetNoticeDetailQueryHandler',
    'GetNoticeListQueryHandler',
    'GetPostDetailQueryHandler',
    'GetPostListQueryHandler',
    'GetRoleAllocatedUsersQueryHandler',
    'GetRoleDeptTreeQueryHandler',
    'GetRoleDetailQueryHandler',
    'GetRoleListQueryHandler',
    'GetRoleMenuTreeQueryHandler',
    'GetRoleUnallocatedUsersQueryHandler',
    'GetUserAuthRoleQueryHandler',
    'GetUserDeptTreeQueryHandler',
    'GetUserDetailQueryHandler',
    'GetUserListQueryHandler',
    'GetUserProfileQueryHandler',
]
