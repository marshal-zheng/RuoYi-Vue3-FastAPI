"""Process-wide wiring of the file asset services; the composition root supplies owner policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from config.env import FileAssetConfig
from modules.file_assets.application.asset_service import AssetService
from modules.file_assets.application.binding_service import BindingService
from modules.file_assets.application.cleanup_service import CleanupService
from modules.file_assets.application.policies import PolicyRegistry
from modules.file_assets.application.runtime import (
    FileAssetRuntime,
    build_storage,
    peek_file_asset_runtime,
    set_file_asset_runtime,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.application.policies import AssetOwnerPolicy

_policy_loader: Callable[[], Iterable[AssetOwnerPolicy]] | None = None
_registry: PolicyRegistry | None = None
_services: FileAssetServices | None = None


def set_policy_loader(loader: Callable[[], Iterable[AssetOwnerPolicy]]) -> None:
    """Called once by the composition root; policies are explicit code, never discovered."""
    global _policy_loader, _registry  # noqa: PLW0603
    _policy_loader = loader
    _registry = None


def get_policy_registry() -> PolicyRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        if _policy_loader is None:
            raise RuntimeError('file asset owner policies are not configured')
        _registry = PolicyRegistry(_policy_loader())
    return _registry


def get_binding_service() -> BindingService:
    """Binding is pure database work and stays available even when storage is not."""
    return BindingService(get_policy_registry(), delete_grace_hours=FileAssetConfig.file_asset_delete_grace_hours)


@dataclass
class FileAssetServices:
    runtime: FileAssetRuntime
    registry: PolicyRegistry
    assets: AssetService
    bindings: BindingService
    cleanup: CleanupService


def configure_file_assets(
    session_factory: Callable[[], AsyncSession],
    *,
    redis_client: Any | None = None,
    runtime: FileAssetRuntime | None = None,
) -> FileAssetServices:
    global _services  # noqa: PLW0603
    runtime = runtime or FileAssetRuntime(FileAssetConfig, build_storage(FileAssetConfig))
    set_file_asset_runtime(runtime)
    registry = get_policy_registry()
    _services = FileAssetServices(
        runtime=runtime,
        registry=registry,
        assets=AssetService(runtime, registry, session_factory),
        bindings=BindingService(registry, delete_grace_hours=runtime.settings.file_asset_delete_grace_hours),
        cleanup=CleanupService(runtime, session_factory, redis_client),
    )
    return _services


def get_file_asset_services() -> FileAssetServices:
    if _services is None:
        from modules.file_assets.domain.errors import FileAssetsUnavailableError  # noqa: PLC0415

        raise FileAssetsUnavailableError('NOT_INITIALIZED', retry_after=None)
    return _services


def peek_file_asset_services() -> FileAssetServices | None:
    return _services


async def shutdown_file_assets() -> None:
    global _services  # noqa: PLW0603
    runtime = peek_file_asset_runtime()
    if runtime is not None:
        await runtime.stop()
    set_file_asset_runtime(None)
    _services = None
