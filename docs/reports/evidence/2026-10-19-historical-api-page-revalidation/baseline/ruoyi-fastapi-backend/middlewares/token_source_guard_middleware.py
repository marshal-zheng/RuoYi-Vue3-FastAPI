from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from utils.log_util import logger


class TokenSourceGuardASGIMiddleware:
    """Reject token from query/cookie/form sources for protected APIs."""

    def __init__(self, app: ASGIApp, *, exclude_prefixes: list[str]):
        self.app = app
        self.exclude_prefixes = [prefix for prefix in exclude_prefixes if prefix]
        self.disallowed_param_names = {'token', 'access_token', 'admin-token'}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        path = str(scope.get('path', ''))
        if any(path.startswith(prefix) for prefix in self.exclude_prefixes):
            await self.app(scope, receive, send)
            return

        headers = self._decode_headers(scope.get('headers', []))
        violation = self._query_violation(scope)
        if violation is None:
            violation = self._cookie_violation(headers)

        body: bytes | None = None
        if violation is None and self._is_form_request(headers):
            body = await self._drain_request_body(receive)
            violation = self._form_violation(body)

        if violation is not None:
            logger.warning('token_source_block path={} source={}', path, violation)
            await self._reject(send=send, source=violation)
            return

        replay_receive = self._build_replay_receive(body, receive) if body is not None else receive
        await self.app(scope, replay_receive, send)

    @staticmethod
    def _decode_headers(raw_headers) -> dict[str, str]:
        decoded: dict[str, str] = {}
        for key, value in raw_headers:
            decoded[key.decode('latin-1').lower()] = value.decode('latin-1')
        return decoded

    def _query_violation(self, scope: Scope) -> str | None:
        raw_query = scope.get('query_string', b'')
        if not raw_query:
            return None
        parsed = parse_qs(raw_query.decode('utf-8', errors='ignore'), keep_blank_values=True)
        for name in self.disallowed_param_names:
            if name in parsed:
                return f'query:{name}'
        return None

    def _cookie_violation(self, headers: dict[str, str]) -> str | None:
        raw_cookie = headers.get('cookie', '')
        if not raw_cookie:
            return None
        for item in raw_cookie.split(';'):
            if '=' not in item:
                continue
            key = item.split('=', 1)[0].strip().lower()
            if key in self.disallowed_param_names:
                return f'cookie:{key}'
        return None

    @staticmethod
    def _is_form_request(headers: dict[str, str]) -> bool:
        content_type = headers.get('content-type', '').lower()
        return 'application/x-www-form-urlencoded' in content_type

    def _form_violation(self, body: bytes) -> str | None:
        if not body:
            return None
        parsed = parse_qs(body.decode('utf-8', errors='ignore'), keep_blank_values=True)
        for name in self.disallowed_param_names:
            if name in parsed:
                return f'form:{name}'
        return None

    @staticmethod
    async def _drain_request_body(receive: Receive) -> bytes:
        chunks = []
        while True:
            message = await receive()
            if message.get('type') == 'http.disconnect':
                break
            if message.get('type') != 'http.request':
                continue
            chunk = message.get('body', b'') or b''
            if chunk:
                chunks.append(chunk)
            if not message.get('more_body', False):
                break
        return b''.join(chunks)

    @staticmethod
    def _build_replay_receive(body: bytes, receive: Receive) -> Receive:
        state = {'sent': False}

        async def replay_receive() -> Message:
            if not state['sent']:
                state['sent'] = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            # Resume server events after the single body replay.
            return await receive()

        return replay_receive

    @staticmethod
    async def _reject(send: Send, *, source: str) -> None:
        payload = {
            'type': 'https://api.example.com/problems/token-source',
            'title': '非法认证来源',
            'status': 400,
            'detail': f'Disallowed token source: {source}',
            'errorCode': 10013,
        }
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers = [
            (b'content-type', b'application/problem+json; charset=utf-8'),
            (b'content-length', str(len(body)).encode('ascii')),
        ]
        await send({'type': 'http.response.start', 'status': 400, 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})


def add_token_source_guard_middleware(app: FastAPI) -> None:
    app.add_middleware(
        TokenSourceGuardASGIMiddleware,
        exclude_prefixes=[
            '/login',
            '/captchaImage',
            '/register',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/.well-known/jwks.json',
            '/auth/m2m/token',
        ],
    )
