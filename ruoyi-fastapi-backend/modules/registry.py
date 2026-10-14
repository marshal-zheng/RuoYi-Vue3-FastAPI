"""Explicit module registry for vertical-slice loading."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import TYPE_CHECKING, Any

from fastapi import Depends

from module_generator.controller.gen_controller import genController
from modules.identity.api.captcha_controller import captchaController
from modules.identity.api.login_controller import loginController
from modules.identity.api.security_controller import securityController
from modules.project.api.project_controller import projectController
from modules.project.api.project_version_controller import projectVersionController
from modules.scheduler.api.job_controller import jobController
from modules.system.api.audit_controller import auditController
from modules.system.api.cache_controller import cache_router
from modules.system.api.common_controller import commonController
from modules.system.api.config_controller import configController
from modules.system.api.dept_controller import deptController
from modules.system.api.dev_menu_sync_controller import devMenuSyncController
from modules.system.api.dict_controller import dictController
from modules.system.api.event_controller import eventController
from modules.system.api.log_controller import logController
from modules.system.api.menu_controller import menuController
from modules.system.api.notice_controller import noticeController
from modules.system.api.online_controller import onlineController
from modules.system.api.post_controller import postController
from modules.system.api.resilience_controller import resilienceController
from modules.system.api.role_controller import roleController
from modules.system.api.server_controller import serverController
from modules.system.api.user_controller import userController
from modules.system.application.services.capability_gate_service import require_capability_enabled
from modules.system.runtime import is_dev_managed_data_hot_reconcile_enabled
from utils.log_util import logger

if TYPE_CHECKING:
    from container import AppContainer


ContainerExtension = Callable[['AppContainer'], Any]


@dataclass(frozen=True)
class RouterRegistration:
    """Router registration metadata."""

    router: Any
    tags: tuple[str, ...] = field(default_factory=tuple)
    capability_module_key: str | None = None


@dataclass(frozen=True)
class ModuleRegistration:
    """Module registration metadata."""

    name: str
    version: str
    routers: tuple[RouterRegistration, ...]
    container_extensions: tuple[ContainerExtension, ...] = field(default_factory=tuple)

    @property
    def route_prefixes(self) -> tuple[str, ...]:
        prefixes = []
        for registration in self.routers:
            prefix = registration.router.prefix or '/'
            if prefix not in prefixes:
                prefixes.append(prefix)
        return tuple(prefixes)


@dataclass(frozen=True)
class LoadedModule:
    """Runtime-loaded module snapshot for audit logs."""

    name: str
    version: str
    route_prefixes: tuple[str, ...]
    router_count: int


def _load_optional_router(module_path: str, router_name: str) -> Any | None:
    try:
        module = import_module(module_path)
        return getattr(module, router_name)
    except Exception as exc:  # pragma: no cover - depends on optional module readiness
        logger.warning(
            'Skip optional module router {}.{} due to import error: {}',
            module_path,
            router_name,
            exc,
        )
        return None


protocol_router = _load_optional_router('module_admin.controller.protocol_controller', 'protocolController')
simulation_router = _load_optional_router('module_admin.controller.simulation_controller', 'simulationController')
device_category_router = _load_optional_router(
    'module_admin.controller.device_category_controller', 'device_category_router'
)
device_router = _load_optional_router('module_admin.controller.device_controller', 'deviceController')


def _should_register_dev_menu_router() -> bool:
    return is_dev_managed_data_hot_reconcile_enabled()


def _build_system_routers() -> tuple[RouterRegistration, ...]:
    routers: list[RouterRegistration] = [
        RouterRegistration(router=menuController, tags=('系统管理-菜单管理',), capability_module_key='platform'),
        RouterRegistration(router=deptController, tags=('系统管理-部门管理',), capability_module_key='platform'),
        RouterRegistration(router=postController, tags=('系统管理-岗位管理',), capability_module_key='platform'),
        RouterRegistration(router=dictController, tags=('系统管理-字典管理',), capability_module_key='platform'),
        RouterRegistration(router=configController, tags=('系统管理-参数管理',), capability_module_key='platform'),
        RouterRegistration(router=noticeController, tags=('系统管理-通知公告管理',), capability_module_key='platform'),
        RouterRegistration(router=logController, tags=('系统管理-日志管理',), capability_module_key='platform'),
        RouterRegistration(router=onlineController, tags=('系统监控-在线用户',), capability_module_key='platform'),
        RouterRegistration(router=serverController, tags=('系统监控-菜单管理',), capability_module_key='platform'),
        RouterRegistration(router=cache_router, tags=('系统监控-缓存监控',), capability_module_key='platform'),
        RouterRegistration(router=resilienceController, tags=('系统监控-弹性治理',), capability_module_key='platform'),
        RouterRegistration(router=auditController, tags=('系统监控-审计日志',), capability_module_key='platform'),
        RouterRegistration(router=eventController, tags=('系统监控-事件治理',), capability_module_key='platform'),
    ]
    if _should_register_dev_menu_router():
        routers.append(RouterRegistration(router=devMenuSyncController, tags=('系统管理-开发态菜单热同步',)))
    routers.append(RouterRegistration(router=commonController, tags=('通用模块',)))
    return tuple(routers)


_module_registry: list[ModuleRegistration] = [
    ModuleRegistration(
        name='identity',
        version='v1',
        routers=(
            RouterRegistration(router=loginController, tags=('登录模块',)),
            RouterRegistration(router=securityController, tags=('安全鉴权模块',)),
            RouterRegistration(router=captchaController, tags=('验证码模块',)),
            RouterRegistration(router=userController, tags=('系统管理-用户管理',), capability_module_key='platform'),
            RouterRegistration(router=roleController, tags=('系统管理-角色管理',), capability_module_key='platform'),
        ),
    ),
    ModuleRegistration(
        name='system',
        version='v1',
        routers=_build_system_routers(),
    ),
    ModuleRegistration(
        name='project',
        version='v1',
        routers=(
            RouterRegistration(router=projectController, tags=('工程管理',), capability_module_key='platform'),
            RouterRegistration(
                router=projectVersionController, tags=('工程管理-版本管理',), capability_module_key='platform'
            ),
        ),
    ),
]

if protocol_router is not None:
    _module_registry.append(
        ModuleRegistration(
            name='protocol',
            version='v1',
            routers=(RouterRegistration(router=protocol_router, tags=('协议管理',)),),
        )
    )
if simulation_router is not None:
    _module_registry.append(
        ModuleRegistration(
            name='simulation',
            version='v1',
            routers=(RouterRegistration(router=simulation_router, tags=('仿真管理',)),),
        )
    )
if device_category_router is not None and device_router is not None:
    _module_registry.append(
        ModuleRegistration(
            name='device',
            version='v1',
            routers=(
                RouterRegistration(router=device_category_router, tags=('设备中心-分类管理',)),
                RouterRegistration(router=device_router, tags=('设备中心-设备管理',)),
            ),
        )
    )

_module_registry.extend(
    (
        ModuleRegistration(
            name='scheduler',
            version='v1',
            routers=(
                RouterRegistration(router=jobController, tags=('系统监控-定时任务',), capability_module_key='platform'),
            ),
        ),
        ModuleRegistration(
            name='codegen',
            version='v1',
            routers=(RouterRegistration(router=genController, tags=('代码生成',), capability_module_key='platform'),),
        ),
    )
)

MODULE_REGISTRY: tuple[ModuleRegistration, ...] = tuple(_module_registry)


def get_module_registry() -> tuple[ModuleRegistration, ...]:
    """Return immutable module registry snapshot."""
    return MODULE_REGISTRY


def register_modules(app: Any, registry: Sequence[ModuleRegistration] | None = None) -> tuple[LoadedModule, ...]:
    """Register routers from explicit module registry."""
    module_registry = tuple(registry or MODULE_REGISTRY)
    loaded_modules: list[LoadedModule] = []
    for module in module_registry:
        for registration in module.routers:
            dependencies = []
            if registration.capability_module_key:
                dependencies.append(Depends(require_capability_enabled(registration.capability_module_key)))
            app.include_router(router=registration.router, tags=list(registration.tags), dependencies=dependencies)
        loaded_modules.append(
            LoadedModule(
                name=module.name,
                version=module.version,
                route_prefixes=module.route_prefixes,
                router_count=len(module.routers),
            )
        )
    return tuple(loaded_modules)


async def initialize_module_extensions(
    container: AppContainer,
    registry: Sequence[ModuleRegistration] | None = None,
) -> None:
    """Initialize module container extensions after app container is ready."""
    module_registry = tuple(registry or MODULE_REGISTRY)
    for module in module_registry:
        for extension in module.container_extensions:
            result = extension(container)
            if inspect.isawaitable(result):
                await result


def log_loaded_modules(loaded_modules: Iterable[LoadedModule]) -> None:
    """Log loaded modules with route prefixes and versions."""
    for module in loaded_modules:
        logger.info(
            'Loaded module `{}` (version={}, prefixes={}, routers={})',
            module.name,
            module.version,
            ','.join(module.route_prefixes),
            module.router_count,
        )
