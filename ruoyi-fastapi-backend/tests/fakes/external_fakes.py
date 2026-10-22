from __future__ import annotations

import fnmatch
import time
from collections import defaultdict
from copy import deepcopy
from typing import Any

from events.domain_events import DomainEvent
from ports import IAuditLogger, ICacheProvider, IEventBus, IRedisClient


class InMemoryRedisClient:
    """Redis-like in-memory fake for unit tests."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._expires_at: dict[str, float] = {}
        self._lists: dict[str, list[Any]] = defaultdict(list)

    def _purge_if_expired(self, key: str) -> None:
        expires_at = self._expires_at.get(key)
        if expires_at is not None and expires_at <= time.time():
            self._values.pop(key, None)
            self._lists.pop(key, None)
            self._expires_at.pop(key, None)

    def _purge_all_expired(self) -> None:
        for key in list(self._expires_at.keys()):
            self._purge_if_expired(key)

    async def get(self, key: str) -> Any | None:
        self._purge_if_expired(key)
        return self._values.get(key)

    async def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> bool:
        self._values[key] = value
        ex = kwargs.get('ex')
        if ex is not None:
            self._expires_at[key] = time.time() + int(ex)
        elif key in self._expires_at:
            self._expires_at.pop(key, None)
        return True

    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        self._values[key] = value
        self._expires_at[key] = time.time() + int(ttl)
        return True

    async def setnx(self, key: str, value: Any) -> int:
        self._purge_if_expired(key)
        if key in self._values:
            return 0
        self._values[key] = value
        return 1

    async def expire(self, key: str, ttl: int) -> int:
        if key not in self._values and key not in self._lists:
            return 0
        self._expires_at[key] = time.time() + int(ttl)
        return 1

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            deleted += int(key in self._values or key in self._lists)
            self._values.pop(key, None)
            self._lists.pop(key, None)
            self._expires_at.pop(key, None)
        return deleted

    async def keys(self, pattern: str = '*') -> list[str]:
        self._purge_all_expired()
        all_keys = set(self._values.keys()) | set(self._lists.keys())
        return sorted(key for key in all_keys if fnmatch.fnmatch(key, pattern))

    async def scan_iter(self, *, match: str = '*'):
        for key in await self.keys(match):
            yield key

    async def info(self, section: str | None = None) -> dict[str, Any]:
        self._purge_all_expired()
        payload = {'section': section or 'default', 'keys': len(self._values) + len(self._lists)}
        return payload

    async def dbsize(self) -> int:
        self._purge_all_expired()
        return len(set(self._values.keys()) | set(self._lists.keys()))

    async def rpush(self, key: str, *values: Any) -> int:
        self._lists[key].extend(values)
        return len(self._lists[key])

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        rows = self._lists.get(key, [])
        if end == -1:
            end = len(rows) - 1
        self._lists[key] = rows[start : end + 1] if rows else []
        return True

    async def llen(self, key: str) -> int:
        return len(self._lists.get(key, []))

    async def lrange(self, key: str, start: int, end: int) -> list[Any]:
        rows = self._lists.get(key, [])
        if not rows:
            return []
        if end == -1:
            end = len(rows) - 1
        return deepcopy(rows[start : end + 1])

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class InMemoryCacheProvider:
    """Cache provider fake for unit tests."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache[key] = value

    async def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    async def invalidate_many(self, keys: list[str]) -> None:
        for key in keys:
            self._cache.pop(key, None)


class InMemoryAuditLogger:
    """Audit logger fake for unit tests."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def record(
        self,
        action: str,
        actor: str,
        target: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.entries.append(
            {
                'action': action,
                'actor': actor,
                'target': target,
                'payload': deepcopy(payload) if payload is not None else None,
            }
        )


class InMemoryEventBus:
    """Event bus fake for unit tests."""

    def __init__(self) -> None:
        self._handlers: dict[str, list] = defaultdict(list)
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> dict[str, int]:
        self.published.append(event)
        for handler in self._handlers[event.event_type]:
            await handler(
                DomainEvent.from_dict(
                    {
                        **event.to_dict(),
                        'payload': deepcopy(dict(event.payload)),
                        'metadata': deepcopy(dict(event.metadata)),
                    }
                )
            )
        return {
            'handlers_total': len(self._handlers[event.event_type]),
            'handlers_succeeded': len(self._handlers[event.event_type]),
            'handlers_failed': 0,
            'handlers_skipped': 0,
        }

    def subscribe(self, event_type: str, handler, *, handler_name: str | None = None) -> None:
        _ = handler_name
        self._handlers[event_type].append(handler)


def assert_external_fake_contracts() -> None:
    """Assert fake instances satisfy runtime-checkable protocols."""
    assert isinstance(InMemoryRedisClient(), IRedisClient)
    assert isinstance(InMemoryCacheProvider(), ICacheProvider)
    assert isinstance(InMemoryAuditLogger(), IAuditLogger)
    assert isinstance(InMemoryEventBus(), IEventBus)
