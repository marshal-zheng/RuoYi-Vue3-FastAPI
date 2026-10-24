"""Container lifecycle wiring for FastAPI application."""

from __future__ import annotations

from fastapi import Request

from container.app_container import AppContainer, create_app_container
from utils.log_util import logger


def build_container() -> AppContainer:
    """Build container at composition root."""
    return create_app_container()


def validate_container_bindings(container: AppContainer) -> None:
    """Validate provider bindings and fail fast on startup."""
    container.validate_bindings()
    logger.info('Container binding validation passed')


def attach_container(app, container: AppContainer) -> None:
    """Attach container to FastAPI app state."""
    app.state.container = container


def get_app_container(request: Request) -> AppContainer:
    """Resolve app container from request scope."""
    container = getattr(request.app.state, 'container', None)
    if container is None:
        raise RuntimeError('Application container is not initialized')
    if not isinstance(container, AppContainer):
        raise RuntimeError('Invalid container type in application state')
    return container


async def initialize_container_runtime(
    container: AppContainer,
    *,
    test_mode: bool,
    test_redis_client=None,
):
    """Initialize infrastructure providers for current runtime mode."""
    return await container.initialize_runtime(
        redis_client=test_redis_client,
        initialize_scheduler=not test_mode,
    )


async def shutdown_container_runtime(container: AppContainer) -> None:
    """Shutdown infrastructure providers."""
    await container.shutdown_runtime()
