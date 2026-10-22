from __future__ import annotations

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from jwt import InvalidTokenError
from redis.exceptions import WatchError

from config.enums import RedisInitKeyConfig
from config.env import AppConfig, SecurityConfig
from exceptions.exception import AuthException, ValidationException
from utils.log_util import logger


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _to_text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in (raw or '').split(',') if item.strip()]


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f'{parsed.scheme}://{parsed.netloc}'


def _normalize_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    parsed = urlparse(origin)
    if parsed.scheme and parsed.netloc:
        return f'{parsed.scheme}://{parsed.netloc}'
    return origin.rstrip('/')


def _normalize_path(path: str) -> str:
    normalized = (path or '/').strip() or '/'
    if not normalized.startswith('/'):
        normalized = f'/{normalized}'
    return normalized


def _canonical_alg(value: str) -> str:
    raw = (value or '').strip()
    if not raw:
        return raw
    upper = raw.upper()
    if upper == 'EDDSA':
        return 'EdDSA'
    return upper


@dataclass
class _SigningKeyRecord:
    kid: str
    alg: str
    private_key: Any
    public_key: Any
    public_jwk: dict[str, Any]
    status: str
    activated_at: datetime
    retired_at: datetime | None = None


class SecurityTokenService:
    """Security hard-cut token service."""

    _CLIENT_ASSERTION_ALGS = {'RS256', 'RS384', 'RS512', 'PS256', 'PS384', 'PS512', 'EdDSA', 'ES256'}

    def __init__(self, redis_client: Any):
        self.redis_client = redis_client
        self.issuer = (SecurityConfig.security_jwt_issuer or 'ruoyi-fastapi').strip() or 'ruoyi-fastapi'
        self.default_algorithm = _canonical_alg(SecurityConfig.security_jwt_sign_algorithm or 'RS256')
        self.allowed_algorithms = {_canonical_alg(item) for item in _parse_csv(SecurityConfig.security_jwt_allowed_algorithms)}
        if not self.allowed_algorithms:
            self.allowed_algorithms = {'RS256', 'EdDSA'}
        self.max_token_seconds = max(1, int(SecurityConfig.security_jwt_max_expire_seconds))
        self.clock_skew_seconds = max(0, int(SecurityConfig.security_jwt_clock_skew_seconds))
        self.key_retire_grace_seconds = max(60, int(SecurityConfig.security_key_rotation_grace_seconds))
        self.alert_threshold = max(1, int(SecurityConfig.security_event_alert_threshold))
        self.allowed_origins = {item for item in (_normalize_origin(raw) for raw in _parse_csv(SecurityConfig.security_allowed_origins)) if item}
        self._signing_keys: dict[str, _SigningKeyRecord] = {}
        self._active_kid: str | None = None
        self._init_signing_keyring()

    def _require_redis(self) -> Any:
        if self.redis_client is None:
            raise RuntimeError('Redis client is not initialized')
        return self.redis_client

    def _init_signing_keyring(self) -> None:
        configured_private = (SecurityConfig.security_jwt_private_key_pem or '').strip()
        configured_public = (SecurityConfig.security_jwt_public_key_pem or '').strip()
        algorithm = self.default_algorithm

        if configured_private and configured_public:
            private_key = serialization.load_pem_private_key(configured_private.encode('utf-8'), password=None)
            public_key = serialization.load_pem_public_key(configured_public.encode('utf-8'))
            self._register_signing_key(private_key=private_key, public_key=public_key, algorithm=algorithm, make_active=True)
            return

        private_key, public_key = self._generate_key_pair(algorithm)
        logger.warning('未配置 SECURITY_JWT_PRIVATE_KEY_PEM/SECURITY_JWT_PUBLIC_KEY_PEM，已生成内存密钥')
        self._register_signing_key(private_key=private_key, public_key=public_key, algorithm=algorithm, make_active=True)

    def _generate_key_pair(self, algorithm: str) -> tuple[Any, Any]:
        normalized = _canonical_alg(algorithm)
        if normalized.startswith('RS'):
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            return private_key, private_key.public_key()
        if normalized == 'EdDSA':
            private_key = ed25519.Ed25519PrivateKey.generate()
            return private_key, private_key.public_key()
        raise RuntimeError(f'Unsupported signing algorithm: {algorithm}')

    def _register_signing_key(self, *, private_key: Any, public_key: Any, algorithm: str, make_active: bool) -> _SigningKeyRecord:
        normalized_alg = _canonical_alg(algorithm)
        if normalized_alg not in self.allowed_algorithms:
            raise RuntimeError(f'Signing algorithm not allowed by whitelist: {normalized_alg}')
        public_jwk = self._build_public_jwk(public_key=public_key, algorithm=normalized_alg)
        kid = f'k-{hashlib.sha256(json.dumps(public_jwk, sort_keys=True).encode("utf-8")).hexdigest()[:16]}'
        public_jwk['kid'] = kid
        record = _SigningKeyRecord(
            kid=kid,
            alg=normalized_alg,
            private_key=private_key,
            public_key=public_key,
            public_jwk=public_jwk,
            status='active' if make_active else 'retiring',
            activated_at=_utc_now(),
        )
        self._signing_keys[kid] = record
        if make_active:
            self._active_kid = kid
        return record

    @staticmethod
    def _build_public_jwk(*, public_key: Any, algorithm: str) -> dict[str, Any]:
        if algorithm.startswith('RS'):
            numbers = public_key.public_numbers()
            n = _b64url(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, 'big'))
            e = _b64url(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, 'big'))
            return {'kty': 'RSA', 'use': 'sig', 'alg': algorithm, 'n': n, 'e': e}
        if algorithm == 'EdDSA':
            raw = public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            return {'kty': 'OKP', 'crv': 'Ed25519', 'use': 'sig', 'alg': 'EdDSA', 'x': _b64url(raw)}
        raise RuntimeError(f'Unsupported JWK algorithm: {algorithm}')

    def _active_signing_key(self) -> _SigningKeyRecord:
        if not self._active_kid:
            raise RuntimeError('No active signing key available')
        record = self._signing_keys.get(self._active_kid)
        if record is None or record.status == 'revoked':
            raise RuntimeError('Active signing key is not available')
        return record

    def _verification_key_for_token(self, token: str) -> _SigningKeyRecord:
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise AuthException(user_message='用户token不合法', developer_message=f'Invalid token header: {exc}') from exc

        kid = str(header.get('kid') or '')
        alg = _canonical_alg(str(header.get('alg') or ''))
        if not kid or not alg:
            raise AuthException(user_message='用户token不合法', developer_message='Token header missing kid/alg')
        if alg not in self.allowed_algorithms:
            raise AuthException(user_message='用户token不合法', developer_message=f'Algorithm not allowed: {alg}')

        record = self._signing_keys.get(kid)
        if not record:
            raise AuthException(user_message='用户token不合法', developer_message=f'Unknown kid: {kid}')
        if record.status == 'revoked':
            raise AuthException(user_message='用户token已失效，请重新登录', developer_message=f'Revoked kid: {kid}')
        if record.alg != alg:
            raise AuthException(user_message='用户token不合法', developer_message='Header algorithm mismatch key record')
        if record.retired_at and _utc_now() > record.retired_at:
            raise AuthException(user_message='用户token已失效，请重新登录', developer_message='Signing key retired')
        return record

    def list_signing_keys(self) -> list[dict[str, Any]]:
        keys: list[dict[str, Any]] = []
        for record in self._signing_keys.values():
            keys.append(
                {
                    'kid': record.kid,
                    'alg': record.alg,
                    'status': record.status,
                    'activatedAt': record.activated_at.isoformat(),
                    'retiredAt': record.retired_at.isoformat() if record.retired_at else None,
                }
            )
        return sorted(keys, key=lambda item: item['activatedAt'], reverse=True)

    async def rotate_signing_key(self, *, algorithm: str | None = None, operator: str = 'system') -> dict[str, Any]:
        alg = _canonical_alg(algorithm or self.default_algorithm)
        previous = self._active_signing_key()
        previous.status = 'retiring'
        previous.retired_at = _utc_now() + timedelta(seconds=self.key_retire_grace_seconds)

        private_key, public_key = self._generate_key_pair(alg)
        current = self._register_signing_key(private_key=private_key, public_key=public_key, algorithm=alg, make_active=True)
        await self.log_security_event(
            event_type='signing_key_rotated',
            subject=operator,
            reason='manual_rotation',
            payload={'previousKid': previous.kid, 'currentKid': current.kid},
        )
        return {'previousKid': previous.kid, 'currentKid': current.kid, 'algorithm': current.alg}

    async def revoke_signing_key(self, *, kid: str, operator: str = 'system') -> None:
        record = self._signing_keys.get(kid)
        if record is None:
            raise ValidationException(user_message='密钥不存在', developer_message=f'Unknown signing kid: {kid}')
        if record.status == 'revoked':
            return
        record.status = 'revoked'
        record.retired_at = _utc_now()

        if self._active_kid == kid:
            candidates = [item for item in self._signing_keys.values() if item.status in {'active', 'retiring'} and item.kid != kid]
            if candidates:
                candidates.sort(key=lambda item: item.activated_at, reverse=True)
                candidates[0].status = 'active'
                self._active_kid = candidates[0].kid
            else:
                private_key, public_key = self._generate_key_pair(self.default_algorithm)
                created = self._register_signing_key(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm=self.default_algorithm,
                    make_active=True,
                )
                self._active_kid = created.kid

        await self.log_security_event(
            event_type='signing_key_revoked',
            subject=operator,
            reason='emergency_revoke',
            payload={'kid': kid},
        )

    def get_jwks(self) -> dict[str, Any]:
        now = _utc_now()
        keys = []
        for record in self._signing_keys.values():
            if record.status == 'revoked':
                continue
            if record.retired_at and now > record.retired_at:
                continue
            keys.append(dict(record.public_jwk))
        return {'keys': keys}

    def _encode_with_active_key(self, payload: dict[str, Any]) -> str:
        active = self._active_signing_key()
        return jwt.encode(
            payload=payload,
            key=active.private_key,
            algorithm=active.alg,
            headers={'kid': active.kid, 'typ': 'JWT'},
        )

    async def issue_access_token(
        self,
        *,
        subject: str,
        audience: str,
        expires_seconds: int,
        token_use: str,
        max_expire_seconds: int | None = None,
        claims: dict[str, Any] | None = None,
    ) -> str:
        now = _utc_now()
        lifetime_limit = self.max_token_seconds if max_expire_seconds is None else max(1, int(max_expire_seconds))
        actual_expire_seconds = min(max(1, int(expires_seconds)), lifetime_limit)
        payload: dict[str, Any] = {
            'iss': self.issuer,
            'aud': audience,
            'sub': subject,
            'jti': uuid.uuid4().hex,
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=actual_expire_seconds),
            'token_use': token_use,
        }
        if claims:
            payload.update(claims)
        return self._encode_with_active_key(payload)

    async def verify_access_token(
        self,
        token: str,
        *,
        audience: str,
        enforce_replay: bool = False,
        expected_use: str | None = None,
        enforce_session: bool = False,
        max_lifetime_seconds: int | None = None,
    ) -> dict[str, Any]:
        record = self._verification_key_for_token(token)
        try:
            payload = jwt.decode(
                token,
                key=record.public_key,
                algorithms=[record.alg],
                audience=audience,
                issuer=self.issuer,
                leeway=self.clock_skew_seconds,
                options={'require': ['iss', 'aud', 'sub', 'jti', 'iat', 'nbf', 'exp']},
            )
        except InvalidTokenError as exc:
            raise AuthException(user_message='用户token不合法', developer_message=f'Invalid token: {exc}') from exc

        if expected_use and payload.get('token_use') != expected_use:
            raise AuthException(user_message='用户token不合法', developer_message='Unexpected token_use')

        issued_at = _coerce_int(payload.get('iat'))
        expires_at = _coerce_int(payload.get('exp'))
        lifetime_limit = self.max_token_seconds if max_lifetime_seconds is None else max(1, int(max_lifetime_seconds))
        if issued_at > 0 and expires_at > 0 and expires_at - issued_at > lifetime_limit + self.clock_skew_seconds:
            raise AuthException(user_message='用户token不合法', developer_message='Token lifetime exceeds max policy')

        if enforce_replay:
            await self._assert_first_use('sec:jti', str(payload.get('jti')), payload.get('exp'))
        if enforce_session:
            await self._assert_user_session_active(payload=payload, token=token)
        return payload

    async def _assert_first_use(self, prefix: str, identifier: str, exp_value: Any) -> None:
        if not identifier:
            raise AuthException(user_message='用户token不合法', developer_message='Missing identifier for replay check')
        expires_epoch = _coerce_int(exp_value)
        now_epoch = int(_utc_now().timestamp())
        ttl = max(1, expires_epoch - now_epoch)
        replay_key = f'{prefix}:{identifier}'
        inserted = await self._require_redis().set(replay_key, '1', ex=ttl, nx=True)
        if not inserted:
            raise AuthException(user_message='用户token已失效，请重新登录', developer_message=f'Replay detected: {replay_key}')

    async def _assert_user_session_active(self, *, payload: dict[str, Any], token: str) -> None:
        session_id = str(payload.get('session_id') or payload.get('sessionId') or '')
        if not session_id:
            return
        key = f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}'
        cached_token = _to_text(await self._require_redis().get(key))
        if not cached_token or cached_token != token:
            raise AuthException(user_message='用户token已失效，请重新登录', developer_message='Session not active or token mismatch')

    async def register_user_session(
        self,
        *,
        session_id: str,
        token: str,
        refresh_token: str,
        user_id: str,
        user_name: str,
        dept_name: str | None,
        login_info: dict[str, Any] | None,
        expires_at: Any,
        refresh_expires_at: Any,
        previous_refresh_token: str | None = None,
    ) -> None:
        if not session_id:
            raise ValidationException(user_message='会话标识不能为空', developer_message='Missing session_id')

        now = int(_utc_now().timestamp())
        access_ttl = max(1, _coerce_int(expires_at) - now)
        refresh_ttl = max(1, _coerce_int(refresh_expires_at) - now)
        redis = self._require_redis()
        token_key = f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}'
        meta_key = f'sec:user_session:{session_id}'
        active_key = f'sec:active_session:{user_id}'
        metadata = json.dumps(
            {
                'sessionId': session_id,
                'userId': user_id,
                'userName': user_name,
                'deptName': dept_name,
                'loginInfo': login_info or {},
                'refreshDigest': hashlib.sha256(refresh_token.encode()).hexdigest(),
                'updatedAt': _utc_now().isoformat(),
            },
            ensure_ascii=False,
        )
        # Refresh, logout and replacement login must agree on the same session.
        # WATCH prevents a refresh from recreating a concurrently revoked session.
        async with redis.pipeline(transaction=True) as pipe:
            while True:
                try:
                    await pipe.watch(meta_key, active_key)
                    previous_session = _to_text(await pipe.get(active_key))
                    if previous_refresh_token is not None:
                        raw_meta = _to_text(await pipe.get(meta_key))
                        current = json.loads(raw_meta) if raw_meta else {}
                        expected = hashlib.sha256(previous_refresh_token.encode()).hexdigest()
                        if (
                            current.get('userId') != user_id
                            or current.get('refreshDigest') != expected
                            or (not AppConfig.app_same_time_login and previous_session != session_id)
                        ):
                            raise AuthException(
                                user_message='登录状态已失效，请重新登录',
                                developer_message='Refresh session revoked, expired, replaced or already rotated',
                            )
                    pipe.multi()
                    if not AppConfig.app_same_time_login and previous_session and previous_session != session_id:
                        pipe.delete(
                            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{previous_session}',
                            f'sec:user_session:{previous_session}',
                        )
                    pipe.set(token_key, token, ex=access_ttl)
                    pipe.set(meta_key, metadata, ex=refresh_ttl)
                    pipe.set(active_key, session_id, ex=refresh_ttl)
                    await pipe.execute()
                    return
                except WatchError:
                    continue

    async def revoke_user_session(self, session_id: str) -> None:
        if not session_id:
            return
        redis = self._require_redis()
        meta_key = f'sec:user_session:{session_id}'
        async with redis.pipeline(transaction=True) as pipe:
            while True:
                try:
                    await pipe.watch(meta_key)
                    raw_meta = _to_text(await pipe.get(meta_key))
                    user_id = str(json.loads(raw_meta).get('userId') or '') if raw_meta else ''
                    active_key = f'sec:active_session:{user_id}'
                    if user_id:
                        await pipe.watch(active_key)
                    active_session = _to_text(await pipe.get(active_key)) if user_id else ''
                    pipe.multi()
                    pipe.delete(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}', meta_key)
                    if user_id and active_session == session_id:
                        pipe.delete(active_key)
                    await pipe.execute()
                    return
                except WatchError:
                    continue

    async def extract_user_context_from_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = await self.verify_access_token(
                token,
                audience=SecurityConfig.security_jwt_audience_api,
                enforce_replay=False,
            )
        except Exception:
            return None
        user_id = payload.get('user_id')
        if user_id is None:
            subject = str(payload.get('sub') or '')
            if subject.startswith('user:'):
                user_id = subject.split(':', 1)[1]
        return {
            'userId': str(user_id) if user_id is not None else '',
            'userName': str(payload.get('user_name') or ''),
            'sessionId': str(payload.get('session_id') or ''),
            'tenantId': str(payload.get('tenant_id') or ''),
            'tokenUse': str(payload.get('token_use') or ''),
        }

    async def log_security_event(
        self,
        *,
        event_type: str,
        subject: str,
        reason: str,
        request_id: str = '',
        source_ip: str = '',
        payload: dict[str, Any] | None = None,
    ) -> None:
        redis = self._require_redis()
        entry = {
            'eventType': event_type,
            'subject': subject,
            'reason': reason,
            'requestId': request_id,
            'sourceIp': source_ip,
            'payload': payload or {},
            'timestamp': _utc_now().isoformat(),
        }
        await redis.rpush('sec:security_events', json.dumps(entry, ensure_ascii=False))
        await redis.ltrim('sec:security_events', -10000, -1)

        minute_bucket = int(_utc_now().timestamp()) // 60
        counter_key = f'sec:security_event_counter:{event_type}:{minute_bucket}'
        count_value = await redis.get(counter_key)
        count = _coerce_int(_to_text(count_value))
        count += 1
        await redis.set(counter_key, str(count), ex=120)
        if count >= self.alert_threshold:
            logger.error(
                'security_alert event={} count={} threshold={} request_id={}',
                event_type,
                count,
                self.alert_threshold,
                request_id,
            )
        logger.warning('security_event={} subject={} reason={} request_id={}', event_type, subject, reason, request_id)

    async def get_security_event_report(self, limit: int = 200) -> dict[str, Any]:
        redis = self._require_redis()
        rows = await redis.lrange('sec:security_events', max(-10000, -abs(limit)), -1)
        events = []
        summary: dict[str, int] = {}
        for row in rows:
            try:
                parsed = json.loads(_to_text(row))
            except Exception:
                continue
            events.append(parsed)
            event_type = str(parsed.get('eventType') or 'unknown')
            summary[event_type] = summary.get(event_type, 0) + 1
        return {'summary': summary, 'events': events}

    async def upsert_embed_policy(
        self,
        *,
        tenant_id: str,
        integration_id: str,
        origin: str,
        path_pattern: str,
        enabled: bool,
    ) -> None:
        normalized_origin = _normalize_origin(origin)
        normalized_pattern = _normalize_path(path_pattern or '/')
        key = f'sec:embed_policy:{tenant_id}:{integration_id}:{normalized_origin}'
        value = {
            'tenantId': tenant_id,
            'integrationId': integration_id,
            'origin': normalized_origin,
            'pathPattern': normalized_pattern,
            'enabled': enabled,
            'updatedAt': _utc_now().isoformat(),
        }
        await self._require_redis().set(key, json.dumps(value, ensure_ascii=False))
        await self.log_security_event(
            event_type='embed_policy_updated',
            subject='system',
            reason='upsert_embed_policy',
            payload=value,
        )

    @staticmethod
    def _path_matches(pattern: str, path: str) -> bool:
        normalized_pattern = _normalize_path(pattern)
        normalized_path = _normalize_path(path)
        if normalized_pattern in {'*', '/*'}:
            return True
        if normalized_pattern.endswith('*'):
            return normalized_path.startswith(normalized_pattern[:-1])
        return normalized_path.startswith(normalized_pattern)

    async def _is_embed_origin_allowed(self, *, tenant_id: str, integration_id: str, origin: str, path: str) -> bool:
        key = f'sec:embed_policy:{tenant_id}:{integration_id}:{_normalize_origin(origin)}'
        raw = await self._require_redis().get(key)
        if not raw:
            return False
        data = json.loads(_to_text(raw))
        if not data.get('enabled', False):
            return False
        return self._path_matches(str(data.get('pathPattern') or '/'), path)

    async def issue_embed_grant(
        self,
        *,
        tenant_id: str,
        integration_id: str,
        origin: str,
        path: str,
        subject: str,
        request_id: str,
        source_ip: str,
    ) -> tuple[str, int]:
        normalized_origin = _normalize_origin(origin)
        normalized_path = _normalize_path(path)
        if not await self._is_embed_origin_allowed(
            tenant_id=tenant_id,
            integration_id=integration_id,
            origin=str(normalized_origin),
            path=normalized_path,
        ):
            await self.log_security_event(
                event_type='embed_origin_denied',
                subject=subject,
                reason='origin_or_path_not_allowed',
                request_id=request_id,
                source_ip=source_ip,
                payload={'tenantId': tenant_id, 'integrationId': integration_id, 'origin': normalized_origin, 'path': normalized_path},
            )
            raise ValidationException(user_message='来源不在白名单内', developer_message='Embed origin/path rejected')

        ttl = min(max(1, int(SecurityConfig.security_embed_grant_ttl_seconds)), 60)
        grant = await self.issue_access_token(
            subject=subject,
            audience=SecurityConfig.security_jwt_audience_embed,
            expires_seconds=ttl,
            token_use='embed_grant',
            claims={
                'tenant_id': tenant_id,
                'integration_id': integration_id,
                'origin': normalized_origin,
                'path': normalized_path,
            },
        )
        unverified = jwt.decode(grant, options={'verify_signature': False})
        grant_id = str(unverified.get('jti') or '')
        await self._require_redis().set(f'sec:embed_grant:{grant_id}', '1', ex=ttl, nx=True)
        return grant, ttl

    async def exchange_embed_grant(
        self,
        *,
        embed_grant: str,
        origin: str,
        request_id: str,
        source_ip: str,
    ) -> tuple[str, int, dict[str, Any]]:
        payload = await self.verify_access_token(
            embed_grant,
            audience=SecurityConfig.security_jwt_audience_embed,
            enforce_replay=False,
            expected_use='embed_grant',
            enforce_session=False,
        )

        normalized_origin = _normalize_origin(origin)
        if normalized_origin != payload.get('origin'):
            await self.log_security_event(
                event_type='embed_exchange_origin_mismatch',
                subject=str(payload.get('sub') or ''),
                reason='origin_mismatch',
                request_id=request_id,
                source_ip=source_ip,
                payload={'expected': payload.get('origin'), 'actual': normalized_origin},
            )
            raise ValidationException(user_message='来源不匹配', developer_message='Embed exchange origin mismatch')

        grant_id = str(payload.get('jti') or '')
        consumed = await self._require_redis().delete(f'sec:embed_grant:{grant_id}')
        if not consumed:
            await self.log_security_event(
                event_type='embed_grant_replay',
                subject=str(payload.get('sub') or ''),
                reason='grant_already_consumed',
                request_id=request_id,
                source_ip=source_ip,
            )
            raise AuthException(user_message='用户token已失效，请重新登录', developer_message='Embed grant replay detected')

        expires_in = min(max(1, int(SecurityConfig.security_embed_access_expire_seconds)), 300, self.max_token_seconds)
        access = await self.issue_access_token(
            subject=str(payload.get('sub') or ''),
            audience=SecurityConfig.security_jwt_audience_api,
            expires_seconds=expires_in,
            token_use='embed_access',
            claims={
                'tenant_id': payload.get('tenant_id'),
                'integration_id': payload.get('integration_id'),
                'origin': payload.get('origin'),
            },
        )
        return access, expires_in, payload

    async def assert_user_session_live(self, *, session_id: str, user_id: str) -> None:
        redis = self._require_redis()
        raw = _to_text(await redis.get(f'sec:user_session:{session_id}')) if session_id else ''
        metadata = json.loads(raw) if raw else {}
        if not session_id or metadata.get('userId') != user_id:
            raise AuthException(user_message='登录状态已失效，请重新登录', developer_message='WebSocket login session revoked or expired')
        if not AppConfig.app_same_time_login:
            active = _to_text(await redis.get(f'sec:active_session:{user_id}'))
            if active != session_id:
                raise AuthException(user_message='登录状态已失效，请重新登录', developer_message='WebSocket login session replaced')

    async def issue_ws_ticket(
        self,
        *,
        subject: str,
        origin: str,
        session_id: str,
        auth_session_id: str,
    ) -> tuple[str, int]:
        await self.assert_user_session_live(session_id=auth_session_id, user_id=subject.removeprefix('user:'))
        ttl = min(max(1, int(SecurityConfig.security_ws_ticket_ttl_seconds)), 30)
        ticket = uuid.uuid4().hex
        data = {
            'subject': subject,
            'origin': _normalize_origin(origin),
            'sessionId': session_id,
            'authSessionId': auth_session_id,
            'createdAt': _utc_now().isoformat(),
        }
        inserted = await self._require_redis().set(
            f'sec:ws_ticket:{ticket}',
            json.dumps(data, ensure_ascii=False),
            ex=ttl,
            nx=True,
        )
        if not inserted:
            raise RuntimeError('Failed to issue ws ticket')
        return ticket, ttl

    async def consume_ws_ticket(
        self,
        *,
        ticket: str,
        origin: str,
        session_id: str,
        request_id: str,
        source_ip: str,
    ) -> dict[str, Any]:
        key = f'sec:ws_ticket:{ticket}'
        raw = await self._require_redis().get(key)
        if not raw:
            await self.log_security_event(
                event_type='ws_ticket_invalid',
                subject='anonymous',
                reason='missing_or_expired_ticket',
                request_id=request_id,
                source_ip=source_ip,
            )
            raise AuthException(user_message='用户token不合法', developer_message='Missing or expired ws ticket')

        data = json.loads(_to_text(raw))
        deleted = await self._require_redis().delete(key)
        if not deleted:
            await self.log_security_event(
                event_type='ws_ticket_replay',
                subject=str(data.get('subject') or ''),
                reason='ticket_reused',
                request_id=request_id,
                source_ip=source_ip,
            )
            raise AuthException(user_message='用户token不合法', developer_message='Ws ticket replay detected')

        normalized_origin = _normalize_origin(origin)
        if data.get('origin') != normalized_origin:
            await self.log_security_event(
                event_type='ws_origin_mismatch',
                subject=str(data.get('subject') or ''),
                reason='origin_mismatch',
                request_id=request_id,
                source_ip=source_ip,
                payload={'expected': data.get('origin'), 'actual': normalized_origin},
            )
            raise AuthException(user_message='用户token不合法', developer_message='Ws origin mismatch')

        if data.get('sessionId') != session_id:
            raise AuthException(user_message='用户token不合法', developer_message='Ws session mismatch')
        await self.assert_user_session_live(
            session_id=str(data.get('authSessionId') or ''),
            user_id=str(data.get('subject') or '').removeprefix('user:'),
        )
        return data

    async def register_client_jwk(
        self,
        *,
        client_id: str,
        tenant_id: str,
        integration_id: str,
        jwk: dict[str, Any],
        enabled: bool,
    ) -> str:
        if not client_id:
            raise ValidationException(user_message='client_id不能为空', developer_message='client_id is required')
        if not isinstance(jwk, dict):
            raise ValidationException(user_message='jwk格式错误', developer_message='JWK must be an object')

        kid = str(jwk.get('kid') or hashlib.sha256(json.dumps(jwk, sort_keys=True).encode('utf-8')).hexdigest()[:16])
        jwk_with_kid = dict(jwk)
        jwk_with_kid['kid'] = kid

        try:
            jwt.PyJWK.from_dict(jwk_with_kid)
        except Exception as exc:
            raise ValidationException(user_message='jwk格式错误', developer_message=f'Invalid JWK: {exc}') from exc

        record = {
            'clientId': client_id,
            'tenantId': tenant_id,
            'integrationId': integration_id,
            'kid': kid,
            'jwk': jwk_with_kid,
            'enabled': enabled,
            'updatedAt': _utc_now().isoformat(),
        }
        redis = self._require_redis()
        await redis.set(f'sec:client_jwk:{client_id}:{kid}', json.dumps(record, ensure_ascii=False))
        await redis.set(f'sec:client_active_kid:{client_id}', kid)
        await self.log_security_event(
            event_type='m2m_client_jwk_registered',
            subject=client_id,
            reason='register_client_jwk',
            payload={'kid': kid, 'enabled': enabled, 'tenantId': tenant_id, 'integrationId': integration_id},
        )
        return kid

    async def verify_private_key_jwt(
        self,
        *,
        assertion: str,
        audience: str | list[str],
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        try:
            header = jwt.get_unverified_header(assertion)
            prelim = jwt.decode(assertion, options={'verify_signature': False})
        except InvalidTokenError as exc:
            raise AuthException(user_message='用户token不合法', developer_message=f'Invalid client assertion: {exc}') from exc

        client_id = str(prelim.get('iss') or '')
        if not client_id or str(prelim.get('sub') or '') != client_id:
            raise AuthException(user_message='用户token不合法', developer_message='client assertion iss/sub mismatch')

        kid = str(header.get('kid') or '')
        alg = _canonical_alg(str(header.get('alg') or ''))
        if not kid or not alg:
            raise AuthException(user_message='用户token不合法', developer_message='client assertion missing kid/alg')
        if alg not in self._CLIENT_ASSERTION_ALGS:
            raise AuthException(user_message='用户token不合法', developer_message=f'client assertion alg not allowed: {alg}')

        raw = await self._require_redis().get(f'sec:client_jwk:{client_id}:{kid}')
        if not raw:
            raise AuthException(user_message='用户token不合法', developer_message='client jwk not found')

        record = json.loads(_to_text(raw))
        if not record.get('enabled', False):
            raise AuthException(user_message='用户token不合法', developer_message='client jwk disabled')

        jwk_dict = record.get('jwk')
        if not isinstance(jwk_dict, dict):
            raise AuthException(user_message='用户token不合法', developer_message='invalid jwk record')
        record_alg = _canonical_alg(str(jwk_dict.get('alg') or ''))
        if record_alg and record_alg != alg:
            raise AuthException(user_message='用户token不合法', developer_message='client assertion algorithm mismatch JWK')

        try:
            pyjwk = jwt.PyJWK.from_dict(jwk_dict)
            payload = jwt.decode(
                assertion,
                key=pyjwk.key,
                algorithms=[alg],
                audience=audience,
                issuer=client_id,
                leeway=self.clock_skew_seconds,
                options={'require': ['iss', 'sub', 'aud', 'jti', 'iat', 'exp']},
            )
        except InvalidTokenError as exc:
            raise AuthException(user_message='用户token不合法', developer_message=f'client assertion verify failed: {exc}') from exc

        issued_at = _coerce_int(payload.get('iat'))
        expires_at = _coerce_int(payload.get('exp'))
        if issued_at and expires_at and expires_at - issued_at > self.max_token_seconds:
            raise AuthException(user_message='用户token不合法', developer_message='client assertion exp too long')
        await self._assert_first_use('sec:m2m_assertion_jti', str(payload.get('jti')), payload.get('exp'))
        return client_id, payload, record

    def extract_origin(self, *, origin: str | None, referer: str | None) -> str | None:
        normalized_origin = _normalize_origin(origin)
        if normalized_origin:
            return normalized_origin
        return _normalize_origin(_origin_from_referer(referer))

    def ensure_origin_allowed(self, origin: str | None) -> None:
        normalized = _normalize_origin(origin)
        if not normalized:
            raise ValidationException(user_message='缺少来源信息', developer_message='Missing Origin/Referer')
        if normalized not in self.allowed_origins:
            raise ValidationException(user_message='来源不在白名单内', developer_message=f'Origin not allowed: {normalized}')

    async def issue_csrf_token(self, subject: str) -> tuple[str, int]:
        if not subject:
            raise ValidationException(user_message='缺少用户信息', developer_message='Missing CSRF subject')
        token = uuid.uuid4().hex
        ttl = max(60, int(SecurityConfig.security_csrf_token_ttl_seconds))
        await self._require_redis().set(f'sec:csrf:{subject}', token, ex=ttl)
        return token, ttl

    async def validate_csrf_token(self, subject: str, token: str) -> bool:
        if not subject or not token:
            return False
        cached = _to_text(await self._require_redis().get(f'sec:csrf:{subject}'))
        return bool(cached and cached == token)
