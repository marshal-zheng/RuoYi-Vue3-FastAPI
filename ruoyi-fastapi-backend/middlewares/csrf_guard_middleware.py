from __future__ import annotations

import json
from typing import Iterable, Optional
from urllib.parse import urlparse

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config.env import SecurityConfig
from middlewares.route_path import route_path
from utils.log_util import logger


class CsrfGuardASGIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool,
        allowed_origins: Iterable[str],
        protected_paths: Iterable[str],
        csrf_header_name: str,
        csrf_cookie_name: str,
        protected_write_paths: Iterable[str] = (),
        access_cookie_name: str = 'ruoyi_at',
    ):
        self.app = app
        self.enabled = enabled
        self.allowed_origins = {item.strip() for item in allowed_origins if item.strip()}
        self.protected_paths = [item.strip() for item in protected_paths if item.strip()]
        # Write-only protection: safe methods (e.g. <img> content GETs without Origin) pass untouched.
        self.protected_write_paths = [item.strip().rstrip('/') for item in protected_write_paths if item.strip()]
        self.csrf_header_name = (csrf_header_name or 'X-CSRF-Token').lower()
        self.csrf_cookie_name = csrf_cookie_name or 'csrf_token'
        self.access_cookie_name = access_cookie_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get('type') != 'http' or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = route_path(scope)
        method = str(scope.get('method', '')).upper()
        write_only = self._is_protected_write_path(path)
        if write_only and method in {'GET', 'HEAD', 'OPTIONS'}:
            await self.app(scope, receive, send)
            return
        if not write_only and not self._is_protected_path(path):
            await self.app(scope, receive, send)
            return

        headers = self._decode_headers(scope)
        cookies = self._parse_cookie(headers.get('cookie', ''))
        has_cookie_context = bool(cookies)
        if not has_cookie_context:
            # 仅在 Cookie 身份上下文启用 CSRF 守卫，避免阻断 m2m 直调场景。
            await self.app(scope, receive, send)
            return

        origin = headers.get('origin') or self._origin_from_referer(headers.get('referer'))
        if not origin or origin not in self.allowed_origins:
            logger.warning('csrf_block path={} reason=invalid_origin origin={}', path, origin or '')
            await self._reject(send, detail='Invalid origin for CSRF protected endpoint')
            return

        if method in {'GET', 'HEAD', 'OPTIONS'}:
            logger.info('csrf_safe_method path={} method={} origin={}', path, method, origin)
            await self.app(scope, receive, send)
            return

        header_token = headers.get(self.csrf_header_name)
        cookie_token = cookies.get(self.csrf_cookie_name)

        if not header_token or not cookie_token or header_token != cookie_token:
            logger.warning('csrf_block path={} reason=token_mismatch', path)
            await self._reject(send, detail='Invalid CSRF token')
            return

        decision = await self._subject_binding(scope, headers, cookies, header_token, write_only=write_only)
        if decision == 'reject':
            return await self._reject(send, detail='Invalid CSRF subject binding')
        if decision == 'reject-token':
            return await self._reject(send, detail='Invalid bearer token in CSRF check')

        logger.info('csrf_pass path={} method={}', path, method)
        await self.app(scope, receive, send)

    async def _subject_binding(
        self, scope: Scope, headers: dict[str, str], cookies: dict[str, str], header_token: str, *, write_only: bool
    ) -> str:
        """Return 'pass', 'reject' (token bound to another subject) or 'reject-token' (unusable bearer)."""
        service = self._resolve_security_service(scope)
        if not service:
            return 'pass'
        path = route_path(scope)
        bearer = headers.get('authorization', '')
        token = bearer.split(' ', 1)[1].strip() if bearer.lower().startswith('bearer ') else ''
        from_cookie = False
        if not token and write_only:
            # Cookie-only identity must be bound to the same subject as the CSRF token.
            token = cookies.get(self.access_cookie_name, '')
            from_cookie = bool(token)
        if not token:
            return 'pass'
        try:
            payload = await service.verify_access_token(
                token,
                audience=SecurityConfig.security_jwt_audience_api,
                enforce_replay=False,
                enforce_session=False,
            )
            subject = str(payload.get('sub') or '')
            valid = await service.validate_csrf_token(subject, header_token)
            if not valid and subject.startswith('user:'):
                valid = await service.validate_csrf_token(subject.split(':', 1)[1], header_token)
        except Exception:
            if from_cookie:
                # An unusable cookie cannot authenticate anyway; authentication answers 401.
                return 'pass'
            logger.warning('csrf_block path={} reason=invalid_bearer', path)
            return 'reject-token'
        if not valid:
            logger.warning('csrf_block path={} reason=token_not_bound_to_subject', path)
            return 'reject'
        return 'pass'

    def _is_protected_write_path(self, path: str) -> bool:
        return any(path == prefix or path.startswith(f'{prefix}/') for prefix in self.protected_write_paths)

    def _is_protected_path(self, path: str) -> bool:
        if not self.protected_paths:
            return False
        return any(path.startswith(prefix) for prefix in self.protected_paths)

    @staticmethod
    def _decode_headers(scope: Scope) -> dict[str, str]:
        decoded: dict[str, str] = {}
        for key, value in scope.get('headers', []):
            decoded[key.decode('latin-1').lower()] = value.decode('latin-1')
        return decoded

    @staticmethod
    def _resolve_security_service(scope: Scope):
        app = scope.get('app')
        state = getattr(app, 'state', None) if app else None
        service = getattr(state, 'security_token_service', None) if state else None
        if service and hasattr(service, 'verify_access_token') and hasattr(service, 'validate_csrf_token'):
            return service
        return None

    @staticmethod
    def _parse_cookie(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        if not raw:
            return result
        for item in raw.split(';'):
            if '=' not in item:
                continue
            key, value = item.split('=', 1)
            result[key.strip()] = value.strip()
        return result

    @staticmethod
    def _origin_from_referer(referer: Optional[str]) -> Optional[str]:
        if not referer:
            return None
        parsed = urlparse(referer)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f'{parsed.scheme}://{parsed.netloc}'

    @staticmethod
    async def _reject(send: Send, *, detail: str) -> None:
        payload = {
            'type': 'https://api.example.com/problems/csrf',
            'title': '请求被拒绝',
            'status': 403,
            'detail': detail,
            'errorCode': 10013,
        }
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers = [
            (b'content-type', b'application/problem+json; charset=utf-8'),
            (b'content-length', str(len(body)).encode('ascii')),
        ]
        await send({'type': 'http.response.start', 'status': 403, 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in (raw or '').split(',') if item.strip()]


def add_csrf_guard_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CsrfGuardASGIMiddleware,
        enabled=SecurityConfig.security_csrf_enabled,
        allowed_origins=_parse_csv(SecurityConfig.security_allowed_origins),
        protected_paths=_parse_csv(SecurityConfig.security_csrf_protected_paths),
        csrf_header_name=SecurityConfig.security_csrf_header_name,
        csrf_cookie_name=SecurityConfig.security_csrf_cookie_name,
        protected_write_paths=_parse_csv(SecurityConfig.security_csrf_protected_write_paths),
        access_cookie_name=SecurityConfig.security_access_cookie_name,
    )
