from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.system.application.services.capability_gate_service import (
    CapabilityGateService,
    get_capability_gate_service,
    invalidate_capability_gate_service,
)
from scripts.internal.db_workflow.capability_models import CapabilityRuntimeGate


class _FakeRedis:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = dict(values or {})

    async def get(self, key: str):
        return self.values.get(key)


def _request_with_redis(redis: _FakeRedis | None):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=redis)))


@pytest.mark.asyncio
async def test_module_without_declared_runtime_gate_is_enabled() -> None:
    service = CapabilityGateService(runtime_gates={})

    assert await service.is_module_enabled(_request_with_redis(_FakeRedis()), 'platform') is True


@pytest.mark.asyncio
async def test_runtime_gate_reads_true_from_sys_config_cache() -> None:
    service = CapabilityGateService(
        runtime_gates={
            'platform': CapabilityRuntimeGate(
                module_key='platform',
                config_key='capability.platform.enabled',
                default_enabled=False,
            )
        }
    )

    request = _request_with_redis(_FakeRedis({'sys_config:capability.platform.enabled': 'true'}))

    assert await service.is_module_enabled(request, 'platform') is True


@pytest.mark.asyncio
async def test_runtime_gate_defaults_to_disabled_when_config_missing_or_invalid() -> None:
    service = CapabilityGateService(
        runtime_gates={
            'platform': CapabilityRuntimeGate(
                module_key='platform',
                config_key='capability.platform.enabled',
                default_enabled=False,
            )
        }
    )

    assert await service.is_module_enabled(_request_with_redis(_FakeRedis()), 'platform') is False
    assert (
        await service.is_module_enabled(
            _request_with_redis(_FakeRedis({'sys_config:capability.platform.enabled': 'not-bool'})),
            'platform',
        )
        is False
    )


def test_capability_gate_service_is_reloaded_after_invalidation(monkeypatch) -> None:
    service_versions: list[str] = []

    def fake_from_declarations(cls, *, modules_root=None):
        version = f'v{len(service_versions) + 1}'
        service_versions.append(version)
        return CapabilityGateService(
            runtime_gates={
                'platform': CapabilityRuntimeGate(
                    module_key='platform',
                    config_key=f'capability.platform.{version}.enabled',
                    default_enabled=False,
                )
            }
        )

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    monkeypatch.setattr(CapabilityGateService, 'from_declarations', classmethod(fake_from_declarations))

    first_service = get_capability_gate_service(request)
    second_service = get_capability_gate_service(request)
    invalidate_capability_gate_service(request.app)
    third_service = get_capability_gate_service(request)

    assert first_service is second_service
    assert first_service.get_runtime_gate('platform').config_key == 'capability.platform.v1.enabled'
    assert third_service is not first_service
    assert third_service.get_runtime_gate('platform').config_key == 'capability.platform.v2.enabled'
