"""Application container and provider registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from container.providers import SERVICE_FACTORY_REGISTRY
from config.database import AsyncSessionLocal
from config.env import CacheConfig
from config.get_redis import RedisUtil
from config.get_scheduler import SchedulerUtil
from utils.count_cache import init_count_cache
from ports import IRedisClient
from utils.log_util import logger
from utils.query_cache import init_query_cache


class ContainerError(RuntimeError):
    """Base error for container lifecycle and binding failures."""


class ContainerBindingError(ContainerError):
    """Raised when required providers are missing or invalid."""


class ContainerInitializationError(ContainerError):
    """Raised when infrastructure providers cannot initialize."""


class ProviderResolutionError(ContainerError):
    """Raised when a provider cannot resolve a requested dependency."""


ServiceFactory = Callable[[Optional[AsyncSession]], Any]


@dataclass
class ProviderHealth:
    """Runtime status summary for providers."""

    initialized: bool = False
    healthy: bool = False
    detail: str = 'not_initialized'

    def to_dict(self) -> dict[str, Any]:
        return {
            'initialized': self.initialized,
            'healthy': self.healthy,
            'detail': self.detail,
        }


class AppContainer:
    """Application-level container with request-scoped service factories."""

    def __init__(self) -> None:
        self._session_factory = AsyncSessionLocal
        self._service_factories: dict[str, ServiceFactory] = dict(SERVICE_FACTORY_REGISTRY)
        self._overrides: dict[str, ServiceFactory] = {}
        self._provider_health: dict[str, ProviderHealth] = {
            'redis': ProviderHealth(),
            'scheduler': ProviderHealth(),
            'query_cache': ProviderHealth(),
            'count_cache': ProviderHealth(),
        }
        self._redis_client: Optional[IRedisClient] = None
        self._scheduler_started: bool = False
        self._query_cache: Any = None
        self._count_cache: Any = None

    @property
    def redis_client(self) -> Optional[IRedisClient]:
        return self._redis_client

    @property
    def query_cache(self) -> Any:
        return self._query_cache

    @property
    def count_cache(self) -> Any:
        return self._count_cache

    def validate_bindings(self) -> None:
        required = {
            'dict_type_service',
            'dict_data_service',
            'project_service',
            'project_topology_service',
            'protocol_service',
            'simulation_service',
        }
        missing = sorted(name for name in required if name not in self._service_factories)
        if missing:
            raise ContainerBindingError(f'Missing provider bindings: {missing}')
        invalid = sorted(name for name, provider in self._service_factories.items() if not callable(provider))
        if invalid:
            raise ContainerBindingError(f'Non-callable provider bindings: {invalid}')

    def override(self, provider_name: str, provider: ServiceFactory) -> None:
        if provider_name not in self._service_factories:
            raise ProviderResolutionError(f'Unknown provider `{provider_name}`')
        if not callable(provider):
            raise ProviderResolutionError(f'Override provider `{provider_name}` is not callable')
        self._overrides[provider_name] = provider

    def reset_override(self, provider_name: Optional[str] = None) -> None:
        if provider_name is None:
            self._overrides.clear()
            return
        self._overrides.pop(provider_name, None)

    def resolve_service(self, provider_name: str, session: AsyncSession | None = None) -> Any:
        provider = self._overrides.get(provider_name) or self._service_factories.get(provider_name)
        if provider is None:
            raise ProviderResolutionError(f'Provider `{provider_name}` is not registered')
        try:
            return provider(session)
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ProviderResolutionError(f'Provider `{provider_name}` failed to resolve: {exc}') from exc

    def dict_type_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('dict_type_service', session)

    def dict_data_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('dict_data_service', session)

    def project_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('project_service', session)

    def project_topology_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('project_topology_service', session)

    def protocol_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('protocol_service', session)

    def simulation_service(self, session: AsyncSession) -> Any:
        return self.resolve_service('simulation_service', session)

    def resolve_infra_service(self, provider_name: str) -> Any:
        return self.resolve_service(provider_name, None)

    def create_task_session(self):
        """Create background-task scoped db session."""
        return self._session_factory()

    async def initialize_runtime(
        self,
        *,
        redis_client: Optional[IRedisClient] = None,
        initialize_scheduler: bool = True,
    ) -> IRedisClient:
        try:
            if redis_client is None:
                redis_client = await RedisUtil.create_redis_pool()
                await RedisUtil.init_sys_dict(redis_client)
                await RedisUtil.init_sys_config(redis_client)
            self._redis_client = redis_client

            redis_healthy = False
            try:
                redis_healthy = bool(await redis_client.ping())
            except Exception as ping_error:
                self._provider_health['redis'] = ProviderHealth(
                    initialized=True,
                    healthy=False,
                    detail=f'ping_failed: {ping_error}',
                )
                raise ContainerInitializationError(f'Redis ping failed: {ping_error}') from ping_error

            self._provider_health['redis'] = ProviderHealth(
                initialized=True,
                healthy=redis_healthy,
                detail='ready' if redis_healthy else 'unhealthy',
            )
            if not redis_healthy:
                raise ContainerInitializationError('Redis health check failed')

            if initialize_scheduler:
                await SchedulerUtil.init_system_scheduler()
                self._scheduler_started = True
                self._provider_health['scheduler'] = ProviderHealth(
                    initialized=True,
                    healthy=True,
                    detail='ready',
                )
            else:
                self._scheduler_started = False
                self._provider_health['scheduler'] = ProviderHealth(
                    initialized=False,
                    healthy=True,
                    detail='disabled_in_test_mode',
                )

            self._query_cache = init_query_cache(
                redis_client=redis_client if CacheConfig.query_cache_enabled else None,
                default_ttl=CacheConfig.query_cache_default_ttl,
                key_prefix='query_cache',
                is_async=True,
            )
            self._provider_health['query_cache'] = ProviderHealth(
                initialized=True,
                healthy=True,
                detail='enabled' if CacheConfig.query_cache_enabled else 'disabled',
            )

            self._count_cache = init_count_cache(
                redis_client=redis_client if CacheConfig.count_cache_enabled else None,
                default_ttl=CacheConfig.count_cache_default_ttl,
                key_prefix=CacheConfig.count_cache_key_prefix,
                enabled=CacheConfig.count_cache_enabled,
            )
            self._provider_health['count_cache'] = ProviderHealth(
                initialized=True,
                healthy=True,
                detail='enabled' if CacheConfig.count_cache_enabled else 'disabled',
            )
        except Exception as exc:
            if isinstance(exc, ContainerInitializationError):
                raise
            raise ContainerInitializationError(f'Container runtime initialization failed: {exc}') from exc

        logger.info('Application container runtime initialized')
        return redis_client

    async def shutdown_runtime(self) -> None:
        if self._scheduler_started:
            try:
                await SchedulerUtil.close_system_scheduler()
                self._provider_health['scheduler'] = ProviderHealth(
                    initialized=False,
                    healthy=True,
                    detail='closed',
                )
            except Exception as exc:
                self._provider_health['scheduler'] = ProviderHealth(
                    initialized=True,
                    healthy=False,
                    detail=f'close_failed: {exc}',
                )
                logger.error(f'Container scheduler shutdown failed: {exc}')
            finally:
                self._scheduler_started = False

        if self._redis_client is not None:
            try:
                await self._redis_client.close()
                self._provider_health['redis'] = ProviderHealth(
                    initialized=False,
                    healthy=True,
                    detail='closed',
                )
            except Exception as exc:
                self._provider_health['redis'] = ProviderHealth(
                    initialized=True,
                    healthy=False,
                    detail=f'close_failed: {exc}',
                )
                logger.error(f'Container redis shutdown failed: {exc}')
            finally:
                self._redis_client = None

        self._query_cache = None
        self._provider_health['query_cache'] = ProviderHealth(
            initialized=False,
            healthy=True,
            detail='closed',
        )
        self._count_cache = None
        self._provider_health['count_cache'] = ProviderHealth(
            initialized=False,
            healthy=True,
            detail='closed',
        )

    def provider_health_summary(self) -> dict[str, dict[str, Any]]:
        return {name: health.to_dict() for name, health in self._provider_health.items()}

    def is_runtime_ready(self) -> bool:
        redis_state = self._provider_health['redis']
        scheduler_state = self._provider_health['scheduler']
        query_cache_state = self._provider_health['query_cache']
        count_cache_state = self._provider_health['count_cache']
        scheduler_ready = scheduler_state.healthy or scheduler_state.detail == 'disabled_in_test_mode'
        query_cache_ready = query_cache_state.healthy and query_cache_state.initialized
        count_cache_ready = count_cache_state.healthy and count_cache_state.initialized
        return (
            redis_state.initialized
            and redis_state.healthy
            and scheduler_ready
            and query_cache_ready
            and count_cache_ready
        )

    def export_dependency_graph(self, output_format: str = 'dot') -> str:
        providers = sorted(self._service_factories.keys())
        if output_format == 'text':
            lines = [
                'AppContainer',
                '- infrastructure: redis, scheduler',
                '- shared: request_session_factory, task_session_factory',
            ]
            lines.extend(f'- service_provider: {name}' for name in providers)
            return '\n'.join(lines)

        if output_format != 'dot':
            raise ValueError(f'Unsupported graph format: {output_format}')

        lines = [
            'digraph AppContainer {',
            '  rankdir=LR;',
            '  app_container [shape=box,label="AppContainer"];',
            '  request_session [shape=ellipse,label="Request AsyncSession"];',
            '  task_session [shape=ellipse,label="Task AsyncSession"];',
            '  redis_provider [shape=ellipse,label="Redis Provider"];',
            '  scheduler_provider [shape=ellipse,label="Scheduler Provider"];',
            '  app_container -> redis_provider;',
            '  app_container -> scheduler_provider;',
            '  app_container -> request_session;',
            '  app_container -> task_session;',
        ]
        for name in providers:
            lines.append(f'  {name} [shape=component,label="{name}"];')
            lines.append(f'  app_container -> {name};')
            lines.append(f'  request_session -> {name};')
        lines.append('}')
        return '\n'.join(lines)


def create_app_container() -> AppContainer:
    container = AppContainer()
    container.validate_bindings()
    return container
