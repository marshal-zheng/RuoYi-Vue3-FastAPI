"""System runtime utilities."""

from __future__ import annotations

from typing import Any

__all__ = [
    'DEFAULT_MANAGED_DATA_MODULES_DIR',
    'DEFAULT_MENU_REGISTRY_FILE',
    'DEFAULT_MODULE_MANIFEST_GLOB',
    'DevManagedDataHotReconcileRuntime',
    'DevMenuEventBroker',
    'DevMenuReconcileService',
    'DevMenuSignatureService',
    'DevMenuSseEvent',
    'DevMenuSyncRuntime',
    'HotReconcileCallbackResult',
    'HotReconcileRuntimeState',
    'ManifestSnapshot',
    'ManifestSnapshotDiff',
    'ManifestSnapshotEntry',
    'MenuRegistryLoader',
    'SseSubscriber',
    'SyncReport',
    'is_dev_managed_data_hot_reconcile_enabled',
    'is_dev_menu_sync_enabled',
]


def __getattr__(name: str) -> Any:
    if name in {'DevMenuEventBroker', 'DevMenuSseEvent', 'SseSubscriber'}:
        from modules.system.runtime.dev_menu_event_broker import DevMenuEventBroker, DevMenuSseEvent, SseSubscriber

        return {
            'DevMenuEventBroker': DevMenuEventBroker,
            'DevMenuSseEvent': DevMenuSseEvent,
            'SseSubscriber': SseSubscriber,
        }[name]

    if name in {'DevMenuReconcileService', 'SyncReport'}:
        from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService, SyncReport

        return {'DevMenuReconcileService': DevMenuReconcileService, 'SyncReport': SyncReport}[name]

    if name == 'DevMenuSignatureService':
        from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService

        return DevMenuSignatureService

    if name in {
        'DEFAULT_MANAGED_DATA_MODULES_DIR',
        'DEFAULT_MODULE_MANIFEST_GLOB',
        'DevManagedDataHotReconcileRuntime',
        'DevMenuSyncRuntime',
        'HotReconcileCallbackResult',
        'HotReconcileRuntimeState',
        'ManifestSnapshot',
        'ManifestSnapshotDiff',
        'ManifestSnapshotEntry',
        'is_dev_managed_data_hot_reconcile_enabled',
        'is_dev_menu_sync_enabled',
    }:
        from modules.system.runtime.dev_menu_sync_runtime import (
            DEFAULT_MANAGED_DATA_MODULES_DIR,
            DEFAULT_MODULE_MANIFEST_GLOB,
            DevManagedDataHotReconcileRuntime,
            DevMenuSyncRuntime,
            HotReconcileCallbackResult,
            HotReconcileRuntimeState,
            ManifestSnapshot,
            ManifestSnapshotDiff,
            ManifestSnapshotEntry,
            is_dev_managed_data_hot_reconcile_enabled,
            is_dev_menu_sync_enabled,
        )

        return {
            'DEFAULT_MANAGED_DATA_MODULES_DIR': DEFAULT_MANAGED_DATA_MODULES_DIR,
            'DEFAULT_MODULE_MANIFEST_GLOB': DEFAULT_MODULE_MANIFEST_GLOB,
            'DevManagedDataHotReconcileRuntime': DevManagedDataHotReconcileRuntime,
            'DevMenuSyncRuntime': DevMenuSyncRuntime,
            'HotReconcileCallbackResult': HotReconcileCallbackResult,
            'HotReconcileRuntimeState': HotReconcileRuntimeState,
            'ManifestSnapshot': ManifestSnapshot,
            'ManifestSnapshotDiff': ManifestSnapshotDiff,
            'ManifestSnapshotEntry': ManifestSnapshotEntry,
            'is_dev_managed_data_hot_reconcile_enabled': is_dev_managed_data_hot_reconcile_enabled,
            'is_dev_menu_sync_enabled': is_dev_menu_sync_enabled,
        }[name]

    if name in {'DEFAULT_MENU_REGISTRY_FILE', 'MenuRegistryLoader'}:
        from modules.system.runtime.menu_registry_loader import DEFAULT_MENU_REGISTRY_FILE, MenuRegistryLoader

        return {
            'DEFAULT_MENU_REGISTRY_FILE': DEFAULT_MENU_REGISTRY_FILE,
            'MenuRegistryLoader': MenuRegistryLoader,
        }[name]

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
