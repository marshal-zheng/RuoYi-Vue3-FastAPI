"""External dependency protocol contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from events.domain_events import DomainEvent


EventHandler = Callable[['DomainEvent'], Awaitable[None]]


@runtime_checkable
class IRedisClient(Protocol):
    """Minimal async Redis contract for application services."""

    async def get(self, key: str) -> Any | None:
        """Read cached value by key."""

    async def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        """Set key to value with optional redis flags."""

    async def setex(self, key: str, ttl: int, value: Any) -> Any:
        """Set key with an expiration in seconds."""

    async def setnx(self, key: str, value: Any) -> Any:
        """Set key only if key does not already exist."""

    async def expire(self, key: str, ttl: int) -> Any:
        """Set expiration time for one key."""

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""

    async def keys(self, pattern: str = '*') -> Iterable[str]:
        """Return keys matching pattern."""

    async def info(self, section: str | None = None) -> dict[str, Any]:
        """Return redis server information."""

    async def dbsize(self) -> int:
        """Return number of keys in current database."""

    async def rpush(self, key: str, *values: Any) -> Any:
        """Append one or more values to a list."""

    async def ltrim(self, key: str, start: int, end: int) -> Any:
        """Trim an existing list to the specified range."""

    async def llen(self, key: str) -> int:
        """Return the length of a list."""

    async def lrange(self, key: str, start: int, end: int) -> list[Any]:
        """Return a list range by start/end offsets."""

    async def ping(self) -> Any:
        """Probe redis availability."""

    async def close(self) -> None:
        """Close redis client resources."""


@runtime_checkable
class ICacheProvider(Protocol):
    """Cache provider abstraction independent from cache backend."""

    async def get(self, key: str) -> Any | None:
        """Return value by key."""

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Write value by key with optional ttl."""

    async def invalidate(self, key: str) -> None:
        """Remove one cached key."""

    async def invalidate_many(self, keys: Iterable[str]) -> None:
        """Remove multiple cached keys."""


@runtime_checkable
class IAuditLogger(Protocol):
    """Audit logger abstraction for security and compliance logs."""

    async def record(
        self,
        action: str,
        actor: str,
        target: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Record one immutable audit entry."""


@runtime_checkable
class IEventBus(Protocol):
    """Event bus abstraction for decoupled message dispatch."""

    async def publish(self, event: 'DomainEvent') -> Any:
        """Publish one domain event to all subscribed handlers."""

    def subscribe(self, event_type: str, handler: EventHandler, *, handler_name: str | None = None) -> None:
        """Subscribe handler to one event type."""


__all__ = [
    'EventHandler',
    'IAuditLogger',
    'ICacheProvider',
    'IEventBus',
    'IRedisClient',
]
