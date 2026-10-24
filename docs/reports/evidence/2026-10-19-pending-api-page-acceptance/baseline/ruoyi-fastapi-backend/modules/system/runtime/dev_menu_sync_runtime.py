"""Development-mode managed-data hot reconcile runtime scaffolding."""

from __future__ import annotations

import asyncio
import hashlib
from contextlib import suppress
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

from config.env import AppConfig, DataBaseWorkflowConfig, DevManagedDataHotReconcileConfig
from scripts.internal.db_workflow.managed_data_declaration_loader import DEFAULT_MODULE_MANIFEST_ROOT
from utils.log_util import logger

DEFAULT_MANAGED_DATA_MODULES_DIR = DEFAULT_MODULE_MANIFEST_ROOT
DEFAULT_MODULE_MANIFEST_GLOB = '*.module.yaml'

T = TypeVar('T')


def _utcnow() -> datetime:
    return datetime.now(UTC)


def is_dev_managed_data_hot_reconcile_enabled() -> bool:
    """Return whether the managed-data hot reconcile runtime should be enabled."""
    return (
        AppConfig.app_env == 'dev'
        and DataBaseWorkflowConfig.db_workflow_mode == 'development'
        and bool(DevManagedDataHotReconcileConfig.dev_managed_data_hot_reconcile_enabled)
    )


def is_dev_menu_sync_enabled() -> bool:
    """Compatibility alias for legacy callers."""
    return is_dev_managed_data_hot_reconcile_enabled()


@dataclass(frozen=True)
class ManifestSnapshotEntry:
    """One manifest file fingerprint used for cheap change detection."""

    relative_path: str
    mtime_ns: int
    size: int

    @property
    def fingerprint(self) -> tuple[int, int]:
        return (self.mtime_ns, self.size)


@dataclass(frozen=True)
class ManifestSnapshotDiff:
    """Directory snapshot diff for add/modify/delete detection."""

    added: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.removed)


@dataclass(frozen=True)
class ManifestSnapshot:
    """Managed manifest directory snapshot."""

    root: Path
    entries: tuple[ManifestSnapshotEntry, ...]
    checksum: str
    captured_at: datetime = field(default_factory=_utcnow)

    @classmethod
    def capture(
        cls,
        root: str | Path = DEFAULT_MANAGED_DATA_MODULES_DIR,
        manifest_glob: str = DEFAULT_MODULE_MANIFEST_GLOB,
    ) -> ManifestSnapshot:
        root_path = Path(root)
        entries: list[ManifestSnapshotEntry] = []
        if root_path.exists():
            for path in sorted(root_path.glob(manifest_glob)):
                if not path.is_file():
                    continue
                stat = path.stat()
                entries.append(
                    ManifestSnapshotEntry(
                        relative_path=path.relative_to(root_path).as_posix(),
                        mtime_ns=stat.st_mtime_ns,
                        size=stat.st_size,
                    )
                )
        checksum = hashlib.sha256(
            '\n'.join(f'{entry.relative_path}|{entry.mtime_ns}|{entry.size}' for entry in entries).encode('utf-8')
        ).hexdigest()
        return cls(root=root_path, entries=tuple(entries), checksum=checksum)

    def diff(self, previous: ManifestSnapshot | None) -> ManifestSnapshotDiff:
        if previous is None:
            return ManifestSnapshotDiff(added=tuple(entry.relative_path for entry in self.entries))

        previous_map = {entry.relative_path: entry for entry in previous.entries}
        current_map = {entry.relative_path: entry for entry in self.entries}
        added = tuple(sorted(current_map.keys() - previous_map.keys()))
        removed = tuple(sorted(previous_map.keys() - current_map.keys()))
        modified = tuple(
            sorted(
                path
                for path in current_map.keys() & previous_map.keys()
                if current_map[path].fingerprint != previous_map[path].fingerprint
            )
        )
        return ManifestSnapshotDiff(added=added, modified=modified, removed=removed)


