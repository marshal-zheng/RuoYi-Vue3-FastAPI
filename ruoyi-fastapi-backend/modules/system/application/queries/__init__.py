"""Query models for system context read operations."""

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
from modules.system.application.queries.notice_queries import (
    GetNoticeDetailQuery,
    GetNoticeListQuery,
)
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

__all__ = [
    'GetConfigDetailQuery',
    'GetConfigListQuery',
    'GetConfigValueByKeyQuery',
    'GetDeptDetailQuery',
    'GetDeptEditOptionQuery',
    'GetDeptListQuery',
    'GetDeptTreeSelectQuery',
    'GetDictDataByTypeQuery',
    'GetDictDataDetailQuery',
    'GetDictDataListQuery',
    'GetDictTypeDetailQuery',
    'GetDictTypeListQuery',
    'GetDictTypeOptionsQuery',
    'GetMenuDetailQuery',
    'GetMenuListQuery',
    'GetMenuTreeQuery',
    'GetNoticeDetailQuery',
    'GetNoticeListQuery',
    'GetPostDetailQuery',
    'GetPostListQuery',
    'GetRoleAllocatedUsersQuery',
    'GetRoleDeptTreeQuery',
    'GetRoleDetailQuery',
    'GetRoleListQuery',
    'GetRoleMenuTreeQuery',
    'GetRoleUnallocatedUsersQuery',
    'GetUserAuthRoleQuery',
    'GetUserDeptTreeQuery',
    'GetUserDetailQuery',
    'GetUserListQuery',
    'GetUserProfileQuery',
]
