from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

from scripts.internal.db_workflow import managed_data_fast_reconcile_service as service_module
from scripts.internal.db_workflow.managed_data_fast_reconcile_service import ManagedDataFastReconcileService
from tests.unit.scripts.test_dev_sync_service import _build_session_factory, _bundle, _seed_roles, _snapshot


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ex=None, nx: bool = False) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self._store:
                removed += 1
                self._store.pop(key, None)
        return removed

    async def keys(self, pattern: str = '*') -> list[str]:
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [key for key in self._store if key.startswith(prefix)]
        return [key for key in self._store if key == pattern]


def test_fast_reconcile_applies_bundle_refreshes_redis_and_skips_same_checksum(monkeypatch, tmp_path) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)
    redis = _FakeRedis()
    invalidation_calls: list[str] = []

    async def fake_invalidate() -> None:
        invalidation_calls.append('invalidate')

    monkeypatch.setattr(service_module, 'invalidate_managed_data_query_caches', fake_invalidate)

    bundle = _bundle(tmp_path, include_config=True)
    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=lambda: SimpleNamespace(load=lambda: bundle),
        redis_client=redis,
    )

    try:
        first_report = asyncio.run(service.reconcile(trigger='file_change'))
        second_report = asyncio.run(
            service.reconcile(
                trigger='file_change',
                previous_compiled_checksum=first_report.compiled_checksum,
            )
        )
        current = _snapshot(session_factory)
    finally:
        asyncio.run(engine.dispose())

    assert first_report.success is True
    assert first_report.compiled_checksum == 'compiled-sha-1'
    assert first_report.state_changed is True
    assert first_report.changed_domains == ('menus', 'role_grants', 'dict_types', 'dict_data', 'configs')
    assert first_report.menu_reload_required is True
    assert first_report.postcondition_status == 'clean'
    assert current['menus'] == {10: '系统管理', 20: '参数配置'}
    assert current['configs'] == {1: 'device.default.timeout'}
    assert invalidation_calls == ['invalidate']

    assert asyncio.run(redis.get('sys_config:device.default.timeout')) == '30'
    dict_payload = json.loads(asyncio.run(redis.get('sys_dict:sys_device_status')))
    assert dict_payload[0]['dictType'] == 'sys_device_status'
    assert dict_payload[0]['dictValue'] == 'enabled'

    assert second_report.success is True
    assert second_report.skipped_reason == 'compiled_checksum_unchanged'
    assert second_report.state_changed is False
    assert second_report.affected_objects == ()
    assert second_report.changed_domains == ()
    assert second_report.menu_reload_required is False
    assert invalidation_calls == ['invalidate']


def test_changed_domains_for_affected_objects_ignores_non_menu_mutations() -> None:
    assert service_module.changed_domains_for_affected_objects(
        (
            'sys_config:device.default.timeout',
            'sys_dict_type:sys_device_status',
            'sys_dict_data:sys_device_status:enabled',
        )
    ) == ('dict_types', 'dict_data', 'configs')


def test_fast_reconcile_rolls_back_when_postcondition_verification_fails(monkeypatch, tmp_path) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)

    async def fake_invalidate() -> None:
        raise AssertionError('cache invalidation should not run on failed reconcile')

    async def fake_refresh(*_args, **_kwargs) -> None:
        raise AssertionError('redis refresh should not run on failed reconcile')

    async def fake_verify(self, *, declaration_bundle, role_key_to_id):
        return service_module.PostconditionVerificationResult(
            duration_ms=1,
            pending_operation_objects=('sys_config:device.default.timeout',),
            metadata_drift_objects=('sys_config:device.default.timeout',),
            residual_objects=('sys_config:device.default.timeout',),
        )

    monkeypatch.setattr(service_module, 'invalidate_managed_data_query_caches', fake_invalidate)
    monkeypatch.setattr(service_module, 'refresh_managed_data_redis_caches', fake_refresh)
    monkeypatch.setattr(service_module.PostconditionVerifier, 'verify', fake_verify)

    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=lambda: SimpleNamespace(load=lambda: _bundle(tmp_path, include_config=True)),
        redis_client=_FakeRedis(),
    )

    try:
        report = asyncio.run(service.reconcile(trigger='file_change'))
        current = _snapshot(session_factory)
    finally:
        asyncio.run(engine.dispose())

    assert report.success is False
    assert report.postcondition_status == 'drift-detected'
    assert report.residual_objects == ('sys_config:device.default.timeout',)
    assert current['menus'] == {}
    assert current['role_menus'] == set()
    assert current['dict_types'] == {}
    assert current['dict_data'] == {}
    assert current['configs'] == {}
    assert current['workflow_objects'] == {}


def test_fast_reconcile_rolls_back_when_runtime_exception_occurs_after_apply(monkeypatch, tmp_path) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)

    async def fake_invalidate() -> None:
        raise AssertionError('cache invalidation should not run on failed reconcile')

    async def fake_refresh(*_args, **_kwargs) -> None:
        raise AssertionError('redis refresh should not run on failed reconcile')

    async def fake_verify(self, *, declaration_bundle, role_key_to_id):
        raise RuntimeError('verify exploded')

    monkeypatch.setattr(service_module, 'invalidate_managed_data_query_caches', fake_invalidate)
    monkeypatch.setattr(service_module, 'refresh_managed_data_redis_caches', fake_refresh)
    monkeypatch.setattr(service_module.PostconditionVerifier, 'verify', fake_verify)

    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=lambda: SimpleNamespace(load=lambda: _bundle(tmp_path, include_config=True)),
        redis_client=_FakeRedis(),
    )

    try:
        report = asyncio.run(service.reconcile(trigger='file_change'))
        current = _snapshot(session_factory)
    finally:
        asyncio.run(engine.dispose())

    assert report.success is False
    assert report.postcondition_status == 'skipped'
    assert report.error == 'verify exploded'
    assert current['menus'] == {}
    assert current['role_menus'] == set()
    assert current['dict_types'] == {}
    assert current['dict_data'] == {}
    assert current['configs'] == {}
    assert current['workflow_objects'] == {}
