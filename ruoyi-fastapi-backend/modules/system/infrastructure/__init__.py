"""System context infrastructure implementations."""

from modules.system.infrastructure.audit_log_repository import AuditLogRepository
from modules.system.infrastructure.common_repository import CommonRepository
from modules.system.infrastructure.config_repository import ConfigRepository
from modules.system.infrastructure.dept_repository import DeptRepository
from modules.system.infrastructure.dict_repository import DictDataRepository, DictTypeRepository
from modules.system.infrastructure.log_repository import LoginLogRepository, OperLogRepository
from modules.system.infrastructure.menu_repository import MenuRepository
from modules.system.infrastructure.notice_repository import NoticeRepository
from modules.system.infrastructure.post_repository import PostRepository
from modules.system.infrastructure.role_dept_repository import RoleDeptRepository
from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
from modules.system.infrastructure.role_repository import RoleRepository
from modules.system.infrastructure.user_post_repository import UserPostRepository
from modules.system.infrastructure.user_repository import UserRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository

__all__ = [
    'AuditLogRepository',
    'CommonRepository',
    'ConfigRepository',
    'DeptRepository',
    'DictTypeRepository',
    'DictDataRepository',
    'OperLogRepository',
    'LoginLogRepository',
    'MenuRepository',
    'NoticeRepository',
    'PostRepository',
    'RoleDeptRepository',
    'RoleMenuRepository',
    'RoleRepository',
    'UserPostRepository',
    'UserRepository',
    'UserRoleRepository',
]