@dataclass(frozen=True)
class HotReconcileCallbackResult:
    """Optional callback result returned by future fast-path reconcile handlers."""

    success: bool = True
    compiled_checksum: str | None = None
    synced_at: datetime | None = None
    error: str | None = None
    event_id: int | None = None


ManifestChangeHandler = Callable[
    [str, ManifestSnapshot, ManifestSnapshotDiff],
    Awaitable[HotReconcileCallbackResult | None] | HotReconcileCallbackResult | None,
]


@dataclass
class HotReconcileRuntimeState:
    """In-memory runtime state shared by diagnostics and dev-only APIs."""

    last_seen_snapshot_checksum: str | None = None
    last_applied_snapshot_checksum: str | None = None
    last_applied_compiled_checksum: str | None = None
    pending_snapshot_checksum: str | None = None
    retry_count: int = 0
    next_retry_at: datetime | None = None
    last_sync_success: bool | None = None
    last_sync_at: datetime | None = None
    last_trigger: str | None = None
    last_error: str | None = None
    last_event_id: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            'lastSeenSnapshotChecksum': self.last_seen_snapshot_checksum,
            'lastAppliedSnapshotChecksum': self.last_applied_snapshot_checksum,
            'lastAppliedCompiledChecksum': self.last_applied_compiled_checksum,
            'pendingSnapshotChecksum': self.pending_snapshot_checksum,
            'retryCount': self.retry_count,
            'nextRetryAt': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'lastSyncSuccess': self.last_sync_success,
            'lastSyncAt': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'lastTrigger': self.last_trigger,
            'lastError': self.last_error,
            'lastEventId': self.last_event_id,
        }


DevMenuSyncState = HotReconcileRuntimeState


