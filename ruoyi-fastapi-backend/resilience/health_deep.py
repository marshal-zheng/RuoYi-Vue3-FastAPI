"""Deep health checks for critical dependencies."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterable, Tuple
from urllib.request import Request, urlopen

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class DeepHealthChecker:
    """Concurrent dependency checker with bounded timeout."""

    def __init__(
        self,
        *,
        db_engine: AsyncEngine,
        redis_client: Any,
        external_urls: Iterable[str],
        timeout_seconds: float = 2.0,
    ) -> None:
        self._db_engine = db_engine
        self._redis_client = redis_client
        self._external_urls = list(external_urls)
        self._timeout_seconds = timeout_seconds

    async def run(self) -> Tuple[int, Dict[str, Any]]:
        checks = {
            'database': self._check_database,
            'redis': self._check_redis,
        }
        for url in self._external_urls:
            checks[f'external:{url}'] = self._build_external_check(url)

        tasks = {name: asyncio.create_task(self._run_with_timeout(name, checker)) for name, checker in checks.items()}
        results: Dict[str, Dict[str, Any]] = {}
        for name, task in tasks.items():
            results[name] = await task

        critical_failed = any(
            item.get('status') != 'healthy' and name in ('database', 'redis')
            for name, item in results.items()
        )
        overall_status = 'unhealthy' if critical_failed else 'healthy'
        http_status = 503 if critical_failed else 200
        payload = {
            'status': overall_status,
            'timeoutSeconds': self._timeout_seconds,
            'dependencies': results,
        }
        return http_status, payload

    async def _run_with_timeout(self, name: str, checker) -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(checker(), timeout=self._timeout_seconds)
        except asyncio.TimeoutError:
            return {
                'status': 'degraded',
                'detail': 'timeout',
                'latencyMs': round((time.perf_counter() - started) * 1000.0, 3),
            }
        except Exception as exc:
            return {
                'status': 'unhealthy',
                'detail': str(exc),
                'latencyMs': round((time.perf_counter() - started) * 1000.0, 3),
            }

        result['latencyMs'] = round((time.perf_counter() - started) * 1000.0, 3)
        return result

    async def _check_database(self) -> Dict[str, Any]:
        async with self._db_engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        return {'status': 'healthy', 'detail': 'ok'}

    async def _check_redis(self) -> Dict[str, Any]:
        if self._redis_client is None:
            return {'status': 'degraded', 'detail': 'not_initialized'}
        pong = await self._redis_client.ping()
        if not pong:
            return {'status': 'unhealthy', 'detail': 'ping_failed'}
        return {'status': 'healthy', 'detail': 'ok'}

    def _build_external_check(self, url: str):
        async def _check() -> Dict[str, Any]:
            def _request() -> int:
                req = Request(url=url, method='GET')
                with urlopen(req, timeout=self._timeout_seconds) as resp:  # noqa: S310
                    return int(getattr(resp, 'status', 200))

            status_code = await asyncio.to_thread(_request)
            if 200 <= status_code < 400:
                return {'status': 'healthy', 'detail': f'http_{status_code}'}
            return {'status': 'degraded', 'detail': f'http_{status_code}'}

        return _check
