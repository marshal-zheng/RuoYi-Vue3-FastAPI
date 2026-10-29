"""Per-process file asset runtime: bounded worker pools, capacity slots, metrics and ownership state."""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypeVar

from modules.file_assets.domain.errors import FileAssetsUnavailableError
from modules.file_assets.infrastructure.s3_storage import (
    ObjectMissingError,
    StorageObjectError,
    StorageUnavailableError,
)
from utils.log_util import logger


def alert(name: str, message: str, **fields: Any) -> None:
    """Operations-visible alert through the existing structured log + metrics channel."""
    logger.bind(event='file_assets_alert', alert=name, **fields).error(message)


if TYPE_CHECKING:
    from collections.abc import Callable

    from config.env import FileAssetSettings
    from modules.file_assets.infrastructure.s3_storage import ObjectStorage

T = TypeVar('T')


class OwnershipState(StrEnum):
    UNCONFIRMED = 'unconfirmed'
    CONFIRMED = 'confirmed'
    INVALID = 'invalid'


@dataclass(frozen=True)
class OwnershipCheck:
    outcome: str  # confirmed | invalid | transient
    reason: str


class Slot:
    """One unit of capacity; released exactly once, after the work that used it has really ended."""

    def __init__(self, semaphore: asyncio.Semaphore, gauge: Counter, name: str):
        self._semaphore = semaphore
        self._gauge = gauge
        self._name = name
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        self._gauge[self._name] -= 1
        self._semaphore.release()


class SlotPool:
    def __init__(self, name: str, capacity: int, wait_seconds: float, gauge: Counter):
        self.name = name
        self.capacity = capacity
        self._wait_seconds = wait_seconds
        self._semaphore = asyncio.Semaphore(capacity)
        self._gauge = gauge

    async def acquire(self) -> Slot:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._wait_seconds)
        except TimeoutError:
            raise FileAssetsUnavailableError(
                'CAPACITY_EXHAUSTED', user_message='文件服务繁忙，请稍后重试', retry_after=5
            ) from None
        self._gauge[self.name] += 1
        return Slot(self._semaphore, self._gauge, self.name)


@dataclass
class FileAssetMetrics:
    """Low-cardinality counters; asset ids, names and users only go to structured logs."""

    counters: Counter = field(default_factory=Counter)
    gauges: dict[str, float] = field(default_factory=dict)
    in_use: Counter = field(default_factory=Counter)

    def inc(self, name: str, amount: int = 1, **labels: str) -> None:
        key = name if not labels else name + '{' + ','.join(f'{k}="{v}"' for k, v in sorted(labels.items())) + '}'
        self.counters[key] += amount

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = float(value)

    def render(self) -> str:
        lines = []
        for key, value in sorted(self.counters.items()):
            lines.append(f'file_assets_{key} {value}')
        for key, value in sorted(self.gauges.items()):
            lines.append(f'file_assets_{key} {value}')
        for key, value in sorted(self.in_use.items()):
            lines.append(f'file_assets_slots_in_use{{pool="{key}"}} {value}')
        return '\n'.join(lines) + ('\n' if lines else '')


