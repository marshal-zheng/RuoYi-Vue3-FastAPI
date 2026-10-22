import base64
from datetime import timedelta
from datetime import datetime, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from config.env import SecurityConfig
from exceptions.exception import AuthException
from modules.identity.application.services.security_token_service import SecurityTokenService


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


class _RedisStub:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    async def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self.store:
                self.store.pop(key, None)
                removed += 1
        return removed

    async def rpush(self, key, *values):
        bucket = self.store.setdefault(key, [])
        bucket.extend(values)
        return len(bucket)

    async def ltrim(self, key, start, end):
        bucket = self.store.get(key, [])
        if not isinstance(bucket, list):
            return True
        size = len(bucket)
        if size == 0:
            return True
        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)
        if start > end:
            self.store[key] = []
            return True
        self.store[key] = bucket[start : end + 1]
        return True

    async def lrange(self, key, start, end):
        bucket = self.store.get(key, [])
        if not isinstance(bucket, list):
            return []
        size = len(bucket)
        if size == 0:
            return []
        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)
        if start > end:
            return []
        return bucket[start : end + 1]


@pytest.mark.asyncio
async def test_issue_and_verify_access_token_enforces_max_lifetime():
    redis = _RedisStub()
    service = SecurityTokenService(redis)

    token = await service.issue_access_token(
        subject='user:1',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=9999,
        token_use='user_access',
        claims={'user_id': '1'},
    )
    payload = jwt.decode(token, options={'verify_signature': False})
    assert payload.get('iss') == SecurityConfig.security_jwt_issuer
    assert payload.get('aud') == SecurityConfig.security_jwt_audience_api
    assert payload.get('jti')
    assert payload.get('exp') - payload.get('iat') <= SecurityConfig.security_jwt_max_expire_seconds

    verified = await service.verify_access_token(
        token,
        audience=SecurityConfig.security_jwt_audience_api,
        enforce_replay=False,
        expected_use='user_access',
    )
    assert verified.get('user_id') == '1'


@pytest.mark.asyncio
async def test_private_key_jwt_client_assertion_verification():
    redis = _RedisStub()
    service = SecurityTokenService(redis)
    client_id = 'client-test'

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    numbers = public_key.public_numbers()
    jwk = {
        'kty': 'RSA',
        'kid': 'client-key-1',
        'alg': 'RS256',
        'use': 'sig',
        'n': _b64url(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, 'big')),
        'e': _b64url(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, 'big')),
    }

    await service.register_client_jwk(
        client_id=client_id,
        tenant_id='t-1',
        integration_id='i-1',
        jwk=jwk,
        enabled=True,
    )

    now = datetime.now(timezone.utc)
    assertion = jwt.encode(
        {
            'iss': client_id,
            'sub': client_id,
            'aud': '/auth/m2m/token',
            'jti': 'assertion-1',
            'iat': now,
            'exp': now + timedelta(seconds=30),
        },
        key=private_key,
        algorithm='RS256',
        headers={'kid': 'client-key-1'},
    )

    verified_client_id, payload, record = await service.verify_private_key_jwt(
        assertion=assertion,
        audience=['/auth/m2m/token', 'http://testserver/auth/m2m/token'],
    )
    assert verified_client_id == client_id
    assert payload.get('iss') == client_id
    assert record.get('kid') == 'client-key-1'


@pytest.mark.asyncio
async def test_embed_grant_single_use_and_origin_binding():
    redis = _RedisStub()
    service = SecurityTokenService(redis)
    origin = 'http://localhost:5173'

    await service.upsert_embed_policy(
        tenant_id='tenant-a',
        integration_id='integration-a',
        origin=origin,
        path_pattern='/embed',
        enabled=True,
    )

    grant, _ = await service.issue_embed_grant(
        tenant_id='tenant-a',
        integration_id='integration-a',
        origin=origin,
        path='/embed/dashboard',
        subject='user:1001',
        request_id='req-1',
        source_ip='127.0.0.1',
    )

    access_token, _, claims = await service.exchange_embed_grant(
        embed_grant=grant,
        origin=origin,
        request_id='req-2',
        source_ip='127.0.0.1',
    )
    assert access_token
    assert claims.get('tenant_id') == 'tenant-a'

    with pytest.raises(AuthException):
        await service.exchange_embed_grant(
            embed_grant=grant,
            origin=origin,
            request_id='req-3',
            source_ip='127.0.0.1',
        )


@pytest.mark.asyncio
async def test_ws_ticket_single_use():
    redis = _RedisStub()
    service = SecurityTokenService(redis)
    origin = 'http://localhost:5173'

    await redis.set('sec:user_session:login-a', '{"userId":"1"}')
    await redis.set('sec:active_session:1', 'login-a')
    ticket, _ = await service.issue_ws_ticket(subject='user:1', origin=origin, session_id='session-a', auth_session_id='login-a')
    first = await service.consume_ws_ticket(
        ticket=ticket,
        origin=origin,
        session_id='session-a',
        request_id='req-ws-1',
        source_ip='127.0.0.1',
    )
    assert first.get('sessionId') == 'session-a'

    with pytest.raises(AuthException):
        await service.consume_ws_ticket(
            ticket=ticket,
            origin=origin,
            session_id='session-a',
            request_id='req-ws-2',
            source_ip='127.0.0.1',
        )


@pytest.mark.asyncio
async def test_csrf_token_issue_and_validate():
    redis = _RedisStub()
    service = SecurityTokenService(redis)

    token, _ = await service.issue_csrf_token('user:1')
    assert await service.validate_csrf_token('user:1', token) is True
    assert await service.validate_csrf_token('user:1', 'bad-token') is False


@pytest.mark.asyncio
@pytest.mark.parametrize('invalidated', ['revoked', 'replaced'])
async def test_unused_ws_ticket_cannot_restore_an_invalidated_login(invalidated):
    redis = _RedisStub()
    service = SecurityTokenService(redis)
    await redis.set('sec:user_session:login-a', '{"userId":"1"}')
    await redis.set('sec:active_session:1', 'login-a')
    ticket, _ = await service.issue_ws_ticket(
        subject='1', origin='http://localhost', session_id='simulation-a', auth_session_id='login-a',
    )
    if invalidated == 'revoked':
        await redis.delete('sec:user_session:login-a')
    else:
        await redis.set('sec:active_session:1', 'login-b')
    with pytest.raises(AuthException):
        await service.consume_ws_ticket(ticket=ticket, origin='http://localhost', session_id='simulation-a',
                                        request_id='qa', source_ip='127.0.0.1')


@pytest.mark.asyncio
async def test_ws_ticket_requires_a_live_authenticated_login():
    service = SecurityTokenService(_RedisStub())
    with pytest.raises(AuthException):
        await service.issue_ws_ticket(subject='1', origin='http://localhost', session_id='simulation-a', auth_session_id='')
