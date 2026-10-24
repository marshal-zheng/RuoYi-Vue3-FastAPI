import asyncio
import time

import pytest

from module_admin.service.simulation_runtime_state import SimulationRuntimeStateStore


@pytest.mark.asyncio
async def test_session_snapshot_roundtrip():
    store = SimulationRuntimeStateStore(redis_client=None)

    await store.save_session_snapshot(
        "session-1",
        {
            "status": "running",
            "engine_present": True,
            "message_count": 10,
        },
    )

    snapshot = await store.get_session_snapshot("session-1")
    assert snapshot is not None
    assert snapshot["session_id"] == "session-1"
    assert snapshot["status"] == "running"
    assert snapshot["message_count"] == 10
    assert "updated_at" in snapshot


@pytest.mark.asyncio
async def test_stream_offset_read():
    store = SimulationRuntimeStateStore(redis_client=None, max_stream_items=10)

    await store.append_events(
        "session-2",
        "messages",
        [{"id": 1}, {"id": 2}, {"id": 3}],
    )

    first_batch, offset = await store.get_events_since("session-2", "messages", offset=0, limit=2)
    assert [item["id"] for item in first_batch] == [1, 2]
    assert offset == 2

    second_batch, next_offset = await store.get_events_since("session-2", "messages", offset=offset, limit=10)
    assert [item["id"] for item in second_batch] == [3]
    assert next_offset == 3


@pytest.mark.asyncio
async def test_stream_trim_to_max_items():
    store = SimulationRuntimeStateStore(redis_client=None, max_stream_items=3)

    await store.append_events(
        "session-3",
        "alarms",
        [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}],
    )

    latest = await store.get_latest_events("session-3", "alarms", limit=10)
    assert [item["id"] for item in latest] == [2, 3, 4]

    size = await store.get_stream_size("session-3", "alarms")
    assert size == 3


@pytest.mark.asyncio
async def test_session_producer_owner_local_locking():
    store = SimulationRuntimeStateStore(redis_client=None)

    assert await store.claim_session_producer_owner("session-owner", "worker-a", ttl_seconds=10) is True
    assert await store.claim_session_producer_owner("session-owner", "worker-b", ttl_seconds=10) is False
    assert await store.claim_session_producer_owner("session-owner", "worker-a", ttl_seconds=10) is True
    assert await store.get_session_producer_owner("session-owner") == "worker-a"

    await store.release_session_producer_owner("session-owner", "worker-b")
    assert await store.get_session_producer_owner("session-owner") == "worker-a"

    await store.release_session_producer_owner("session-owner", "worker-a")
    assert await store.get_session_producer_owner("session-owner") is None
    assert await store.claim_session_producer_owner("session-owner", "worker-b", ttl_seconds=10) is True


@pytest.mark.asyncio
async def test_session_producer_owner_local_ttl_expiry():
    store = SimulationRuntimeStateStore(redis_client=None)

    assert await store.claim_session_producer_owner("session-owner-ttl", "worker-a", ttl_seconds=1) is True
    assert await store.claim_session_producer_owner("session-owner-ttl", "worker-b", ttl_seconds=1) is False

    await asyncio.sleep(1.1)
    assert await store.claim_session_producer_owner("session-owner-ttl", "worker-b", ttl_seconds=1) is True
    assert await store.get_session_producer_owner("session-owner-ttl") == "worker-b"


class _FakeRedisOwnerLock:
    def __init__(self):
        self._data = {}

    def _cleanup(self, key):
        current = self._data.get(key)
        if not current:
            return
        expires_at = current.get("expires_at")
        if expires_at and expires_at <= time.time():
            self._data.pop(key, None)

    async def get(self, key):
        self._cleanup(key)
        current = self._data.get(key)
        return None if not current else current["value"]

    async def set(self, key, value, ex=None, nx=False):
        self._cleanup(key)
        if nx and key in self._data:
            return False
        expires_at = time.time() + int(ex) if ex else None
        self._data[key] = {"value": value, "expires_at": expires_at}
        return True

    async def expire(self, key, ttl_seconds):
        self._cleanup(key)
        if key not in self._data:
            return False
        self._data[key]["expires_at"] = time.time() + int(ttl_seconds)
        return True

    async def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self._data:
                removed += 1
                self._data.pop(key, None)
        return removed


@pytest.mark.asyncio
async def test_session_producer_owner_with_redis_lock():
    redis_client = _FakeRedisOwnerLock()
    store = SimulationRuntimeStateStore(redis_client=redis_client)

    assert await store.claim_session_producer_owner("session-redis-owner", "worker-a", ttl_seconds=5) is True
    assert await store.claim_session_producer_owner("session-redis-owner", "worker-b", ttl_seconds=5) is False
    assert await store.claim_session_producer_owner("session-redis-owner", "worker-a", ttl_seconds=5) is True
    assert await store.get_session_producer_owner("session-redis-owner") == "worker-a"

    await store.release_session_producer_owner("session-redis-owner", "worker-a")
    assert await store.get_session_producer_owner("session-redis-owner") is None
    assert await store.claim_session_producer_owner("session-redis-owner", "worker-b", ttl_seconds=5) is True
