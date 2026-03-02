"""Development-mode menu sync runtime."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from config.env import AppConfig, DevMenuSyncConfig
from utils.log_util import logger


def is_dev_menu_sync_enabled() -> bool:
    """Return whether dev menu sync should run in current process."""
    return AppConfig.app_env == 'dev' and bool(DevMenuSyncConfig.dev_menu_sync)


@dataclass
class DevMenuSyncState:
    """In-memory runtime sync state for API/debug visibility."""

    last_sync_success: bool | None = None
    last_sync_at: datetime | None = None
    last_trigger: str | None = None
    last_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            'lastSyncSuccess': self.last_sync_success,
            'lastSyncAt': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'lastTrigger': self.last_trigger,
            'lastError': self.last_error,
        }


class DevMenuSyncRuntime:
    """Runtime loop that performs startup sync and file-change sync in dev mode."""

    def __init__(
        self,
        service_factory: Callable[[], Any],
        watch_paths: Sequence[str | Path],
        poll_interval_seconds: float | None = None,
        debounce_seconds: float | None = None,
    ) -> None:
        self._service_factory = service_factory
        self._watch_paths = tuple(Path(path) for path in watch_paths)
        self._poll_interval_seconds = (
            float(poll_interval_seconds)
            if poll_interval_seconds is not None
            else float(DevMenuSyncConfig.dev_menu_sync_poll_interval_seconds)
        )
        self._debounce_seconds = (
            float(debounce_seconds)
            if debounce_seconds is not None
            else float(DevMenuSyncConfig.dev_menu_sync_debounce_seconds)
        )
        self._stop_event = asyncio.Event()
        self._watch_task: asyncio.Task | None = None
        self._sync_lock = asyncio.Lock()
        self._known_mtimes: dict[Path, int] = {}
        self._state = DevMenuSyncState()

    @property
    def state(self) -> DevMenuSyncState:
        return self._state

    async def start(self) -> None:
        """Start runtime loop and execute one startup sync."""
        if self._watch_task and not self._watch_task.done():
            return
        self._stop_event.clear()
        self._snapshot_mtimes()
        if DevMenuSyncConfig.dev_menu_sync_auto_startup:
            await self.trigger_sync('startup')
        self._watch_task = asyncio.create_task(self._watch_loop(), name='dev-menu-sync-runtime')

    async def stop(self) -> None:
        """Stop runtime loop."""
        self._stop_event.set()
        if self._watch_task is not None:
            try:
                await asyncio.wait_for(
                    self._watch_task,
                    timeout=max(self._poll_interval_seconds + self._debounce_seconds, 0.1),
                )
            except asyncio.TimeoutError:
                self._watch_task.cancel()
                try:
                    await self._watch_task
                except asyncio.CancelledError:
                    pass
        self._watch_task = None

    async def trigger_sync(self, trigger: str) -> None:
        """Invoke reconcile service once and update runtime state."""
        async with self._sync_lock:
            service = self._service_factory()
            try:
                report = await service.sync_once(trigger=trigger, dry_run=False)
                success = bool(getattr(report, 'success', True))
                self._state.last_sync_success = success
                self._state.last_sync_at = datetime.now()
                self._state.last_trigger = trigger
                self._state.last_error = None if success else str(getattr(report, 'error', 'unknown_error'))
                if success:
                    logger.info('Dev menu sync succeeded (trigger={})', trigger)
                else:
                    logger.warning(
                        'Dev menu sync finished with failure state (trigger={}, error={})',
                        trigger,
                        self._state.last_error,
                    )
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self._state.last_sync_success = False
                self._state.last_sync_at = datetime.now()
                self._state.last_trigger = trigger
                self._state.last_error = str(exc)
                logger.error('Dev menu sync failed (trigger={}): {}', trigger, exc)
            finally:
                await self._close_service_session(service)

    @staticmethod
    async def _close_service_session(service: Any) -> None:
        query_db = getattr(service, 'query_db', None)
        close = getattr(query_db, 'close', None)
        if callable(close):
            result = close()
            if asyncio.iscoroutine(result):
                await result

    async def _watch_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._watch_paths and self._detect_file_changes():
                if self._debounce_seconds > 0:
                    await asyncio.sleep(self._debounce_seconds)
                await self.trigger_sync('file_change')
                self._snapshot_mtimes()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval_seconds)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def _snapshot_mtimes(self) -> None:
        self._known_mtimes = {
            path: self._get_mtime_ns(path)
            for path in self._watch_paths
        }

    def _detect_file_changes(self) -> bool:
        if not self._known_mtimes:
            self._snapshot_mtimes()
            return False
        changed = False
        for path in self._watch_paths:
            current = self._get_mtime_ns(path)
            previous = self._known_mtimes.get(path)
            if previous != current:
                changed = True
        return changed

    @staticmethod
    def _get_mtime_ns(path: Path) -> int:
        try:
            return path.stat().st_mtime_ns
        except FileNotFoundError:
            return -1