class OwnershipGuard:
    """Bucket ownership: only a confirmed installation marker allows file I/O and any object deletion."""

    STARTUP_ATTEMPTS = 3
    UNCONFIRMED_ALERT_AFTER = 300.0
    UNCONFIRMED_INTERVAL = 10.0
    CONFIRMED_INTERVAL = 600.0
    INVALID_INTERVAL = 60.0
    TRANSIENT_RETRY = 30.0

    def __init__(self, runtime: FileAssetRuntime):
        self._runtime = runtime
        self.state = OwnershipState.UNCONFIRMED
        self.reason = 'NOT_CHECKED'
        self.changed_at = time.monotonic()
        self.last_check_at: float | None = None
        self._unconfirmed_alerted = False
        self._task: asyncio.Task | None = None

    @property
    def confirmed(self) -> bool:
        return self.state is OwnershipState.CONFIRMED

    def _transition(self, state: OwnershipState, reason: str) -> None:
        if state is not self.state:
            self.changed_at = time.monotonic()
            self._unconfirmed_alerted = False
            logger.info('file_assets.ownership state={} reason={}', state.value, reason)
            if state is OwnershipState.INVALID:
                alert(
                    'storage_ownership_invalid', 'file capability disabled: bucket ownership is invalid', reason=reason
                )
        self.state, self.reason = state, reason
        self._runtime.metrics.set_gauge('storage_ownership_mismatch', 1 if state is OwnershipState.INVALID else 0)

    async def _read_marker(self) -> OwnershipCheck:  # noqa: PLR0911 - one outcome per storage answer
        runtime = self._runtime
        if runtime.storage is None:
            return OwnershipCheck('invalid', 'NOT_CONFIGURED')
        try:
            marker = await runtime.run_ownership(runtime.storage.read_installation_marker)
        except ObjectMissingError:
            return OwnershipCheck('invalid', 'MARKER_MISSING')
        except StorageObjectError as exc:
            if exc.status == 403 or exc.code == 'AccessDenied':
                return OwnershipCheck('invalid', 'MARKER_ACCESS_DENIED')
            if exc.code == 'NoSuchBucket':
                return OwnershipCheck('invalid', 'BUCKET_MISSING')
            return OwnershipCheck('transient', f'MARKER_READ_{exc.code}')
        except StorageUnavailableError as exc:
            return OwnershipCheck('transient', f'STORAGE_{exc.code}')
        if marker.installation_id == runtime.settings.file_asset_installation_id:
            return OwnershipCheck('confirmed', 'MARKER_MATCH')
        return OwnershipCheck('invalid', 'INSTALLATION_MISMATCH')

    async def check_once(self) -> OwnershipCheck:
        result = await self._read_marker()
        self.last_check_at = time.monotonic()
        if result.outcome == 'confirmed':
            self._transition(OwnershipState.CONFIRMED, result.reason)
        elif result.outcome == 'invalid':
            self._transition(OwnershipState.INVALID, result.reason)
        else:
            # Network/timeout/5xx never changes a known conclusion.
            logger.warning('file_assets.ownership check transient reason={}', result.reason)
            self.reason = result.reason if self.state is OwnershipState.UNCONFIRMED else self.reason
        if (
            self.state is OwnershipState.UNCONFIRMED
            and not self._unconfirmed_alerted
            and time.monotonic() - self.changed_at > self.UNCONFIRMED_ALERT_AFTER
        ):
            self._unconfirmed_alerted = True
            alert('storage_ownership_unconfirmed', 'bucket ownership still unconfirmed', reason=self.reason)
        return result

    async def startup(self) -> None:
        for _ in range(self.STARTUP_ATTEMPTS):
            result = await self.check_once()
            if result.outcome != 'transient':
                break
        if self._runtime.storage is not None:
            self._task = asyncio.create_task(self._loop(), name='file-assets-ownership')

    async def _loop(self) -> None:
        last_transient = False
        while True:
            if last_transient:
                delay = (
                    self.TRANSIENT_RETRY if self.state is not OwnershipState.UNCONFIRMED else self.UNCONFIRMED_INTERVAL
                )
            else:
                delay = {
                    OwnershipState.UNCONFIRMED: self.UNCONFIRMED_INTERVAL,
                    OwnershipState.CONFIRMED: self.CONFIRMED_INTERVAL,
                    OwnershipState.INVALID: self.INVALID_INTERVAL,
                }[self.state]
            await asyncio.sleep(delay)
            try:
                last_transient = (await self.check_once()).outcome == 'transient'
            except Exception as exc:  # pragma: no cover - defensive; keep the guard alive
                logger.error('file_assets.ownership loop error: {}', type(exc).__name__)
                last_transient = True

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    def snapshot(self) -> dict[str, Any]:
        return {
            'state': self.state.value,
            'reason': self.reason,
            'stateAgeSeconds': round(time.monotonic() - self.changed_at, 1),
        }


