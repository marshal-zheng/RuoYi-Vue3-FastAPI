"""
Tiered rate-limiting middleware (auth/write/read) with IP + user scopes.
"""
import asyncio
import ipaddress
import json
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Scope, Send

from config.env import RateLimitConfig, TextFieldAIConfig
from middlewares.text_field_ai_middleware import AI_GENERATE_PATH, ai_route_path
from middlewares.trace_middleware import get_request_id, get_trace_id
from utils.log_util import logger


def _parse_csv(value: str) -> List[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


class RateLimitASGIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        window_seconds: int = 60,
        exclude_paths: Optional[Sequence[str]] = None,
        auth_paths: Optional[Sequence[str]] = None,
        write_methods: Optional[Sequence[str]] = None,
        trusted_proxies: Optional[Sequence[str]] = None,
        auth_ip_limit: int = 20,
        auth_user_limit: int = 40,
        ai_ip_limit: int = 60,
        ai_user_limit: int = 20,
        write_ip_limit: int = 120,
        write_user_limit: int = 240,
        read_ip_limit: int = 600,
        read_user_limit: int = 1200,
        key_prefix: str = 'ratelimit:v1',
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.window_seconds = max(1, int(window_seconds))
        self.exclude_paths = list(exclude_paths or [])
        self.auth_paths = list(auth_paths or ['/login', '/captchaImage'])
        self.write_methods = {item.upper() for item in (write_methods or ['POST', 'PUT', 'PATCH', 'DELETE']) if item}
        self._trust_all_proxies = False
        self._trusted_proxy_ips: set[str] = set()
        self._trusted_proxy_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for proxy in trusted_proxies or []:
            candidate = str(proxy).strip()
            if not candidate:
                continue
            if candidate == '*':
                self._trust_all_proxies = True
                continue
            if '/' in candidate:
                try:
                    self._trusted_proxy_networks.append(ipaddress.ip_network(candidate, strict=False))
                except ValueError:
                    logger.warning(f'ignore invalid trusted proxy cidr: {candidate}')
                continue
            try:
                normalized_ip = ipaddress.ip_address(candidate)
                self._trusted_proxy_ips.add(str(normalized_ip))
            except ValueError:
                logger.warning(f'ignore invalid trusted proxy ip: {candidate}')
        self.key_prefix = key_prefix

        self.auth_ip_limit = max(1, int(auth_ip_limit))
        self.auth_user_limit = max(1, int(auth_user_limit))
        self.ai_ip_limit = max(1, int(ai_ip_limit))
        self.ai_user_limit = max(1, int(ai_user_limit))
        self.write_ip_limit = max(1, int(write_ip_limit))
        self.write_user_limit = max(1, int(write_user_limit))
        self.read_ip_limit = max(1, int(read_ip_limit))
        self.read_user_limit = max(1, int(read_user_limit))

        self._local_guard = asyncio.Lock()
        self._local_counters: Dict[str, Dict[str, Any]] = {}

    async def __call__(self, scope: Scope, receive, send: Send) -> None:
        if scope.get('type') != 'http' or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = ai_route_path(scope)
        method = str(scope.get('method', '')).upper()
        if self._is_excluded(path):
            await self.app(scope, receive, send)
            return

        headers = self._extract_headers(scope.get('headers', []))
        tier = self._resolve_tier(path=path, method=method)
        ip_identifier = self._resolve_client_ip(scope, headers)
        user_identifier = await self._resolve_user_identifier(scope, headers)
        ip_limit, user_limit = self._limits_for_tier(tier)

        now = int(time.time())
        bucket = now // self.window_seconds
        reset_at = (bucket + 1) * self.window_seconds
        retry_after = max(1, reset_at - now)

        ip_key = self._counter_key(tier=tier, scope_kind='ip', identifier=ip_identifier, bucket=bucket)
        ip_count = await self._increment_counter(scope, ip_key, ttl=self.window_seconds + 1)
        ip_remaining = max(0, ip_limit - ip_count)

        if ip_count > ip_limit:
            await self._send_rate_limit_problem(
                scope=scope,
                send=send,
                tier=tier,
                scope_kind='ip',
                identifier=ip_identifier,
                limit=ip_limit,
                count=ip_count,
                reset_at=reset_at,
                retry_after=retry_after,
            )
            return

        user_remaining = ip_remaining
        effective_limit = ip_limit
        effective_remaining = ip_remaining

        if user_identifier:
            user_key = self._counter_key(tier=tier, scope_kind='user', identifier=user_identifier, bucket=bucket)
            user_count = await self._increment_counter(scope, user_key, ttl=self.window_seconds + 1)
            user_remaining = max(0, user_limit - user_count)
            effective_limit = min(ip_limit, user_limit)
            effective_remaining = min(ip_remaining, user_remaining)

            if user_count > user_limit:
                await self._send_rate_limit_problem(
                    scope=scope,
                    send=send,
                    tier=tier,
                    scope_kind='user',
                    identifier=user_identifier,
                    limit=user_limit,
                    count=user_count,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )
                return

        async def send_with_headers(message: Message) -> None:
            if message.get('type') == 'http.response.start':
                message_headers = list(message.get('headers', []))
                message_headers.append((b'ratelimit-limit', str(effective_limit).encode('ascii')))
                message_headers.append((b'ratelimit-remaining', str(max(0, effective_remaining)).encode('ascii')))
                message_headers.append((b'ratelimit-reset', str(reset_at).encode('ascii')))
                message['headers'] = message_headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _is_excluded(self, path: str) -> bool:
        if not self.exclude_paths:
            return False
        for prefix in self.exclude_paths:
            if path.startswith(prefix):
                return True
        return False

    def _resolve_tier(self, path: str, method: str) -> str:
        if path == AI_GENERATE_PATH and method == 'POST':
            return 'ai'
        for prefix in self.auth_paths:
            if path.startswith(prefix):
                return 'auth'
        if method in self.write_methods:
            return 'write'
        return 'read'

    def _limits_for_tier(self, tier: str) -> Tuple[int, int]:
        if tier == 'ai':
            return self.ai_ip_limit, self.ai_user_limit
        if tier == 'auth':
            return self.auth_ip_limit, self.auth_user_limit
        if tier == 'write':
            return self.write_ip_limit, self.write_user_limit
        return self.read_ip_limit, self.read_user_limit

    @staticmethod
    def _extract_headers(raw_headers) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for raw_key, raw_value in raw_headers:
            key = raw_key.decode('latin-1').lower()
            if key not in result:
                result[key] = raw_value.decode('latin-1')
        return result

    def _resolve_client_ip(self, scope: Scope, headers: Dict[str, str]) -> str:
        scope_client_ip = self._scope_client_ip(scope)
        if not self._is_trusted_proxy(scope_client_ip):
            return scope_client_ip

        forwarded = headers.get('x-forwarded-for', '')
        if forwarded:
            for raw_item in forwarded.split(','):
                first_ip = raw_item.strip()
                if first_ip and self._is_valid_ip(first_ip):
                    return first_ip

        return scope_client_ip

    @staticmethod
    def _scope_client_ip(scope: Scope) -> str:
        client = scope.get('client')
        if isinstance(client, (list, tuple)) and client:
            return str(client[0])
        return 'unknown'

    @staticmethod
    def _is_valid_ip(value: str) -> bool:
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def _is_trusted_proxy(self, client_ip: str) -> bool:
        if self._trust_all_proxies:
            return True
        if not client_ip or client_ip == 'unknown':
            return False

        try:
            client_addr = ipaddress.ip_address(client_ip)
        except ValueError:
            return False

        if str(client_addr) in self._trusted_proxy_ips:
            return True
        return any(client_addr in network for network in self._trusted_proxy_networks)

    async def _resolve_user_identifier(self, scope: Scope, headers: Dict[str, str]) -> Optional[str]:
        auth_header = headers.get('authorization', '')
        if not auth_header.lower().startswith('bearer '):
            return None

        token = auth_header[7:].strip()
        if not token:
            return None

        service = self._resolve_security_service(scope)
        if service is None:
            return None
        try:
            user_ctx = await service.extract_user_context_from_token(token)
            if not user_ctx:
                return None
            user_id = user_ctx.get('userId')
            return str(user_id) if user_id else None
        except Exception:
            logger.warning('rate limit token validation failed')
            return None

    @staticmethod
    def _resolve_security_service(scope: Scope) -> Optional[Any]:
        app = scope.get('app')
        state = getattr(app, 'state', None) if app else None
        service = getattr(state, 'security_token_service', None) if state else None
        if service and hasattr(service, 'extract_user_context_from_token'):
            return service
        return None

    def _counter_key(self, tier: str, scope_kind: str, identifier: str, bucket: int) -> str:
        return f'{self.key_prefix}:{tier}:{scope_kind}:{identifier}:{bucket}'

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
        # 测试环境 DummyRedis 不具备可靠过期语义，优先使用本地窗口计数。
        if redis_client.__class__.__name__ == 'DummyRedis':
            return None
        return redis_client

    async def _increment_counter(self, scope: Scope, key: str, ttl: int) -> int:
        redis_client = self._resolve_redis(scope)
        if redis_client is not None:
            try:
                if hasattr(redis_client, 'incr'):
                    count = int(await redis_client.incr(key))
                    if count == 1 and hasattr(redis_client, 'expire'):
                        await redis_client.expire(key, ttl)
                    return count

                raw_value = await redis_client.get(key)
                count = int(raw_value or 0) + 1
                if hasattr(redis_client, 'setex'):
                    await redis_client.setex(key, ttl, str(count))
                else:
                    await redis_client.set(key, str(count), ex=ttl)
                return count
            except Exception:
                logger.warning('rate limit counter unavailable; using local window')
        return await self._increment_counter_local(key=key, ttl=ttl)

    async def _increment_counter_local(self, key: str, ttl: int) -> int:
        now = time.monotonic()
        expires_at = now + max(1, int(ttl))
        async with self._local_guard:
            self._cleanup_local(now=now)
            current = self._local_counters.get(key)
            if current is None:
                self._local_counters[key] = {'count': 1, 'expires_at': expires_at}
                return 1
            current_count = int(current.get('count', 0)) + 1
            current['count'] = current_count
            current['expires_at'] = expires_at
            self._local_counters[key] = current
            return current_count

    def _cleanup_local(self, now: Optional[float] = None) -> None:
        current_time = time.monotonic() if now is None else now
        expired_keys = [key for key, value in self._local_counters.items() if float(value.get('expires_at', 0)) <= current_time]
        for key in expired_keys:
            self._local_counters.pop(key, None)

    async def _send_rate_limit_problem(
        self,
        *,
        scope: Scope,
        send: Send,
        tier: str,
        scope_kind: str,
        identifier: str,
        limit: int,
        count: int,
        reset_at: int,
        retry_after: int,
    ) -> None:
        request_id = get_request_id()
        payload = {
            'type': 'about:blank',
            'title': '请求过于频繁',
            'status': 429,
            'detail': f'请求已触发限流，请在 {retry_after} 秒后重试',
            'instance': str(scope.get('path', '')),
            'errorCode': 42901,
            'requestId': request_id,
        }
        if tier == 'ai':
            payload['aiCode'] = 'quota-exceeded'
        trace_id = get_trace_id()
        if trace_id:
            payload['traceId'] = trace_id
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        headers: List[Tuple[bytes, bytes]] = [
            (b'content-type', b'application/problem+json; charset=utf-8'),
            (b'content-length', str(len(body)).encode('ascii')),
            (b'retry-after', str(retry_after).encode('ascii')),
            (b'ratelimit-limit', str(limit).encode('ascii')),
            (b'ratelimit-remaining', b'0'),
            (b'ratelimit-reset', str(reset_at).encode('ascii')),
        ]
        if request_id:
            headers.append((b'x-request-id', request_id.encode('latin-1', errors='ignore')))
        if trace_id:
            headers.append((b'x-trace-id', trace_id.encode('latin-1', errors='ignore')))
        await send({'type': 'http.response.start', 'status': 429, 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})


def add_rate_limit_middleware(app: FastAPI) -> None:
    if not RateLimitConfig.rate_limit_enabled:
        logger.info('限流中间件已禁用')
        return

    app.add_middleware(
        RateLimitASGIMiddleware,
        enabled=RateLimitConfig.rate_limit_enabled,
        window_seconds=RateLimitConfig.rate_limit_window_seconds,
        exclude_paths=_parse_csv(RateLimitConfig.rate_limit_exclude_paths),
        auth_paths=_parse_csv(RateLimitConfig.rate_limit_auth_paths),
        write_methods=_parse_csv(RateLimitConfig.rate_limit_write_methods),
        trusted_proxies=_parse_csv(RateLimitConfig.rate_limit_trusted_proxies),
        auth_ip_limit=RateLimitConfig.rate_limit_auth_ip,
        auth_user_limit=RateLimitConfig.rate_limit_auth_user,
        ai_ip_limit=TextFieldAIConfig.ai_text_field_ip_per_minute,
        ai_user_limit=TextFieldAIConfig.ai_text_field_user_per_minute,
        write_ip_limit=RateLimitConfig.rate_limit_write_ip,
        write_user_limit=RateLimitConfig.rate_limit_write_user,
        read_ip_limit=RateLimitConfig.rate_limit_read_ip,
        read_user_limit=RateLimitConfig.rate_limit_read_user,
    )
