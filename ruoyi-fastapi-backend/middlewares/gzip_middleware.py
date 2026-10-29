import re

from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from middlewares.route_path import route_path

# File content keeps its exact bytes, length and strong ETag; it is mostly compressed media anyway.
_UNCOMPRESSED_PATHS = re.compile(r'^/file-assets/[^/]+/content$')


class SelectiveGZipMiddleware(GZipMiddleware):
    def __init__(self, app: ASGIApp, minimum_size: int = 500, compresslevel: int = 9) -> None:
        super().__init__(app, minimum_size=minimum_size, compresslevel=compresslevel)
        self._plain_app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http' and _UNCOMPRESSED_PATHS.match(route_path(scope)):
            await self._plain_app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)


def add_gzip_middleware(app: FastAPI):
    """
    添加gzip压缩中间件

    :param app: FastAPI对象
    :return:
    """
    app.add_middleware(SelectiveGZipMiddleware, minimum_size=1000, compresslevel=9)