class FileAssetRuntime:
    def __init__(self, settings: FileAssetSettings, storage: ObjectStorage | None):
        self.settings = settings
        self.storage = storage
        self._storage_probe: tuple[float, str | None] | None = None
        self.metrics = FileAssetMetrics()
        io, download, maintenance = (
            settings.file_asset_io_concurrency,
            settings.file_asset_download_concurrency,
            settings.file_asset_maintenance_concurrency,
        )
        wait = settings.file_asset_slot_wait_seconds
        self.upload_slots = SlotPool('upload', io, wait, self.metrics.in_use)
        self.download_slots = SlotPool('download', download, wait, self.metrics.in_use)
        self.maintenance_slots = SlotPool('maintenance', maintenance, 0, self.metrics.in_use)
        # Pools sized exactly to the slots so no hidden queue grows behind them.
        self._upload_pool = ThreadPoolExecutor(max_workers=io, thread_name_prefix='file-assets-upload')
        self._download_pool = ThreadPoolExecutor(max_workers=download, thread_name_prefix='file-assets-download')
        self._maintenance_pool = ThreadPoolExecutor(max_workers=maintenance, thread_name_prefix='file-assets-maint')
        self._ownership_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='file-assets-owner')
        self.ownership = OwnershipGuard(self)
        self.inflight_uploads: set[asyncio.Task] = set()

    @property
    def configured(self) -> bool:
        return self.storage is not None

    def require_available(self) -> ObjectStorage:
        """File I/O (upload, content, metadata) needs configured storage and a confirmed bucket owner."""
        if self.storage is None:
            raise FileAssetsUnavailableError('NOT_CONFIGURED', retry_after=None)
        if not self.ownership.confirmed:
            reason = 'OWNERSHIP_INVALID' if self.ownership.state is OwnershipState.INVALID else 'OWNERSHIP_UNCONFIRMED'
            raise FileAssetsUnavailableError(reason)
        return self.storage

    @staticmethod
    async def _run(pool: ThreadPoolExecutor, fn: Callable[..., T], *args: Any) -> T:
        return await asyncio.get_running_loop().run_in_executor(pool, fn, *args)

    def submit_upload(self, fn: Callable[..., T], *args: Any) -> asyncio.Future[T]:
        return asyncio.get_running_loop().run_in_executor(self._upload_pool, fn, *args)

    def submit_download(self, fn: Callable[..., T], *args: Any) -> Future[T]:
        """A concurrent future, so callers can wait for a running read even after cancellation."""
        return self._download_pool.submit(fn, *args)

    async def run_download(self, fn: Callable[..., T], *args: Any) -> T:
        return await self._run(self._download_pool, fn, *args)

    async def run_maintenance(self, fn: Callable[..., T], *args: Any) -> T:
        return await self._run(self._maintenance_pool, fn, *args)

    async def run_ownership(self, fn: Callable[..., T], *args: Any) -> T:
        return await self._run(self._ownership_pool, fn, *args)

    async def start(self) -> None:
        await self.ownership.startup()

    async def stop(self) -> None:
        await self.ownership.stop()
        if self.inflight_uploads:
            # Let committed-or-compensated upload work finish instead of abandoning UPLOADING rows.
            await asyncio.wait(
                set(self.inflight_uploads), timeout=self.settings.file_asset_upload_state_timeout_seconds
            )
        for pool in (self._upload_pool, self._download_pool, self._maintenance_pool, self._ownership_pool):
            pool.shutdown(wait=False, cancel_futures=True)

    HEALTH_PROBE_TTL = 10.0

    async def health_probe(self) -> dict[str, Any]:
        """Health that also reflects a storage outage (R12.AC4); one cached marker read per 10 seconds."""
        payload = self.health()
        if payload['status'] != 'available':
            return payload
        cached = self._storage_probe
        if cached is None or time.monotonic() - cached[0] > self.HEALTH_PROBE_TTL:
            try:
                await self.run_ownership(self.storage.read_installation_marker)
                cached = (time.monotonic(), None)
            except StorageUnavailableError as exc:
                cached = (time.monotonic(), f'STORAGE_{exc.code}')
            except Exception:
                cached = (time.monotonic(), None)  # the storage answered; the ownership guard owns that verdict
            self._storage_probe = cached
        if cached[1] is not None:
            payload['status'] = 'unavailable'
            payload['storage'] = {'reachable': False, 'reason': cached[1]}
        else:
            payload['storage'] = {'reachable': True}
        return payload

    def health(self) -> dict[str, Any]:
        available = self.storage is not None and self.ownership.confirmed
        return {
            'status': 'available' if available else 'unavailable',
            'configured': self.storage is not None,
            'missingSettings': list(self.settings.missing_settings),
            'ownership': self.ownership.snapshot(),
            'inflightUploads': len(self.inflight_uploads),
            'slotsInUse': dict(self.metrics.in_use),
        }


_runtime: FileAssetRuntime | None = None


def build_storage(settings: FileAssetSettings) -> ObjectStorage | None:
    if not settings.is_configured:
        return None
    from modules.file_assets.infrastructure.s3_storage import S3ObjectStorage  # noqa: PLC0415

    pools = (
        settings.file_asset_io_concurrency
        + settings.file_asset_download_concurrency
        + settings.file_asset_maintenance_concurrency
        + 2
    )
    return S3ObjectStorage(
        endpoint=settings.file_asset_s3_endpoint,
        bucket=settings.file_asset_s3_bucket,
        region=settings.file_asset_s3_region,
        addressing_style=settings.file_asset_s3_addressing_style,
        access_key=settings.file_asset_s3_access_key.get_secret_value(),
        secret_key=settings.file_asset_s3_secret_key.get_secret_value(),
        max_pool_connections=pools,
    )


def set_file_asset_runtime(runtime: FileAssetRuntime | None) -> None:
    global _runtime  # noqa: PLW0603 - one runtime per process, set by the application lifespan
    _runtime = runtime


def get_file_asset_runtime() -> FileAssetRuntime:
    if _runtime is None:
        raise FileAssetsUnavailableError('NOT_INITIALIZED', retry_after=None)
    return _runtime


def peek_file_asset_runtime() -> FileAssetRuntime | None:
    return _runtime
