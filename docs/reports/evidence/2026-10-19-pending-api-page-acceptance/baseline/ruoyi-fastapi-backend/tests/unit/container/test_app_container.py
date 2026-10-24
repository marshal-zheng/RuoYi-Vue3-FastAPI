from __future__ import annotations

import pytest

from container import AppContainer, ContainerBindingError, ProviderResolutionError


class FakeRedis:
    def __init__(self, healthy: bool = True):
        self.healthy = healthy
        self.closed = False

    async def ping(self) -> bool:
        return self.healthy

    async def close(self) -> None:
        self.closed = True


def test_validate_bindings_success() -> None:
    container = AppContainer()
    container.validate_bindings()


def test_validate_bindings_missing_provider() -> None:
    container = AppContainer()
    container._service_factories.pop('project_service')  # noqa: SLF001
    with pytest.raises(ContainerBindingError):
        container.validate_bindings()


def test_override_and_reset_provider() -> None:
    container = AppContainer()
    marker = object()

    container.override('project_service', lambda _session: marker)
    resolved = container.resolve_service('project_service', session=object())  # type: ignore[arg-type]
    assert resolved is marker

    container.reset_override('project_service')
    resolved = container.resolve_service('project_service', session=object())  # type: ignore[arg-type]
    assert resolved.__class__.__name__ == 'ProjectService'


def test_override_unknown_provider() -> None:
    container = AppContainer()
    with pytest.raises(ProviderResolutionError):
        container.override('unknown_service', lambda _session: object())


@pytest.mark.asyncio
async def test_initialize_and_shutdown_runtime_in_test_mode() -> None:
    container = AppContainer()
    redis = FakeRedis(healthy=True)

    resolved_redis = await container.initialize_runtime(
        redis_client=redis,
        initialize_scheduler=False,
    )
    assert resolved_redis is redis
    assert container.is_runtime_ready() is True
    health = container.provider_health_summary()
    assert health['redis']['healthy'] is True
    assert health['scheduler']['detail'] == 'disabled_in_test_mode'

    await container.shutdown_runtime()
    assert redis.closed is True
    health = container.provider_health_summary()
    assert health['redis']['detail'] == 'closed'


def test_export_dependency_graph_formats() -> None:
    container = AppContainer()
    dot = container.export_dependency_graph(output_format='dot')
    text = container.export_dependency_graph(output_format='text')
    assert 'digraph AppContainer' in dot
    assert 'project_service' in dot
    assert 'AppContainer' in text
    assert 'service_provider: simulation_service' in text
