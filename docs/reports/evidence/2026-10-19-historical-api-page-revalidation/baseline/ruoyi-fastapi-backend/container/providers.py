"""Container provider factories."""

from __future__ import annotations

import ast
import inspect
from importlib import import_module
from pathlib import Path
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIRS = (
    BACKEND_ROOT / 'module_admin' / 'service',
    BACKEND_ROOT / 'module_generator' / 'service',
    BACKEND_ROOT / 'modules' / 'identity' / 'application' / 'services',
    BACKEND_ROOT / 'modules' / 'project' / 'application' / 'services',
    BACKEND_ROOT / 'modules' / 'scheduler' / 'application',
    BACKEND_ROOT / 'modules' / 'system' / 'application' / 'services',
)


def _load_service(module_path: str, class_name: str):
    module = import_module(module_path)
    return getattr(module, class_name)


def _camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def _instantiate_service(service_cls: type, session: AsyncSession | None) -> Any:
    init_signature = inspect.signature(service_cls.__init__)
    params = [param for param in init_signature.parameters.values() if param.name != 'self']
    if not params:
        return service_cls()

    if session is not None:
        try:
            return service_cls(session)
        except TypeError:
            return service_cls()

    try:
        return service_cls()
    except TypeError:
        return service_cls(None)


def _make_service_factory(module_path: str, class_name: str):
    def _factory(session: AsyncSession | None) -> Any:
        service_cls = _load_service(module_path, class_name)
        return _instantiate_service(service_cls, session)

    return _factory


def _discover_service_providers() -> dict[str, Any]:
    providers: dict[str, Any] = {}
    for service_dir in SERVICE_DIRS:
        if not service_dir.exists():
            continue
        for file_path in sorted(service_dir.rglob('*.py')):
            module_path = file_path.relative_to(BACKEND_ROOT).with_suffix('').as_posix().replace('/', '.')
            tree = ast.parse(file_path.read_text(encoding='utf-8'))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                if not node.name.endswith('Service'):
                    continue
                provider_name = _camel_to_snake(node.name)
                providers[provider_name] = _make_service_factory(module_path, node.name)
    return providers


def _project_version_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('project_version_service requires request session')

    from modules.project.infrastructure.project_topology_repository import ProjectTopologyRepository
    from modules.project.infrastructure.project_version_repository import ProjectVersionRepository
    from modules.project.application.services.project_version_service import ProjectVersionService

    return ProjectVersionService(
        version_repo=ProjectVersionRepository(session),
        topology_repo=ProjectTopologyRepository(session),
    )


def _project_topology_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('project_topology_service requires request session')

    from modules.project.infrastructure.project_topology_repository import ProjectTopologyRepository
    from modules.project.infrastructure.project_repository import ProjectRepository  # noqa: PLC0415
    from modules.project.infrastructure.project_version_repository import ProjectVersionRepository  # noqa: PLC0415
    from modules.project.application.services.project_topology_service import ProjectTopologyService

    return ProjectTopologyService(
        topology_repo=ProjectTopologyRepository(session),
        project_repo=ProjectRepository(session),
        version_repo=ProjectVersionRepository(session),
    )


def _project_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('project_service requires request session')

    from module_admin.repository import (
        DeviceInterfaceRepository,
        DeviceRepository,
    )
    from modules.project.infrastructure.project_repository import ProjectRepository
    from modules.project.infrastructure.project_topology_repository import ProjectTopologyRepository
    from modules.project.infrastructure.project_version_repository import ProjectVersionRepository
    from modules.project.application.services.project_service import ProjectService

    return ProjectService(
        project_repo=ProjectRepository(session),
        version_repo=ProjectVersionRepository(session),
        topology_repo=ProjectTopologyRepository(session),
        device_repo=DeviceRepository(session),
        interface_repo=DeviceInterfaceRepository(session),
        query_db=session,
    )


def _protocol_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('protocol_service requires request session')

    from module_admin.repository import ProtocolRepository
    from module_admin.service.protocol_service import ProtocolService

    return ProtocolService(
        protocol_repo=ProtocolRepository(session),
        query_db=session,
    )


def _config_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('config_service requires request session')

    from modules.system.infrastructure.config_repository import ConfigRepository
    from modules.system.application.services.config_service import ConfigService

    return ConfigService(
        config_repo=ConfigRepository(session),
        query_db=session,
    )


def _dept_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('dept_service requires request session')

    from modules.system.infrastructure.dept_repository import DeptRepository
    from modules.system.application.services.dept_service import DeptService

    return DeptService(
        dept_repo=DeptRepository(session),
        query_db=session,
    )


def _common_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('common_service requires request session')

    from modules.system.infrastructure.common_repository import CommonRepository
    from modules.system.application.services.common_service import CommonService

    return CommonService(common_repo=CommonRepository(session))


def _menu_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('menu_service requires request session')

    from modules.system.infrastructure.menu_repository import MenuRepository
    from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
    from modules.system.infrastructure.role_repository import RoleRepository
    from modules.system.application.services.menu_service import MenuService

    return MenuService(
        menu_repo=MenuRepository(session),
        role_repo=RoleRepository(session),
        role_menu_repo=RoleMenuRepository(session),
        query_db=session,
    )


def _notice_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('notice_service requires request session')

    from modules.system.infrastructure.notice_repository import NoticeRepository
    from modules.system.application.services.notice_service import NoticeService

    return NoticeService(
        notice_repo=NoticeRepository(session),
        query_db=session,
    )


def _post_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('post_service requires request session')

    from modules.system.infrastructure.post_repository import PostRepository
    from modules.system.application.services.post_service import PostService

    return PostService(
        post_repo=PostRepository(session),
        query_db=session,
    )


