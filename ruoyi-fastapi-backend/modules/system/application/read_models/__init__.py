"""Read models for system context query handlers."""

from modules.system.application.read_models.config_read_models import (
    ConfigDetailReadModel,
    ConfigListItemReadModel,
    ConfigPageReadModel,
    ConfigValueReadModel,
)
from modules.system.application.read_models.dept_read_models import (
    DeptDetailReadModel,
    DeptItemReadModel,
    DeptTreeNodeReadModel,
)
from modules.system.application.read_models.dict_read_models import (
    DictDataDetailReadModel,
    DictDataItemReadModel,
    DictDataPageReadModel,
    DictTypeDetailReadModel,
    DictTypeItemReadModel,
    DictTypePageReadModel,
)
from modules.system.application.read_models.menu_read_models import (
    MenuItemReadModel,
    MenuTreeNodeReadModel,
    RoleMenuTreeReadModel,
)
from modules.system.application.read_models.notice_read_models import (
    NoticeDetailReadModel,
    NoticeItemReadModel,
    NoticePageReadModel,
)
from modules.system.application.read_models.post_read_models import (
    PostDetailReadModel,
    PostItemReadModel,
    PostPageReadModel,
)
from modules.system.application.read_models.role_read_models import (
    RoleDeptTreeReadModel,
    RoleDetailReadModel,
    RoleItemReadModel,
    RolePageReadModel,
    RoleUserItemReadModel,
    RoleUserPageReadModel,
)
from modules.system.application.read_models.user_read_models import (
    UserAllocatedRoleReadModel,
    UserDetailReadModel,
    UserInfoReadModel,
    UserListItemReadModel,
    UserPageReadModel,
    UserProfileReadModel,
    UserRoleResponseReadModel,
)

__all__ = [
    'ConfigDetailReadModel',
    'ConfigListItemReadModel',
    'ConfigPageReadModel',
    'ConfigValueReadModel',
    'DeptDetailReadModel',
    'DeptItemReadModel',
    'DeptTreeNodeReadModel',
    'DictDataDetailReadModel',
    'DictDataItemReadModel',
    'DictDataPageReadModel',
    'DictTypeDetailReadModel',
    'DictTypeItemReadModel',
    'DictTypePageReadModel',
    'MenuItemReadModel',
    'MenuTreeNodeReadModel',
    'NoticeDetailReadModel',
    'NoticeItemReadModel',
    'NoticePageReadModel',
    'PostDetailReadModel',
    'PostItemReadModel',
    'PostPageReadModel',
    'RoleDeptTreeReadModel',
    'RoleDetailReadModel',
    'RoleItemReadModel',
    'RoleMenuTreeReadModel',
    'RolePageReadModel',
    'RoleUserItemReadModel',
    'RoleUserPageReadModel',
    'UserAllocatedRoleReadModel',
    'UserDetailReadModel',
    'UserInfoReadModel',
    'UserListItemReadModel',
    'UserPageReadModel',
    'UserProfileReadModel',
    'UserRoleResponseReadModel',
]
