from fastapi import FastAPI

from middlewares.handle import handle_middleware
from middlewares.request_logging_middleware import RequestLoggingASGIMiddleware


def _middleware_classes(app: FastAPI) -> list[type]:
    return [middleware.cls for middleware in app.user_middleware]


def test_handle_middleware_skips_request_logging_when_disabled(monkeypatch):
    monkeypatch.setattr('middlewares.handle.LogConfig.request_logging_enabled', False)
    app = FastAPI()

    handle_middleware(app)

    assert RequestLoggingASGIMiddleware not in _middleware_classes(app)


def test_handle_middleware_adds_request_logging_when_enabled(monkeypatch):
    monkeypatch.setattr('middlewares.handle.LogConfig.request_logging_enabled', True)
    app = FastAPI()

    handle_middleware(app)

    assert RequestLoggingASGIMiddleware in _middleware_classes(app)
