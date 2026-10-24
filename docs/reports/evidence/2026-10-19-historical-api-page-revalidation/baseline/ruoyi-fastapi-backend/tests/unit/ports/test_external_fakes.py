import pytest

from events.domain_events import DomainEvent
from tests.fakes.external_fakes import (
    InMemoryAuditLogger,
    InMemoryCacheProvider,
    InMemoryEventBus,
    InMemoryRedisClient,
    assert_external_fake_contracts,
)


def test_external_fakes_satisfy_protocol_contracts() -> None:
    assert_external_fake_contracts()


@pytest.mark.asyncio
async def test_in_memory_redis_supports_core_operations() -> None:
    redis = InMemoryRedisClient()

    assert await redis.ping() is True
    assert await redis.set('k1', 'v1') is True
    assert await redis.get('k1') == 'v1'
    assert await redis.setnx('k1', 'ignored') == 0
    assert await redis.setnx('k2', 'v2') == 1
    assert await redis.get('k2') == 'v2'

    assert await redis.rpush('stream', 'a', 'b', 'c') == 3
    assert await redis.llen('stream') == 3
    assert await redis.lrange('stream', 0, -1) == ['a', 'b', 'c']
    assert await redis.ltrim('stream', 1, 2) is True
    assert await redis.lrange('stream', 0, -1) == ['b', 'c']

    assert await redis.delete('k1', 'k2') == 2
    assert await redis.get('k1') is None


@pytest.mark.asyncio
async def test_in_memory_cache_audit_and_event_bus() -> None:
    cache = InMemoryCacheProvider()
    await cache.set('x', {'ok': True})
    assert await cache.get('x') == {'ok': True}
    await cache.invalidate('x')
    assert await cache.get('x') is None

    audit = InMemoryAuditLogger()
    await audit.record('create', 'tester', 'entity:1', {'name': 'demo'})
    assert audit.entries[0]['action'] == 'create'

    bus = InMemoryEventBus()
    received = []

    async def handler(event: DomainEvent):
        received.append(dict(event.payload))

    bus.subscribe('user.created', handler)
    await bus.publish(
        DomainEvent.create(
            event_type='user.created',
            aggregate_type='user',
            aggregate_id='1',
            payload={'user_id': 1},
        )
    )
    assert received == [{'user_id': 1}]
