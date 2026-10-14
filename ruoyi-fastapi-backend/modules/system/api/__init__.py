"""System context HTTP/API adapters."""

from modules.system.api.audit_controller import auditController
from modules.system.api.cache_controller import cache_router
from modules.system.api.common_controller import commonController
from modules.system.api.config_controller import configController
from modules.system.api.dept_controller import deptController
from modules.system.api.dev_menu_sync_controller import devMenuSyncController
from modules.system.api.dict_controller import dictController
from modules.system.api.log_controller import logController
from modules.system.api.menu_controller import menuController
from modules.system.api.notice_controller import noticeController
from modules.system.api.online_controller import onlineController
from modules.system.api.post_controller import postController
from modules.system.api.resilience_controller import resilienceController
from modules.system.api.role_controller import roleController
from modules.system.api.server_controller import serverController
from modules.system.api.user_controller import userController

__all__ = [
    'auditController',
    'cache_router',
    'commonController',
    'configController',
    'deptController',
    'devMenuSyncController',
    'dictController',
    'logController',
    'menuController',
    'noticeController',
    'onlineController',
    'postController',
    'resilienceController',
    'roleController',
    'serverController',
    'userController',
]
