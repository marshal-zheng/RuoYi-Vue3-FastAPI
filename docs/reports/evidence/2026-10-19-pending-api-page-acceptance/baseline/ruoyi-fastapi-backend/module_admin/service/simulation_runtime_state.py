"""
Shared runtime state store for simulation sessions.

Design goals:
- Persist session snapshot in Redis for cross-worker visibility.
- Persist append-only event streams (messages/bandwidth/alarms/faults).
- Keep an in-process fallback store to preserve behavior when Redis is unavailable.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from ports import IRedisClient
from utils.log_util import logger


class SimulationRuntimeStateStore:
    """Runtime state store with Redis-first and local-memory fallback."""

    VALID_STREAMS = {'messages', 'bandwidth', 'alarms', 'faults'}

    def __init__(
        self,
        redis_client: Optional[IRedisClient] = None,
        session_ttl: int = 24 * 3600,
        stream_ttl: int = 2 * 3600,
        max_stream_items: int = 5000,
        key_prefix: str = 'sim:session',
    ):
        self.redis = redis_client
        self.session_ttl = session_ttl
        self.stream_ttl = stream_ttl
        self.max_stream_items = max_stream_items
        self.key_prefix = key_prefix

        self._local_sessions: Dict[str, Dict[str, Any]] = {}
        self._local_streams: Dict[str, Dict[str, List[str]]] = {}
        self._local_producer_owner: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _meta_key(self, session_id: str) -> str:
        return f'{self.key_prefix}:{session_id}:meta'

    def _stream_key(self, session_id: str, stream: str) -> str:
        return f'{self.key_prefix}:{session_id}:stream:{stream}'

    def _producer_owner_key(self, session_id: str) -> str:
        return f'{self.key_prefix}:{session_id}:producer_owner'

    @staticmethod
    def _dumps(payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)

    @staticmethod
    def _loads(payload: Any) -> Any:
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    @staticmethod
    def _to_text(payload: Any) -> Optional[str]:
        if payload is None:
            return None
        if isinstance(payload, bytes):
            return payload.decode('utf-8')
        return str(payload)

    async def save_session_snapshot(self, session_id: str, snapshot: Dict[str, Any]) -> None:
        payload = dict(snapshot or {})
        payload.setdefault('session_id', session_id)
        payload['updated_at'] = payload.get('updated_at') or time.time()

        async with self._lock:
            self._local_sessions[session_id] = payload

        if self.redis is None:
            return

        try:
            await self.redis.setex(self._meta_key(session_id), self.session_ttl, self._dumps(payload))
        except Exception as exc:
            logger.warning(f'save_session_snapshot redis failed: {exc}')

    async def get_session_snapshot(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.redis is not None:
            try:
                cached = await self.redis.get(self._meta_key(session_id))
                if cached:
                    return self._loads(cached)
            except Exception as exc:
                logger.warning(f'get_session_snapshot redis failed: {exc}')

        async with self._lock:
            data = self._local_sessions.get(session_id)
            return dict(data) if data else None

    async def clear_session(self, session_id: str) -> None:
        async with self._lock:
            self._local_sessions.pop(session_id, None)
            self._local_streams.pop(session_id, None)
            self._local_producer_owner.pop(session_id, None)

        if self.redis is None:
            return

        try:
            keys = [self._meta_key(session_id)]
            for stream in self.VALID_STREAMS:
                keys.append(self._stream_key(session_id, stream))
            keys.append(self._producer_owner_key(session_id))
            await self.redis.delete(*keys)
        except Exception as exc:
            logger.warning(f'clear_session redis failed: {exc}')

    async def claim_session_producer_owner(self, session_id: str, worker_id: str, ttl_seconds: int = 10) -> bool:
        """Claim owner token for session-level producer (cross-worker safe when Redis is available)."""
        ttl = max(1, int(ttl_seconds or 1))
        owner_key = self._producer_owner_key(session_id)
        redis_lock_capable = self.redis is not None and (hasattr(self.redis, 'set') or hasattr(self.redis, 'setnx'))
        if redis_lock_capable:
            try:
                current_owner = None
                if hasattr(self.redis, 'get'):
                    current_owner = self._to_text(await self.redis.get(owner_key))
                if current_owner == worker_id:
                    if hasattr(self.redis, 'expire'):
                        await self.redis.expire(owner_key, ttl)
                    elif hasattr(self.redis, 'setex'):
                        await self.redis.setex(owner_key, ttl, worker_id)
                    return True

                if hasattr(self.redis, 'set'):
                    acquired = await self.redis.set(owner_key, worker_id, ex=ttl, nx=True)
                    if acquired:
                        return True
                elif hasattr(self.redis, 'setnx'):
                    acquired = await self.redis.setnx(owner_key, worker_id)
                    if acquired:
                        if hasattr(self.redis, 'expire'):
                            await self.redis.expire(owner_key, ttl)
                        return True

                if hasattr(self.redis, 'get'):
                    current_owner = self._to_text(await self.redis.get(owner_key))
                    if current_owner == worker_id:
                        if hasattr(self.redis, 'expire'):
                            await self.redis.expire(owner_key, ttl)
                        return True
            except Exception as exc:
                logger.warning(f'claim_session_producer_owner redis failed: {exc}')
            else:
                return False

        now_ts = time.time()
        async with self._lock:
            current = self._local_producer_owner.get(session_id)
            if current:
                expires_at = float(current.get('expires_at', 0.0))
                owner_id = str(current.get('worker_id', ''))
                if owner_id and owner_id != worker_id and expires_at > now_ts:
                    return False
            self._local_producer_owner[session_id] = {
                'worker_id': worker_id,
                'expires_at': now_ts + ttl,
            }
            return True

    async def release_session_producer_owner(self, session_id: str, worker_id: str) -> None:
        """Release owner token if currently owned by worker_id."""
        owner_key = self._producer_owner_key(session_id)

        if self.redis is not None and hasattr(self.redis, 'get') and hasattr(self.redis, 'delete'):
            try:
                current_owner = self._to_text(await self.redis.get(owner_key))
                if current_owner == worker_id:
                    await self.redis.delete(owner_key)
            except Exception as exc:
                logger.warning(f'release_session_producer_owner redis failed: {exc}')

        async with self._lock:
            current = self._local_producer_owner.get(session_id)
            if current and str(current.get('worker_id', '')) == worker_id:
                self._local_producer_owner.pop(session_id, None)

    async def get_session_producer_owner(self, session_id: str) -> Optional[str]:
        """Return current owner worker id if present."""
        owner_key = self._producer_owner_key(session_id)
        if self.redis is not None and hasattr(self.redis, 'get'):
            try:
                current_owner = self._to_text(await self.redis.get(owner_key))
                if current_owner:
                    return current_owner
            except Exception as exc:
                logger.warning(f'get_session_producer_owner redis failed: {exc}')

        now_ts = time.time()
        async with self._lock:
            current = self._local_producer_owner.get(session_id)
            if not current:
                return None
            expires_at = float(current.get('expires_at', 0.0))
            if expires_at <= now_ts:
                self._local_producer_owner.pop(session_id, None)
                return None
            owner_id = str(current.get('worker_id', ''))
            return owner_id or None

    async def append_events(self, session_id: str, stream: str, events: List[Dict[str, Any]]) -> None:
        if stream not in self.VALID_STREAMS:
            raise ValueError(f'invalid stream: {stream}')
        if not events:
            return

        serialized_events = [self._dumps(event) for event in events]

        async with self._lock:
            streams = self._local_streams.setdefault(session_id, {})
            bucket = streams.setdefault(stream, [])
            bucket.extend(serialized_events)
            if len(bucket) > self.max_stream_items:
                streams[stream] = bucket[-self.max_stream_items :]

        if self.redis is None:
            return

        key = self._stream_key(session_id, stream)
        try:
            for payload in serialized_events:
                await self.redis.rpush(key, payload)
            await self.redis.ltrim(key, -self.max_stream_items, -1)
            if hasattr(self.redis, 'expire'):
                await self.redis.expire(key, self.stream_ttl)
        except Exception as exc:
            logger.warning(f'append_events redis failed: stream={stream} error={exc}')

    async def get_events_since(
        self,
        session_id: str,
        stream: str,
        offset: int = 0,
        limit: int = 200,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if stream not in self.VALID_STREAMS:
            raise ValueError(f'invalid stream: {stream}')

        safe_offset = max(0, int(offset or 0))
        safe_limit = max(1, int(limit or 1))

        if self.redis is not None and hasattr(self.redis, 'llen') and hasattr(self.redis, 'lrange'):
            try:
                key = self._stream_key(session_id, stream)
                total = int(await self.redis.llen(key))
                if safe_offset >= total:
                    return [], safe_offset

                end = min(total - 1, safe_offset + safe_limit - 1)
                rows = await self.redis.lrange(key, safe_offset, end)
                events = [self._loads(row) for row in rows]
                return events, end + 1
            except Exception as exc:
                logger.warning(f'get_events_since redis failed: stream={stream} error={exc}')

        async with self._lock:
            rows = self._local_streams.get(session_id, {}).get(stream, [])
            total = len(rows)
            if safe_offset >= total:
                return [], safe_offset

            end = min(total - 1, safe_offset + safe_limit - 1)
            events = [self._loads(row) for row in rows[safe_offset : end + 1]]
            return events, end + 1

    async def get_latest_events(self, session_id: str, stream: str, limit: int = 100) -> List[Dict[str, Any]]:
        if stream not in self.VALID_STREAMS:
            raise ValueError(f'invalid stream: {stream}')

        safe_limit = max(1, int(limit or 1))

        if self.redis is not None and hasattr(self.redis, 'llen') and hasattr(self.redis, 'lrange'):
            try:
                key = self._stream_key(session_id, stream)
                total = int(await self.redis.llen(key))
                if total <= 0:
                    return []
                start = max(0, total - safe_limit)
                rows = await self.redis.lrange(key, start, total - 1)
                return [self._loads(row) for row in rows]
            except Exception as exc:
                logger.warning(f'get_latest_events redis failed: stream={stream} error={exc}')

        async with self._lock:
            rows = self._local_streams.get(session_id, {}).get(stream, [])
            if not rows:
                return []
            return [self._loads(row) for row in rows[-safe_limit:]]

    async def get_stream_size(self, session_id: str, stream: str) -> int:
        if stream not in self.VALID_STREAMS:
            raise ValueError(f'invalid stream: {stream}')

        if self.redis is not None and hasattr(self.redis, 'llen'):
            try:
                return int(await self.redis.llen(self._stream_key(session_id, stream)))
            except Exception as exc:
                logger.warning(f'get_stream_size redis failed: stream={stream} error={exc}')

        async with self._lock:
            rows = self._local_streams.get(session_id, {}).get(stream, [])
            return len(rows)


_runtime_state_store: Optional[SimulationRuntimeStateStore] = None


def init_simulation_runtime_state_store(
    redis_client=None,
    session_ttl: int = 24 * 3600,
    stream_ttl: int = 2 * 3600,
    max_stream_items: int = 5000,
) -> SimulationRuntimeStateStore:
    """Initialize singleton runtime state store."""
    global _runtime_state_store
    _runtime_state_store = SimulationRuntimeStateStore(
        redis_client=redis_client,
        session_ttl=session_ttl,
        stream_ttl=stream_ttl,
        max_stream_items=max_stream_items,
    )
    return _runtime_state_store


def get_simulation_runtime_state_store() -> SimulationRuntimeStateStore:
    """Get singleton runtime state store."""
    global _runtime_state_store
    if _runtime_state_store is None:
        _runtime_state_store = SimulationRuntimeStateStore(redis_client=None)
    return _runtime_state_store
