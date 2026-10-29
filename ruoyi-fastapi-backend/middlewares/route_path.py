"""Route-relative request path for ASGI middlewares.

Since uvicorn 0.26, `scope['path']` includes `root_path` (e.g. `/dev-api`, `/prod-api`), while routes and
configured prefixes are root-relative. Middlewares must match against the same path routing uses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import Scope


def route_path(scope: Scope) -> str:
    path = str(scope.get('path', ''))
    root_path = str(scope.get('root_path', '') or '').rstrip('/')
    if root_path and (path == root_path or path.startswith(f'{root_path}/')):
        return path[len(root_path) :] or '/'
    return path
