from __future__ import annotations

import pytest
from fastapi import APIRouter, FastAPI

import modules.registry as registry_module
from modules.registry import (
    ModuleRegistration,
    RouterRegistration,
    _build_system_routers,
    _should_register_dev_menu_router,
    get_module_registry,
    initialize_module_extensions,
    register_modules,
)


def test_module_registry_contains_required_contexts() -> None:
    required_contexts = {
        'identity',
        'project',
        'simulation',
        'device',
        'protocol',
        'system',
        'codegen',
        'scheduler',
    }
    registry = get_module_registry()
    context_names = {module.name for module in registry}

    assert required_contexts.issubset(context_names)



def test_register_modules_returns_loaded_metadata() -> None:
    app = FastAPI()

    loaded_modules = register_modules(app, get_module_registry())

    assert len(loaded_modules) >= 8
    loaded_by_name = {module.name: module for module in loaded_modules}
    assert loaded_by_name['identity'].version == 'v1'
    assert '/system/user' in loaded_by_name['identity'].route_prefixes


@pytest.mark.asyncio
async def test_initialize_module_extensions_supports_sync_and_async() -> None:
    sync_called = False
    async_called = False

    def sync_extension(_container):
        nonlocal sync_called
        sync_called = True

    async def async_extension(_container):
        nonlocal async_called
        async_called = True

    module = ModuleRegistration(
        name='test_module',
        version='v1',
        routers=(RouterRegistration(router=APIRouter(prefix='/test'), tags=('test',)),),
        container_extensions=(sync_extension, async_extension),
    )

    await initialize_module_extensions(object(), registry=(module,))

    assert sync_called is True
    assert async_called is True


def test_dev_menu_router_registration_guard(monkeypatch) -> None:
    monkeypatch.setattr(registry_module, 'is_dev_managed_data_hot_reconcile_enabled', lambda: False)
    assert _should_register_dev_menu_router() is False

    monkeypatch.setattr(registry_module, 'is_dev_managed_data_hot_reconcile_enabled', lambda: True)
    assert _should_register_dev_menu_router() is True


def test_build_system_routers_excludes_dev_menu_router_when_guard_off(monkeypatch) -> None:
    monkeypatch.setattr(registry_module, 'is_dev_managed_data_hot_reconcile_enabled', lambda: False)
    routers = _build_system_routers()
    assert '/dev/menu' not in {router.router.prefix for router in routers}