def _role_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('role_service requires request session')

    from modules.system.infrastructure.role_dept_repository import RoleDeptRepository
    from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
    from modules.system.infrastructure.role_repository import RoleRepository
    from modules.system.infrastructure.user_repository import UserRepository
    from modules.system.application.services.role_service import RoleService

    return RoleService(
        role_repo=RoleRepository(session),
        role_menu_repo=RoleMenuRepository(session),
        role_dept_repo=RoleDeptRepository(session),
        user_repo=UserRepository(session),
        query_db=session,
    )


def _device_category_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('device_category_service requires request session')

    from module_admin.repository import DeviceCategoryRepository, DeviceRepository
    from module_admin.service.device_category_service import DeviceCategoryService

    return DeviceCategoryService(
        category_repo=DeviceCategoryRepository(session),
        device_repo=DeviceRepository(session),
        query_db=session,
    )


def _device_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('device_service requires request session')

    from module_admin.repository import DeviceCategoryRepository, DeviceInterfaceRepository, DeviceRepository
    from module_admin.service.device_service import DeviceService

    return DeviceService(
        device_repo=DeviceRepository(session),
        interface_repo=DeviceInterfaceRepository(session),
        category_repo=DeviceCategoryRepository(session),
        query_db=session,
    )


def _dict_data_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('dict_data_service requires request session')

    from modules.system.infrastructure.dict_repository import DictDataRepository, DictTypeRepository
    from modules.system.application.services.dict_data_service import DictDataService

    return DictDataService(
        dict_type_repo=DictTypeRepository(session),
        dict_data_repo=DictDataRepository(session),
    )


def _dict_type_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('dict_type_service requires request session')

    from modules.system.infrastructure.dict_repository import DictDataRepository, DictTypeRepository
    from modules.system.application.services.dict_type_service import DictTypeService

    return DictTypeService(
        dict_type_repo=DictTypeRepository(session),
        dict_data_repo=DictDataRepository(session),
        dict_data_service=_dict_data_service_factory(session),
    )


def _user_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('user_service requires request session')

    from modules.system.application.services.user_service import UserService

    return UserService(
        query_db=session,
        config_service=_config_service_factory(session),
        dept_service=_dept_service_factory(session),
    )


def _login_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('login_service requires request session')

    from modules.identity.infrastructure.login_repository import LoginRepository
    from modules.system.infrastructure.user_repository import UserRepository
    from modules.identity.application.services.login_service import LoginService

    return LoginService(
        query_db=session,
        login_repo=LoginRepository(session),
        user_repo=UserRepository(session),
        user_service=_user_service_factory(session),
    )


def _job_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('job_service requires request session')

    from modules.scheduler.infrastructure.job_repository import JobRepository
    from modules.scheduler.application.job_service import JobService

    return JobService(
        job_repo=JobRepository(session),
        query_db=session,
    )


def _gen_table_column_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('gen_table_column_service requires request session')

    from module_generator.repository import GenTableColumnRepository
    from module_generator.service.gen_service import GenTableColumnService

    return GenTableColumnService(
        column_repo=GenTableColumnRepository(session),
    )


def _gen_table_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('gen_table_service requires request session')

    from module_generator.repository import GenTableColumnRepository, GenTableRepository
    from module_generator.service.gen_service import GenTableService

    return GenTableService(
        table_repo=GenTableRepository(session),
        column_repo=GenTableColumnRepository(session),
        query_db=session,
    )


def _job_log_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('job_log_service requires request session')

    from modules.scheduler.infrastructure.job_repository import JobLogRepository
    from modules.scheduler.application.job_log_service import JobLogService

    return JobLogService(
        job_log_repo=JobLogRepository(session),
        query_db=session,
    )


def _operation_log_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('operation_log_service requires request session')

    from modules.system.infrastructure.log_repository import OperLogRepository
    from modules.system.application.services.log_service import OperationLogService

    return OperationLogService(
        oper_log_repo=OperLogRepository(session),
        query_db=session,
    )


def _login_log_service_factory(session: AsyncSession | None) -> Any:
    if session is None:
        raise RuntimeError('login_log_service requires request session')

    from modules.system.infrastructure.log_repository import LoginLogRepository
    from modules.system.application.services.log_service import LoginLogService

    return LoginLogService(
        login_log_repo=LoginLogRepository(session),
        query_db=session,
    )


SERVICE_FACTORY_REGISTRY = _discover_service_providers()
SERVICE_FACTORY_REGISTRY.update(
    {
        'common_service': _common_service_factory,
        'config_service': _config_service_factory,
        'dept_service': _dept_service_factory,
        'device_category_service': _device_category_service_factory,
        'device_service': _device_service_factory,
        'dict_data_service': _dict_data_service_factory,
        'dict_type_service': _dict_type_service_factory,
        'gen_table_column_service': _gen_table_column_service_factory,
        'gen_table_service': _gen_table_service_factory,
        'job_log_service': _job_log_service_factory,
        'job_service': _job_service_factory,
        'login_log_service': _login_log_service_factory,
        'login_service': _login_service_factory,
        'menu_service': _menu_service_factory,
        'notice_service': _notice_service_factory,
        'operation_log_service': _operation_log_service_factory,
        'post_service': _post_service_factory,
        'protocol_service': _protocol_service_factory,
        'project_service': _project_service_factory,
        'project_topology_service': _project_topology_service_factory,
        'project_version_service': _project_version_service_factory,
        'role_service': _role_service_factory,
        'user_service': _user_service_factory,
    }
)
