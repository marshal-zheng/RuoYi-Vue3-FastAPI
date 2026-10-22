"""Run against a local Redis with RUOYI_SESSION_REDIS_TEST_URL; all keys are UUID-namespaced."""
import asyncio
import os
import time
import uuid

import pytest
from redis import asyncio as aioredis

from config.env import AppConfig
from exceptions.exception import AuthException
from modules.identity.application.services.security_token_service import SecurityTokenService


class _NamespacedPipeline:
    def __init__(self, pipe, prefix):
        self.pipe, self.prefix = pipe, prefix

    async def __aenter__(self):
        await self.pipe.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self.pipe.__aexit__(*args)

    async def watch(self, *keys):
        await self.pipe.watch(*(self.prefix + key for key in keys))

    async def get(self, key):
        return await self.pipe.get(self.prefix + key)

    def multi(self):
        self.pipe.multi()

    def set(self, key, value, **kwargs):
        self.pipe.set(self.prefix + key, value, **kwargs)

    def delete(self, *keys):
        self.pipe.delete(*(self.prefix + key for key in keys))

    async def execute(self):
        return await self.pipe.execute()


class _NamespacedRedis:
    def __init__(self, redis, prefix):
        self.redis, self.prefix = redis, prefix

    def pipeline(self, **kwargs):
        return _NamespacedPipeline(self.redis.pipeline(**kwargs), self.prefix)

    async def get(self, key):
        return await self.redis.get(self.prefix + key)

    async def delete(self, *keys):
        return await self.redis.delete(*(self.prefix + key for key in keys))

    async def ttl(self, key):
        return await self.redis.ttl(self.prefix + key)


@pytest.fixture
async def sessions(monkeypatch):
    url = os.environ.get('RUOYI_SESSION_REDIS_TEST_URL')
    if not url:
        pytest.skip('Set RUOYI_SESSION_REDIS_TEST_URL to run isolated Redis session regression tests')
    redis = aioredis.from_url(url, decode_responses=True)
    await redis.ping()
    prefix = f'qa:session-renewal:{uuid.uuid4().hex}:'
    scoped = _NamespacedRedis(redis, prefix)
    monkeypatch.setattr(AppConfig, 'app_same_time_login', False)
    try:
        yield SecurityTokenService(scoped), scoped
    finally:
        keys = [key async for key in redis.scan_iter(match=prefix + '*')]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


def _session(**overrides):
    return dict(session_id='s1', token='access-old', refresh_token='refresh-old', user_id='1',
                user_name='qa', dept_name=None, login_info={}, expires_at=int(time.time()) + 60,
                refresh_expires_at=int(time.time()) + 3600, **overrides)


@pytest.mark.asyncio
async def test_refresh_authority_survives_access_expiry(sessions):
    service, redis = sessions
    await service.register_user_session(**_session())
    assert 0 < await redis.ttl('access_token:s1') <= 60
    assert await redis.ttl('sec:user_session:s1') > 3500
    assert await redis.ttl('sec:active_session:1') > 3500
    await redis.delete('access_token:s1')
    update = _session()
    update.update(token='access-new', refresh_token='refresh-new', previous_refresh_token='refresh-old')
    await service.register_user_session(**update)
    assert await redis.get('access_token:s1') == 'access-new'


@pytest.mark.asyncio
async def test_rotated_refresh_cannot_be_replayed(sessions):
    service, redis = sessions
    await service.register_user_session(**_session())
    update = _session()
    update.update(token='access-new', refresh_token='refresh-new', previous_refresh_token='refresh-old')
    await service.register_user_session(**update)
    with pytest.raises(AuthException):
        await service.register_user_session(**update)
    assert await redis.get('access_token:s1') == 'access-new'


@pytest.mark.asyncio
@pytest.mark.parametrize('reason', ['logout', 'replaced', 'expired'])
async def test_invalidated_session_cannot_be_restored(sessions, reason):
    service, redis = sessions
    await service.register_user_session(**_session())
    if reason == 'logout':
        await service.revoke_user_session('s1')
    elif reason == 'expired':
        await redis.delete('sec:user_session:s1')
    else:
        update = _session()
        update.update(session_id='s2', token='second-access', refresh_token='second-refresh')
        await service.register_user_session(**update)
    update = _session()
    update.update(token='access-new', refresh_token='refresh-new', previous_refresh_token='refresh-old')
    with pytest.raises(AuthException):
        await service.register_user_session(**update)
    assert await redis.get('access_token:s1') != 'access-new'


@pytest.mark.asyncio
async def test_concurrent_rotation_consumes_refresh_once(sessions):
    service, _ = sessions
    await service.register_user_session(**_session())
    update = _session()
    update.update(token='access-new', refresh_token='refresh-new', previous_refresh_token='refresh-old')
    results = await asyncio.gather(*(service.register_user_session(**update) for _ in range(8)), return_exceptions=True)
    assert sum(result is None for result in results) == 1
    assert sum(isinstance(result, AuthException) for result in results) == 7


@pytest.mark.asyncio
async def test_revoke_wins_against_concurrent_refresh(sessions):
    service, redis = sessions
    await service.register_user_session(**_session())
    update = _session()
    update.update(token='access-new', refresh_token='refresh-new', previous_refresh_token='refresh-old')
    await asyncio.gather(service.register_user_session(**update), service.revoke_user_session('s1'), return_exceptions=True)
    assert await redis.get('access_token:s1') is None
    assert await redis.get('sec:user_session:s1') is None


@pytest.mark.asyncio
async def test_revoking_old_session_preserves_new_active_pointer(sessions, monkeypatch):
    service, redis = sessions
    monkeypatch.setattr(AppConfig, 'app_same_time_login', True)
    await service.register_user_session(**_session())
    update = _session()
    update.update(session_id='s2', token='second-access', refresh_token='second-refresh')
    await service.register_user_session(**update)
    await service.revoke_user_session('s1')
    assert await redis.get('sec:active_session:1') == 's2'
    assert await redis.get('access_token:s2') == 'second-access'
