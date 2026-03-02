"""System runtime utilities."""

from __future__ import annotations

from typing import Any

__all__ = [
    'DevMenuReconcileService',
    'DevMenuSignatureService',
    'DevMenuSyncRuntime',
    'DEFAULT_MENU_REGISTRY_FILE',
    'MenuRegistryLoader',
    'SyncReport',
    'is_dev_menu_sync_enabled',
]


def __getattr__(name: str) -> Any:
    if name in {'DevMenuReconcileService', 'SyncReport'}:
        from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService, SyncReport

        return {'DevMenuReconcileService': DevMenuReconcileService, 'SyncReport': SyncReport}[name]

    if name == 'DevMenuSignatureService':
        from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService

        return DevMenuSignatureService

    if name in {'DevMenuSyncRuntime', 'is_dev_menu_sync_enabled'}:
        from modules.system.runtime.dev_menu_sync_runtime import DevMenuSyncRuntime, is_dev_menu_sync_enabled

        return {'DevMenuSyncRuntime': DevMenuSyncRuntime, 'is_dev_menu_sync_enabled': is_dev_menu_sync_enabled}[name]

    if name in {'DEFAULT_MENU_REGISTRY_FILE', 'MenuRegistryLoader'}:
        from modules.system.runtime.menu_registry_loader import DEFAULT_MENU_REGISTRY_FILE, MenuRegistryLoader

        return {
            'DEFAULT_MENU_REGISTRY_FILE': DEFAULT_MENU_REGISTRY_FILE,
            'MenuRegistryLoader': MenuRegistryLoader,
        }[name]

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
