"""Path-level request body caps and receive-time limits for upload endpoints.

Runs before Starlette spools multipart data to disk, so oversized or slow uploads are rejected at the
earliest point even when Content-Length is missing or forged (chunked bodies are counted as received).
Purpose-specific limits are still enforced byte-exactly after parsing.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

from config.env import ErrorHandlingConfig, FileAssetConfig
from middlewares.route_path import route_path
from middlewares.trace_middleware import get_request_id
from modules.file_assets.domain.errors import AssetReceiveTimeoutError, AssetTooLargeError
from modules.file_assets.domain.types import MAX_ATTACHMENT_BYTES, MAX_IMAGE_BYTES

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

MULTIPART_OVERHEAD = 64 * 1024
DEFAULT_UPLOAD_LIMITS = {
    '/file-assets/uploads': MAX_ATTACHMENT_BYTES + MULTIPART_OVERHEAD,
    '/system/user/profile/avatar': MAX_IMAGE_BYTES + MULTIPART_OVERHEAD,
}


class UploadLimitASGIMiddleware:
    def __init__(self, app: ASGIApp, *, limits: dict[str, int], receive_timeout_seconds: float):
        self.app = app
        self.limits = dict(limits)
        self.receive_timeout_seconds = receive_timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get('type') != 'http' or str(scope.get('method', '')).upper() != 'POST':
            await self.app(scope, receive, send)
            return
        limit = self.limits.get(route_path(scope).rstrip('/'))
        if limit is None:
            await self.app(scope, receive, send)
            return
        declared = self._content_length(scope)
        if declared is not None and declared > limit:
            await self._reject(scope, send, limit)
            return

        received = 0
        deadline = time.monotonic() + self.receive_timeout_seconds

        async def limited_receive() -> Message:
            nonlocal received
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssetReceiveTimeoutError()
            try:
                message = await asyncio.wait_for(receive(), timeout=remaining)
            except TimeoutError:
                raise AssetReceiveTimeoutError() from None
            if message.get('type') == 'http.request':
                received += len(message.get('body', b''))
                if received > limit:
                    raise AssetTooLargeError('REQUEST_TOO_LARGE', f'上传请求超过 {limit // (1024 * 1024)} MiB 限制')
            return message

        await self.app(scope, limited_receive, send)

    @staticmethod
    def _content_length(scope: Scope) -> int | None:
        for key, value in scope.get('headers', []):
            if key.lower() == b'content-length':
                try:
                    return int(value)
                except ValueError:
                    return None
        return None

    @staticmethod
    async def _reject(scope: Scope, send: Send, limit: int) -> None:
        base_url = str(ErrorHandlingConfig.problem_type_base_url or '').strip().rstrip('/')
        payload = {
            'type': f'{base_url}/file-asset-too-large' if base_url else 'about:blank',
            'title': '文件过大',
            'status': 413,
            'detail': f'上传请求超过 {limit // (1024 * 1024)} MiB 限制',
            'instance': str(scope.get('path', '')),
            'errorCode': 48003,
            'reasonCode': 'REQUEST_TOO_LARGE',
        }
        request_id = get_request_id()
        if request_id:
            payload['requestId'] = request_id
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        await send(
            {
                'type': 'http.response.start',
                'status': 413,
                'headers': [
                    (b'content-type', b'application/problem+json'),
                    (b'content-length', str(len(body)).encode('ascii')),
                    (b'connection', b'close'),
                ],
            }
        )
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})


def add_upload_limit_middleware(app: FastAPI) -> None:
    app.add_middleware(
        UploadLimitASGIMiddleware,
        limits=DEFAULT_UPLOAD_LIMITS,
        receive_timeout_seconds=FileAssetConfig.file_asset_upload_receive_timeout_seconds,
    )
