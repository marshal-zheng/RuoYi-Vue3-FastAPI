"""FastAPI dependency helpers for container-resolved services."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from container.wiring import get_app_container


def service_provider(provider_name: str, *, require_session: bool = True):
    """Return a FastAPI dependency that resolves service from container."""

    if require_session:

        def _provider(
            request: Request,
            query_db: AsyncSession = Depends(get_db),
        ):
            container = get_app_container(request)
            return container.resolve_service(provider_name, query_db)

        return _provider

    def _provider(request: Request):
        container = get_app_container(request)
        return container.resolve_service(provider_name, None)

    return _provider