class DevManagedDataHotReconcileRuntime:
    """Watch `capabilities/modules/*.module.yaml` and serialize reconcile callbacks."""

    def __init__(
        self,
        modules_root: str | Path = DEFAULT_MANAGED_DATA_MODULES_DIR,
        manifest_glob: str = DEFAULT_MODULE_MANIFEST_GLOB,
        watch_interval_ms: int | None = None,
        debounce_ms: int | None = None,
        retry_backoff_ms: int | None = None,
        retry_max_backoff_ms: int | None = None,
        on_manifest_change: ManifestChangeHandler | None = None,
    ) -> None:
        self._modules_root = Path(modules_root)
        self._manifest_glob = manifest_glob
        self._watch_interval_seconds = (
            float(watch_interval_ms) / 1000
            if watch_interval_ms is not None
            else float(DevManagedDataHotReconcileConfig.dev_managed_data_watch_interval_ms) / 1000
        )
        self._debounce_seconds = (
            float(debounce_ms) / 1000
            if debounce_ms is not None
            else float(DevManagedDataHotReconcileConfig.dev_managed_data_debounce_ms) / 1000
        )
        self._retry_backoff_seconds = (
            float(retry_backoff_ms) / 1000
            if retry_backoff_ms is not None
            else float(DevManagedDataHotReconcileConfig.dev_managed_data_retry_backoff_ms) / 1000
        )
        self._retry_max_backoff_seconds = (
            float(retry_max_backoff_ms) / 1000
            if retry_max_backoff_ms is not None
            else float(DevManagedDataHotReconcileConfig.dev_managed_data_retry_max_backoff_ms) / 1000
        )
        self._on_manifest_change = on_manifest_change
        self._stop_event = asyncio.Event()
        self._watch_task: asyncio.Task | None = None
        self._sync_lock = asyncio.Lock()
        self._state = HotReconcileRuntimeState()
        self._latest_snapshot: ManifestSnapshot | None = None

    @property
    def state(self) -> HotReconcileRuntimeState:
        return self._state

    @property
    def latest_snapshot(self) -> ManifestSnapshot | None:
        return self._latest_snapshot

    @property
    def modules_root(self) -> Path:
        return self._modules_root

    @property
    def sync_lock(self) -> asyncio.Lock:
        return self._sync_lock

    def capture_snapshot(self) -> ManifestSnapshot:
        return ManifestSnapshot.capture(root=self._modules_root, manifest_glob=self._manifest_glob)

    def _validate_watch_target(self) -> None:
        if not self._modules_root.exists():
            raise RuntimeError(
                'managed-data hot reconcile modules root does not exist: '
                f'{self._modules_root}. Check capability manifest path configuration.'
            )
        if not self._modules_root.is_dir():
            raise RuntimeError(
                'managed-data hot reconcile modules root is not a directory: '
                f'{self._modules_root}. Check capability manifest path configuration.'
            )
        manifest_count = sum(1 for _ in self._modules_root.glob(self._manifest_glob))
        if manifest_count == 0:
            raise RuntimeError(
                'managed-data hot reconcile found no module manifests under '
                f'{self._modules_root} ({self._manifest_glob}).'
            )

    def snapshot_diff(self, previous: ManifestSnapshot | None, current: ManifestSnapshot | None = None) -> ManifestSnapshotDiff:
        snapshot = current or self.capture_snapshot()
        return snapshot.diff(previous)

    def record_sync_success(
        self,
        *,
        trigger: str,
        snapshot_checksum: str | None = None,
        compiled_checksum: str | None = None,
        synced_at: datetime | None = None,
        event_id: int | None = None,
    ) -> None:
        self._state.last_sync_success = True
        self._state.last_sync_at = synced_at or _utcnow()
        self._state.last_trigger = trigger
        self._state.last_error = None
        self._state.pending_snapshot_checksum = None
        self._state.retry_count = 0
        self._state.next_retry_at = None
        if snapshot_checksum is not None:
            self._state.last_applied_snapshot_checksum = snapshot_checksum
        if compiled_checksum is not None:
            self._state.last_applied_compiled_checksum = compiled_checksum
        if event_id is not None:
            self._state.last_event_id = event_id

    def record_sync_failure(
        self,
        *,
        trigger: str,
        error: str,
        synced_at: datetime | None = None,
        pending_snapshot_checksum: str | None = None,
        retry_count: int | None = None,
        retry_after: datetime | None = None,
    ) -> None:
        self._state.last_sync_success = False
        self._state.last_sync_at = synced_at or _utcnow()
        self._state.last_trigger = trigger
        self._state.last_error = error
        if pending_snapshot_checksum is not None:
            self._state.pending_snapshot_checksum = pending_snapshot_checksum
            self._state.retry_count = retry_count if retry_count is not None else self._state.retry_count + 1
            self._state.next_retry_at = retry_after

    def _next_retry_count_for_snapshot(self, snapshot_checksum: str) -> int:
        if self._state.pending_snapshot_checksum == snapshot_checksum:
            return self._state.retry_count + 1
        return 1

    def _compute_retry_after(self, retry_count: int) -> datetime:
        if self._retry_backoff_seconds <= 0 or self._retry_max_backoff_seconds <= 0:
            return _utcnow()
        exponent = max(0, retry_count - 1)
        delay_seconds = min(self._retry_max_backoff_seconds, self._retry_backoff_seconds * (2 ** exponent))
        return _utcnow() + timedelta(seconds=delay_seconds)

    def _should_delay_retry(self, snapshot_checksum: str) -> bool:
        pending_snapshot_checksum = self._state.pending_snapshot_checksum
        next_retry_at = self._state.next_retry_at
        if pending_snapshot_checksum != snapshot_checksum or next_retry_at is None:
            return False
        return _utcnow() < next_retry_at

    async def run_serialized(self, operation: Callable[[], Awaitable[T] | T]) -> T:
        async with self._sync_lock:
            result = operation()
            if asyncio.iscoroutine(result):
                return await result
            return result

    async def reconcile_snapshot(
        self,
        trigger: str,
        snapshot: ManifestSnapshot | None = None,
        diff: ManifestSnapshotDiff | None = None,
    ) -> HotReconcileCallbackResult | None:
        current_snapshot = snapshot or self.capture_snapshot()
        current_diff = diff or current_snapshot.diff(self._latest_snapshot)
        self._state.last_seen_snapshot_checksum = current_snapshot.checksum

        if self._on_manifest_change is None:
            self._latest_snapshot = current_snapshot
            return None

        async def _invoke_callback() -> HotReconcileCallbackResult | None:
            callback_result = self._on_manifest_change(trigger, current_snapshot, current_diff)
            if asyncio.iscoroutine(callback_result):
                callback_result = await callback_result
            if callback_result is None:
                self._latest_snapshot = current_snapshot
                self.record_sync_success(trigger=trigger, snapshot_checksum=current_snapshot.checksum)
                return None
            if callback_result.success:
                self._latest_snapshot = current_snapshot
                self.record_sync_success(
                    trigger=trigger,
                    snapshot_checksum=current_snapshot.checksum,
                    compiled_checksum=callback_result.compiled_checksum,
                    synced_at=callback_result.synced_at,
                    event_id=callback_result.event_id,
                )
                return callback_result
            retry_count = self._next_retry_count_for_snapshot(current_snapshot.checksum)
            self.record_sync_failure(
                trigger=trigger,
                error=callback_result.error or 'unknown_error',
                synced_at=callback_result.synced_at,
                pending_snapshot_checksum=current_snapshot.checksum,
                retry_count=retry_count,
                retry_after=self._compute_retry_after(retry_count),
            )
            return callback_result

        try:
            return await self.run_serialized(_invoke_callback)
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            retry_count = self._next_retry_count_for_snapshot(current_snapshot.checksum)
            self.record_sync_failure(
                trigger=trigger,
                error=str(exc),
                pending_snapshot_checksum=current_snapshot.checksum,
                retry_count=retry_count,
                retry_after=self._compute_retry_after(retry_count),
            )
            logger.error('Dev managed data hot reconcile failed (trigger={}): {}', trigger, exc)
            raise

    async def start(self) -> None:
        if self._watch_task and not self._watch_task.done():
            return
        self._stop_event.clear()
        self._validate_watch_target()
        self._latest_snapshot = self.capture_snapshot()
        self._state.last_seen_snapshot_checksum = self._latest_snapshot.checksum
        self._watch_task = asyncio.create_task(self._watch_loop(), name='dev-managed-data-hot-reconcile')

    async def stop(self) -> None:
        self._stop_event.set()
        if self._watch_task is not None:
            try:
                await asyncio.wait_for(
                    self._watch_task,
                    timeout=max(self._watch_interval_seconds + self._debounce_seconds, 0.1),
                )
            except TimeoutError:
                self._watch_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._watch_task
        self._watch_task = None

    async def _watch_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._watch_interval_seconds)
                break
            except TimeoutError:
                pass
            except asyncio.CancelledError:
                break

            previous_snapshot = self._latest_snapshot
            current_snapshot = self.capture_snapshot()
            diff = current_snapshot.diff(previous_snapshot)
            if not diff.has_changes:
                continue

            if self._debounce_seconds > 0:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._debounce_seconds)
                except TimeoutError:
                    pass
                except asyncio.CancelledError:
                    break
                if self._stop_event.is_set():
                    break
                current_snapshot = self.capture_snapshot()
                diff = current_snapshot.diff(previous_snapshot)
                if not diff.has_changes:
                    self._latest_snapshot = current_snapshot
                    self._state.last_seen_snapshot_checksum = current_snapshot.checksum
                    continue

            if self._should_delay_retry(current_snapshot.checksum):
                continue

            logger.debug(
                'Dev managed data manifest snapshot changed: added={}, modified={}, removed={}, previous_checksum={}, current_checksum={}',
                diff.added,
                diff.modified,
                diff.removed,
                previous_snapshot.checksum if previous_snapshot is not None else None,
                current_snapshot.checksum,
            )

            if self._on_manifest_change is None:
                self._latest_snapshot = current_snapshot
                self._state.last_seen_snapshot_checksum = current_snapshot.checksum
                continue

            try:
                await self.reconcile_snapshot('file_change', snapshot=current_snapshot, diff=diff)
            except Exception:
                continue


DevMenuSyncRuntime = DevManagedDataHotReconcileRuntime
