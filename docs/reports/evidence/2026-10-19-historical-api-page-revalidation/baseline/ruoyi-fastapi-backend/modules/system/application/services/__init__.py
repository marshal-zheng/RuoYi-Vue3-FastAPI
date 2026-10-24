"""System context application services and dependency helpers."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from modules.system.application.services.config_service import ConfigService
from modules.system.application.services.dept_service import DeptService
from modules.system.application.services.dict_data_service import DictDataService
from modules.system.application.services.dict_type_service import DictTypeService
from modules.system.application.services.menu_service import MenuService
from modules.system.application.services.notice_service import NoticeService
from modules.system.application.services.post_service import PostService
from modules.system.application.services.role_service import RoleService
from modules.system.application.services.user_service import UserService
from utils.excel_util import ExcelUtil


def get_dict_type_service(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
) -> DictTypeService:
    from container.wiring import get_app_container

    container = get_app_container(request)
    return container.resolve_service('dict_type_service', query_db)


def get_dict_data_service(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
) -> DictDataService:
    from container.wiring import get_app_container

    container = get_app_container(request)
    return container.resolve_service('dict_data_service', query_db)


__all__ = [
    'ConfigService',
    'DeptService',
    'DictTypeService',
    'DictDataService',
    'MenuService',
    'NoticeService',
    'PostService',
    'RoleService',
    'UserService',
    'ExcelUtil',
    'get_dict_type_service',
    'get_dict_data_service',
]
