"""In-memory resilience metrics."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict


class ResilienceMetrics:
    """Counters for retry/circuit/bulkhead/saga events."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._counters: Dict[str, int] = defaultdict(int)

    async def inc(self, name: str, value: int = 1) -> None:
        async with self._lock:
            self._counters[name] += value

    async def snapshot(self) -> Dict[str, int]:
        async with self._lock:
            return dict(self._counters)
