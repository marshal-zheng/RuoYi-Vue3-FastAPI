"""Async bulkhead isolation primitives."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict

from resilience.models import BulkheadConfig


class BulkheadRejectedError(RuntimeError):
    """Raised when bulkhead cannot accept request within wait budget."""


class Bulkhead:
    """Semaphore-based concurrency limiter with timeout."""

    def __init__(self, name: str, config: BulkheadConfig) -> None:
        self.name = name
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrency)
        self._active = 0
        self._peak_active = 0
        self._rejected_total = 0
        self._lock = asyncio.Lock()

    async def run(self, action: Callable[[], Awaitable[Any]]) -> Any:
        if not self.config.enabled:
            return await action()

        acquired = False
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.config.max_wait_seconds)
            acquired = True
        except asyncio.TimeoutError as exc:
            async with self._lock:
                self._rejected_total += 1
            raise BulkheadRejectedError(f'bulkhead rejected: {self.name}') from exc

        try:
            async with self._lock:
                self._active += 1
                if self._active > self._peak_active:
                    self._peak_active = self._active
            return await action()
        finally:
            if acquired:
                self._semaphore.release()
            async with self._lock:
                if self._active > 0:
                    self._active -= 1

    async def snapshot(self) -> Dict[str, int]:
        async with self._lock:
            return {
                'active': self._active,
                'peakActive': self._peak_active,
                'rejectedTotal': self._rejected_total,
                'maxConcurrency': self.config.max_concurrency,
            }


class BulkheadRegistry:
    """Registry for named bulkhead pools."""

    def __init__(self) -> None:
        self._bulkheads: Dict[str, Bulkhead] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, name: str, config: BulkheadConfig) -> Bulkhead:
        async with self._lock:
            bulkhead = self._bulkheads.get(name)
            if bulkhead is None:
                bulkhead = Bulkhead(name=name, config=config)
                self._bulkheads[name] = bulkhead
            return bulkhead

    async def list_snapshots(self) -> list[dict]:
        async with self._lock:
            items = list(self._bulkheads.items())

        snapshots: list[dict] = []
        for name, bulkhead in items:
            snapshot = await bulkhead.snapshot()
            snapshot['name'] = name
            snapshots.append(snapshot)
        snapshots.sort(key=lambda item: item['name'])
        return snapshots
