from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from modules.system.application.services.cache_service import CacheService


@pytest.mark.asyncio
async def test_single_key_delete_never_expands_a_suffix_or_glob():
    redis = SimpleNamespace(delete=AsyncMock(), keys=AsyncMock())
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=redis)))
    await CacheService().clear_cache_monitor_cache_key_services(request, 'sys_config:own[*]')
    redis.delete.assert_awaited_once_with('sys_config:own[*]')
    redis.keys.assert_not_awaited()


@pytest.mark.asyncio
async def test_namespace_scan_bounds_and_escapes_literal_name():
    patterns = []

    async def scan_iter(*, match):
        patterns.append(match)
        yield 'own[*]:one'
        yield 'own[*]:nested:two'

    redis = SimpleNamespace(scan_iter=scan_iter, delete=AsyncMock())
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=redis)))
    service = CacheService()
    assert await service.get_cache_monitor_cache_key_services(request, 'own[*]') == ['one', 'nested:two']
    await service.clear_cache_monitor_cache_name_services(request, 'own[*]')
    assert patterns == [r'own\[\*\]:*', r'own\[\*\]:*']
    redis.delete.assert_awaited_once_with('own[*]:one', 'own[*]:nested:two')
