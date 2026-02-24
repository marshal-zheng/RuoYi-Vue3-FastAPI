"""
Idempotency middleware for write endpoints.

Behavior:
- Activate only for configured methods/paths and when X-Idempotency-Key exists.
- Cache first successful (2xx) response by key + request fingerprint within TTL.
- Replay cached response for retries with same key + same payload.
- Return HTTP 409 when same key is reused with different payload.
"""
import asyncio
import base64
import hashlib
import json
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl

from fastapi import FastAPI
import jwt
from jwt.exceptions import InvalidTokenError
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config.env import IdempotencyConfig, JwtConfig
from middlewares.trace_middleware import get_request_id
from utils.log_util import logger

_HOP_BY_HOP_HEADERS = {
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailers',
    'transfer-encoding',
    'upgrade',
}

_RELEASE_LOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
end
return 0
"""


def _parse_csv(value: str) -> List[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


class IdempotencyASGIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        ttl_seconds: int = 600,
        lock_ttl_seconds: int = 30,
        wait_timeout_ms: int = 2000,
        methods: Optional[Sequence[str]] = None,
        path_prefixes: Optional[Sequence[str]] = None,
        exclude_paths: Optional[Sequence[str]] = None,
        max_request_body_bytes: int = 2 * 1024 * 1024,
        max_response_body_bytes: int = 2 * 1024 * 1024,
        key_prefix: str = 'idem:v1',
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.lock_ttl_seconds = max(1, int(lock_ttl_seconds))
        self.wait_timeout_ms = max(0, int(wait_timeout_ms))
        self.max_request_body_bytes = int(max_request_body_bytes)
        self.max_response_body_bytes = int(max_response_body_bytes)
        self.key_prefix = key_prefix

        self.methods = {item.upper() for item in (methods or ['POST', 'PUT']) if item}
        self.path_prefixes = list(path_prefixes or ['/'])
        self.exclude_paths = list(exclude_paths or [])

        self._local_guard = asyncio.Lock()
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._local_locks: Dict[str, Dict[str, Any]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get('type') != 'http' or not self.enabled:
            await self.app(scope, receive, send)
            return

        method = str(scope.get('method', '')).upper()
        path = str(scope.get('path', ''))
        if not self._should_handle_path(method, path):
            await self.app(scope, receive, send)
            return

        request_headers = self._extract_request_headers(scope.get('headers', []))
        idempotency_key = request_headers.get('x-idempotency-key', '').strip()
        if not idempotency_key:
            await self.app(scope, receive, send)
            return

        skip_reason = self._resolve_skip_reason(request_headers)
        if skip_reason is not None:
            logger.warning(
                f'idempotency skip cache due to request policy: '
                f'path={path} reason={skip_reason} limit={self.max_request_body_bytes}'
            )
            await self.app(scope, receive, send)
            return

        identity_scope = self._resolve_identity_scope(scope, request_headers)
        request_body = await self._drain_request_body(receive)
        replay_receive = self._build_replay_receive(request_body)
        content_type = request_headers.get('content-type', '')
        query_string = scope.get('query_string', b'')
        fingerprint = self._build_fingerprint(method, path, query_string, content_type, request_body, identity_scope)
        cache_key = self._cache_key(method, path, idempotency_key, identity_scope)
        lock_key = self._lock_key(method, path, idempotency_key, identity_scope)

        cached_entry = await self._get_cache_entry(scope, cache_key)
        if cached_entry is not None:
            await self._handle_cached_entry(scope, send, cached_entry, fingerprint, idempotency_key)
            return

        lock_token = uuid.uuid4().hex
        lock_acquired, lock_backend = await self._acquire_lock(scope, lock_key, lock_token)
        if not lock_acquired:
            awaited_entry = await self._wait_for_cache_entry(scope, cache_key, timeout_ms=self.wait_timeout_ms)
            if awaited_entry is not None:
                await self._handle_cached_entry(scope, send, awaited_entry, fingerprint, idempotency_key)
                return
            await self._send_problem(
                scope=scope,
                send=send,
                status_code=409,
                title='请求正在处理',
                detail='相同幂等键的请求正在处理，请稍后重试',
                error_code=40902,
            )
            return

        try:
            # Double-check after lock to avoid duplicate execution under race.
            cached_entry = await self._get_cache_entry(scope, cache_key)
            if cached_entry is not None:
                await self._handle_cached_entry(scope, send, cached_entry, fingerprint, idempotency_key)
                return

            capture: Dict[str, Any] = {
                'status_code': None,
                'headers': [],
                'body_chunks': [],
                'body_size': 0,
            }

            async def capture_send(message: Message) -> None:
                message_type = message.get('type')
                if message_type == 'http.response.start':
                    capture['status_code'] = int(message.get('status', 0))
                    capture['headers'] = list(message.get('headers', []))
                elif message_type == 'http.response.body':
                    chunk = message.get('body', b'') or b''
                    if chunk:
                        capture['body_chunks'].append(chunk)
                        capture['body_size'] += len(chunk)
                await send(message)

            await self.app(scope, replay_receive, capture_send)

            status_code = int(capture.get('status_code') or 0)
            if 200 <= status_code < 300:
                body_bytes = b''.join(capture.get('body_chunks') or [])
                if self.max_response_body_bytes <= 0 or len(body_bytes) <= self.max_response_body_bytes:
                    entry = {
                        'fingerprint': fingerprint,
                        'status_code': status_code,
                        'headers': self._headers_to_store(capture.get('headers') or []),
                        'body_b64': base64.b64encode(body_bytes).decode('ascii'),
                        'created_at': int(time.time()),
                    }
                    await self._set_cache_entry(scope, cache_key, entry, ttl_seconds=self.ttl_seconds)
                else:
                    logger.warning(
                        f'idempotency skip cache due to response body too large: '
                        f'path={path} size={len(body_bytes)} limit={self.max_response_body_bytes}'
                    )
        finally:
            await self._release_lock(scope, lock_key, lock_token, backend=lock_backend)

    def _should_handle_path(self, method: str, path: str) -> bool:
        if method not in self.methods:
            return False

        if self.exclude_paths:
            for prefix in self.exclude_paths:
                if path.startswith(prefix):
                    return False

        if not self.path_prefixes:
            return True

        for prefix in self.path_prefixes:
            if prefix == '/' or path.startswith(prefix):
                return True
        return False

    @staticmethod
    def _extract_request_headers(raw_headers: Iterable[Tuple[bytes, bytes]]) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for raw_key, raw_value in raw_headers:
            key = raw_key.decode('latin-1').lower()
            if key not in result:
                result[key] = raw_value.decode('latin-1')
        return result

    @staticmethod
    async def _drain_request_body(receive: Receive) -> bytes:
        chunks: List[bytes] = []
        while True:
            message = await receive()
            message_type = message.get('type')
            if message_type == 'http.disconnect':
                break
            if message_type != 'http.request':
                continue
            chunk = message.get('body', b'') or b''
            if chunk:
                chunks.append(chunk)
            if not message.get('more_body', False):
                break
        return b''.join(chunks)

    @staticmethod
    def _build_replay_receive(body: bytes) -> Receive:
        sent = {'done': False}

        async def replay_receive() -> Message:
            if not sent['done']:
                sent['done'] = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        return replay_receive

    def _build_fingerprint(
        self,
        method: str,
        path: str,
        query_string: bytes,
        content_type: str,
        body: bytes,
        identity_scope: str,
    ) -> str:
        normalized_query = parse_qsl(query_string.decode('utf-8', errors='ignore'), keep_blank_values=True)
        normalized_query.sort(key=lambda item: (item[0], item[1]))
        payload = self._normalize_payload(content_type, body)
        source = {
            'method': method,
            'path': path,
            'scope': identity_scope,
            'query': normalized_query,
            'payload': payload,
        }
        digest = hashlib.sha256(
            json.dumps(source, ensure_ascii=False, separators=(',', ':'), sort_keys=True, default=str).encode('utf-8')
        )
        return digest.hexdigest()

    @staticmethod
    def _normalize_payload(content_type: str, body: bytes) -> Any:
        if not body:
            return None

        if 'application/json' in content_type.lower():
            try:
                return json.loads(body.decode('utf-8'))
            except Exception:
                pass

        return {'raw_sha256': hashlib.sha256(body).hexdigest(), 'size': len(body)}

    def _cache_key(self, method: str, path: str, idempotency_key: str, identity_scope: str) -> str:
        base = f'{method}:{path}:{idempotency_key}:{identity_scope}'
        digest = hashlib.sha256(base.encode('utf-8')).hexdigest()
        return f'{self.key_prefix}:resp:{digest}'

    def _lock_key(self, method: str, path: str, idempotency_key: str, identity_scope: str) -> str:
        base = f'{method}:{path}:{idempotency_key}:{identity_scope}'
        digest = hashlib.sha256(base.encode('utf-8')).hexdigest()
        return f'{self.key_prefix}:lock:{digest}'

    def _resolve_skip_reason(self, headers: Dict[str, str]) -> Optional[str]:
        if self.max_request_body_bytes <= 0:
            return None

        content_type = str(headers.get('content-type', '')).lower()
        if 'multipart/form-data' in content_type:
            return 'multipart-form-data'
        if 'application/octet-stream' in content_type:
            return 'octet-stream'

        content_length_raw = headers.get('content-length')
        if content_length_raw is None:
            return 'missing-content-length'
        try:
            content_length = int(content_length_raw)
        except (TypeError, ValueError):
            return f'invalid-content-length:{content_length_raw}'

        if content_length < 0:
            return f'invalid-content-length:{content_length}'
        if content_length > self.max_request_body_bytes:
            return f'content-length-exceeds-limit:{content_length}'
        return None

    def _resolve_identity_scope(self, scope: Scope, headers: Dict[str, str]) -> str:
        auth_header = headers.get('authorization', '')
        if not auth_header.lower().startswith('bearer '):
            return f'anon:{self._resolve_client_ip(scope)}'

        token = auth_header[7:].strip()
        if not token:
            return f'anon:{self._resolve_client_ip(scope)}'

        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()[:24]
        try:
            payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
        except InvalidTokenError:
            return f'token:{token_hash}'
        except Exception as exc:
            logger.warning(f'idempotency decode token failed: {exc}')
            return f'token:{token_hash}'

        user_id = payload.get('user_id') or payload.get('userId') or payload.get('sub')
        tenant_id = payload.get('tenant_id') or payload.get('tenantId')
        session_id = payload.get('session_id') or payload.get('sessionId')

        segments: List[str] = []
        if user_id is not None:
            segments.append(f'user:{user_id}')
        if tenant_id is not None:
            segments.append(f'tenant:{tenant_id}')
        if session_id is not None:
            segments.append(f'session:{session_id}')
        if segments:
            return '|'.join(segments)
        return f'token:{token_hash}'

    @staticmethod
    def _resolve_client_ip(scope: Scope) -> str:
        client = scope.get('client')
        if isinstance(client, (list, tuple)) and client:
            return str(client[0])
        return 'unknown'

    @staticmethod
    def _headers_to_store(headers: List[Tuple[bytes, bytes]]) -> List[List[str]]:
        result: List[List[str]] = []
        for raw_name, raw_value in headers:
            name = raw_name.decode('latin-1')
            if name.lower() in _HOP_BY_HOP_HEADERS:
                continue
            result.append([name, raw_value.decode('latin-1')])
        return result

    @staticmethod
    def _entry_to_headers(entry: Dict[str, Any]) -> List[Tuple[bytes, bytes]]:
        headers: List[Tuple[bytes, bytes]] = []
        for item in entry.get('headers', []):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            name = str(item[0]).encode('latin-1', errors='ignore')
            value = str(item[1]).encode('latin-1', errors='ignore')
            headers.append((name, value))
        return headers

    async def _handle_cached_entry(
        self,
        scope: Scope,
        send: Send,
        entry: Dict[str, Any],
        fingerprint: str,
        idempotency_key: str,
    ) -> None:
        cached_fingerprint = str(entry.get('fingerprint', ''))
        if cached_fingerprint != fingerprint:
            await self._send_problem(
                scope=scope,
                send=send,
                status_code=409,
                title='幂等键冲突',
                detail=(
                    '相同 X-Idempotency-Key 对应的请求体不一致，'
                    f'key={idempotency_key}'
                ),
                error_code=40901,
            )
            return

        body_b64 = str(entry.get('body_b64', '') or '')
        try:
            body = base64.b64decode(body_b64.encode('ascii'))
        except Exception:
            body = b''
        status_code = int(entry.get('status_code') or 200)
        headers = self._entry_to_headers(entry)
        await send({'type': 'http.response.start', 'status': status_code, 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})

    async def _wait_for_cache_entry(self, scope: Scope, cache_key: str, timeout_ms: int) -> Optional[Dict[str, Any]]:
        if timeout_ms <= 0:
            return await self._get_cache_entry(scope, cache_key)
        deadline = time.monotonic() + (timeout_ms / 1000.0)
        while time.monotonic() < deadline:
            cached = await self._get_cache_entry(scope, cache_key)
            if cached is not None:
                return cached
            await asyncio.sleep(0.05)
        return await self._get_cache_entry(scope, cache_key)

    async def _send_problem(
        self,
        *,
        scope: Scope,
        send: Send,
        status_code: int,
        title: str,
        detail: str,
        error_code: int,
    ) -> None:
        request_id = get_request_id()
        payload = {
            'type': 'https://api.example.com/problems/idempotency',
            'title': title,
            'status': status_code,
            'detail': detail,
            'instance': str(scope.get('path', '')),
            'errorCode': error_code,
            'requestId': request_id,
        }
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        headers: List[Tuple[bytes, bytes]] = [
            (b'content-type', b'application/problem+json; charset=utf-8'),
            (b'content-length', str(len(body)).encode('ascii')),
        ]
        if request_id:
            headers.append((b'x-request-id', request_id.encode('latin-1', errors='ignore')))
        await send({'type': 'http.response.start', 'status': int(status_code), 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})

    @staticmethod
    def _resolve_redis(scope: Scope):
        app = scope.get('app')
        if app is None:
            return None
        state = getattr(app, 'state', None)
        if state is None:
            return None
        redis_client = getattr(state, 'redis', None)
        if redis_client is None:
            return None
        # 测试环境 DummyRedis 不具备真实 TTL 语义，回退到本地 TTL 存储更稳定。
        if redis_client.__class__.__name__ == 'DummyRedis':
            return None
        return redis_client

    @staticmethod
    def _decode_cache_payload(payload: Any) -> Optional[Dict[str, Any]]:
        if payload is None:
            return None
        raw_value = payload
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode('utf-8')
        if isinstance(raw_value, str):
            try:
                raw_value = json.loads(raw_value)
            except Exception:
                return None
        if not isinstance(raw_value, dict):
            return None
        return raw_value

    async def _get_cache_entry(self, scope: Scope, cache_key: str) -> Optional[Dict[str, Any]]:
        redis_client = self._resolve_redis(scope)
        if redis_client is not None:
            try:
                payload = await redis_client.get(cache_key)
                decoded = self._decode_cache_payload(payload)
                if decoded is not None:
                    return decoded
            except Exception as exc:
                logger.warning(f'idempotency redis get failed, fallback local: key={cache_key}, error={exc}')
        return await self._local_get_cache_entry(cache_key)

    async def _set_cache_entry(self, scope: Scope, cache_key: str, entry: Dict[str, Any], ttl_seconds: int) -> None:
        redis_client = self._resolve_redis(scope)
        payload = json.dumps(entry, ensure_ascii=False, separators=(',', ':'))
        if redis_client is not None:
            try:
                if hasattr(redis_client, 'setex'):
                    await redis_client.setex(cache_key, ttl_seconds, payload)
                else:
                    await redis_client.set(cache_key, payload, ex=ttl_seconds)
                return
            except Exception as exc:
                logger.warning(f'idempotency redis set failed, fallback local: key={cache_key}, error={exc}')
        await self._local_set_cache_entry(cache_key, entry, ttl_seconds=ttl_seconds)

    async def _acquire_lock(self, scope: Scope, lock_key: str, token: str) -> Tuple[bool, str]:
        redis_client = self._resolve_redis(scope)
        if redis_client is not None:
            try:
                acquired = await redis_client.set(lock_key, token, ex=self.lock_ttl_seconds, nx=True)
                return bool(acquired), 'redis'
            except Exception as exc:
                logger.warning(f'idempotency redis lock failed, fallback local: key={lock_key}, error={exc}')
        acquired = await self._local_acquire_lock(lock_key, token, ttl_seconds=self.lock_ttl_seconds)
        return acquired, 'local'

    async def _release_lock(self, scope: Scope, lock_key: str, token: str, backend: str) -> None:
        if backend == 'redis':
            redis_client = self._resolve_redis(scope)
            if redis_client is not None:
                try:
                    if hasattr(redis_client, 'eval'):
                        try:
                            await redis_client.eval(_RELEASE_LOCK_LUA, 1, lock_key, token)
                        except TypeError:
                            # Some clients expose eval(script, keys=[...], args=[...]).
                            await redis_client.eval(_RELEASE_LOCK_LUA, keys=[lock_key], args=[token])
                        return

                    current_token = await redis_client.get(lock_key)
                    if isinstance(current_token, bytes):
                        current_token = current_token.decode('utf-8', errors='ignore')
                    if str(current_token or '') == token:
                        await redis_client.delete(lock_key)
                    return
                except Exception as exc:
                    logger.warning(f'idempotency redis unlock failed, fallback local: key={lock_key}, error={exc}')
        await self._local_release_lock(lock_key, token)

    async def _local_get_cache_entry(self, cache_key: str) -> Optional[Dict[str, Any]]:
        now = time.monotonic()
        async with self._local_guard:
            self._cleanup_local(now=now)
            item = self._local_cache.get(cache_key)
            if not item:
                return None
            cached_entry = item.get('entry')
            if isinstance(cached_entry, dict):
                return dict(cached_entry)
            return None

    async def _local_set_cache_entry(self, cache_key: str, entry: Dict[str, Any], ttl_seconds: int) -> None:
        expires_at = time.monotonic() + max(1, int(ttl_seconds))
        async with self._local_guard:
            self._cleanup_local(now=time.monotonic())
            self._local_cache[cache_key] = {'expires_at': expires_at, 'entry': dict(entry)}

    async def _local_acquire_lock(self, lock_key: str, token: str, ttl_seconds: int) -> bool:
        now = time.monotonic()
        expires_at = now + max(1, int(ttl_seconds))
        async with self._local_guard:
            self._cleanup_local(now=now)
            current = self._local_locks.get(lock_key)
            if current and float(current.get('expires_at', 0)) > now:
                return False
            self._local_locks[lock_key] = {'expires_at': expires_at, 'token': token}
            return True

    async def _local_release_lock(self, lock_key: str, token: str) -> None:
        async with self._local_guard:
            current = self._local_locks.get(lock_key)
            if current and str(current.get('token', '')) == token:
                self._local_locks.pop(lock_key, None)

    def _cleanup_local(self, now: Optional[float] = None) -> None:
        current_time = time.monotonic() if now is None else now
        expired_cache_keys = [key for key, value in self._local_cache.items() if float(value.get('expires_at', 0)) <= current_time]
        for key in expired_cache_keys:
            self._local_cache.pop(key, None)

        expired_lock_keys = [key for key, value in self._local_locks.items() if float(value.get('expires_at', 0)) <= current_time]
        for key in expired_lock_keys:
            self._local_locks.pop(key, None)


def add_idempotency_middleware(app: FastAPI) -> None:
    """Register idempotency middleware when feature flag is enabled."""
    if not IdempotencyConfig.idempotency_enabled:
        logger.info('幂等中间件已禁用')
        return

    app.add_middleware(
        IdempotencyASGIMiddleware,
        enabled=IdempotencyConfig.idempotency_enabled,
        ttl_seconds=IdempotencyConfig.idempotency_ttl_seconds,
        lock_ttl_seconds=IdempotencyConfig.idempotency_lock_ttl_seconds,
        wait_timeout_ms=IdempotencyConfig.idempotency_wait_timeout_ms,
        methods=_parse_csv(IdempotencyConfig.idempotency_methods),
        path_prefixes=_parse_csv(IdempotencyConfig.idempotency_path_prefixes) or ['/'],
        exclude_paths=_parse_csv(IdempotencyConfig.idempotency_exclude_paths),
        max_request_body_bytes=IdempotencyConfig.idempotency_max_request_body_bytes,
        max_response_body_bytes=IdempotencyConfig.idempotency_max_response_body_bytes,
    )
