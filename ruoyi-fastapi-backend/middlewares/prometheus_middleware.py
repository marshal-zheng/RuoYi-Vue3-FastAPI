"""
Prometheus request metrics middleware.
"""
import time
from typing import Iterable, Sequence

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Scope, Send

from utils.prometheus_metrics import PrometheusMetricsRegistry


class PrometheusMetricsASGIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        exclude_paths: Sequence[str] = (),
    ) -> None:
        self.app = app
        self.exclude_paths = tuple(exclude_paths or ())

    async def __call__(self, scope: Scope, receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "")).upper()
        path = str(scope.get("path", ""))
        if self._is_excluded(path):
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message.get("status", status_code))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._observe(scope, method=method, path=path, status_code=status_code, started_at=started_at)
            raise

        self._observe(scope, method=method, path=path, status_code=status_code, started_at=started_at)

    def _observe(self, scope: Scope, *, method: str, path: str, status_code: int, started_at: float) -> None:
        app = scope.get("app")
        if app is None:
            return

        state = getattr(app, "state", None)
        if state is None:
            return

        registry = getattr(state, "metrics_registry", None)
        if not isinstance(registry, PrometheusMetricsRegistry):
            return

        duration_seconds = max(0.0, time.perf_counter() - started_at)
        registry.observe_http_request(
            method=method,
            path=path,
            status_code=int(status_code),
            duration_seconds=duration_seconds,
        )

    def _is_excluded(self, path: str) -> bool:
        for prefix in self.exclude_paths:
            if path.startswith(prefix):
                return True
        return False


def add_prometheus_metrics_middleware(app: FastAPI, exclude_paths: Iterable[str] = ()) -> None:
    app.add_middleware(PrometheusMetricsASGIMiddleware, exclude_paths=tuple(exclude_paths))

