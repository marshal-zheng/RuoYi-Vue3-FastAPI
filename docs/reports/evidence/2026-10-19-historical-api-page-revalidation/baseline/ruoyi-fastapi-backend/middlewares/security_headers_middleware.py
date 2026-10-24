from __future__ import annotations

import secrets

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config.env import SecurityConfig


class SecurityHeadersASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message.get('type') == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.extend(self._build_security_headers())
                message['headers'] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _build_security_headers(self) -> list[tuple[bytes, bytes]]:
        nonce = secrets.token_urlsafe(16)
        frame_ancestors = self._build_frame_ancestors()
        csp_parts = [
            "default-src 'self'",
            f"script-src {SecurityConfig.security_csp_script_src} 'nonce-{nonce}'",
            f"style-src {SecurityConfig.security_csp_style_src}",
            f"img-src {SecurityConfig.security_csp_img_src}",
            f"connect-src {SecurityConfig.security_csp_connect_src}",
            "object-src 'none'",
            "base-uri 'self'",
            f"frame-ancestors {frame_ancestors}",
        ]
        csp_value = '; '.join(csp_parts)

        headers: list[tuple[bytes, bytes]] = [
            (b'x-content-type-options', b'nosniff'),
            (b'x-frame-options', b'SAMEORIGIN'),
            (b'referrer-policy', b'strict-origin-when-cross-origin'),
            (b'permissions-policy', b'camera=(), microphone=(), geolocation=()'),
        ]

        if SecurityConfig.security_csp_enabled:
            headers.append((b'content-security-policy', csp_value.encode('utf-8')))
            headers.append((b'x-csp-nonce', nonce.encode('utf-8')))

        if SecurityConfig.security_hsts_enabled:
            hsts = f'max-age={SecurityConfig.security_hsts_max_age}; includeSubDomains'
            headers.append((b'strict-transport-security', hsts.encode('ascii')))

        return headers

    @staticmethod
    def _build_frame_ancestors() -> str:
        configured = SecurityConfig.security_frame_ancestors.strip()
        if configured:
            return configured
        allowed = [item.strip() for item in SecurityConfig.security_allowed_origins.split(',') if item.strip()]
        if not allowed:
            return "'self'"
        return ' '.join(["'self'"] + allowed)


def add_security_headers_middleware(app: FastAPI) -> None:
    app.add_middleware(SecurityHeadersASGIMiddleware)
