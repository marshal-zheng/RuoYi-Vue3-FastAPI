"""Shared HTTP contract models and coercion helpers."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase
from utils.response_serializer import serialize_for_response


class CollectionResult(CamelModelBase):
    """HTTP collection result without pagination metadata."""

    items: list[Any] = Field(default_factory=list, description='Collection items')


class PagedResult(CamelModelBase):
    """HTTP offset pagination result."""

    items: list[Any] = Field(default_factory=list, description='Page items')
    total: int = Field(default=0, description='Total item count')
    page: int = Field(default=1, description='Current page number')
    page_size: int = Field(default=10, description='Current page size')


class CursorResult(CamelModelBase):
    """HTTP cursor pagination result."""

    items: list[Any] = Field(default_factory=list, description='Page items')
    page_size: int = Field(default=10, description='Current page size')
    next_cursor: str | None = Field(default=None, description='Next page cursor')


class BatchItemError(CamelModelBase):
    """Per-item batch error payload."""

    error_code: int | str | None = Field(default=None, description='Business error code')
    title: str | None = Field(default=None, description='Short error title')
    detail: str | None = Field(default=None, description='Detailed error message')


class BatchItemResult(CamelModelBase):
    """Per-item batch execution result."""

    success: bool = Field(description='Whether this item succeeded')
    item_id: str | int | None = Field(default=None, description='Item identifier')
    error: BatchItemError | None = Field(default=None, description='Per-item error details')


class AcceptedJobResult(CamelModelBase):
    """Accepted async job result."""

    job_id: str = Field(description='Accepted job id')
    status: str = Field(default='accepted', description='Accepted job status')
    status_url: str | None = Field(default=None, description='Absolute job status URL')


class ValidationErrorItem(CamelModelBase):
    """RFC 9457 validation error extension item."""

    field: str = Field(description='Invalid field path')
    message: str = Field(description='Validation failure message')
    code: str | None = Field(default=None, description='Validator error code')


class ProblemDetails(CamelModelBase):
    """RFC 9457 Problem Details payload."""

    type: str = Field(description='Problem type URI')
    title: str = Field(description='Short summary')
    status: int = Field(description='HTTP status')
    detail: str = Field(description='Detailed explanation')
    instance: str = Field(description='Problem instance path')
    error_code: int | str | None = Field(default=None, description='Business error code')
    request_id: str | None = Field(default=None, description='Request id')
    trace_id: str | None = Field(default=None, description='Trace id')
    errors: list[ValidationErrorItem] | None = Field(default=None, description='Validation errors')


def _read_attr(source: Any, *names: str) -> Any:
    for name in names:
        if isinstance(source, Mapping) and name in source:
            return source[name]
        if hasattr(source, name):
            return getattr(source, name)
    return None


def ensure_list_items(items: Any) -> list[Any]:
    """Normalize items into a JSON-serializable list."""
    if items is None:
        return []
    serialized = serialize_for_response(items)
    if isinstance(serialized, list):
        return serialized
    if isinstance(serialized, tuple):
        return list(serialized)
    if isinstance(serialized, set):
        return list(serialized)
    return [serialized]


def coerce_collection_result(source: Any) -> CollectionResult:
    """Coerce arbitrary query results into a collection result."""
    items = _read_attr(source, 'items')
    if items is None and isinstance(source, Sequence) and not isinstance(source, (str, bytes, bytearray)):
        items = list(source)
    return CollectionResult(items=ensure_list_items(items))


def coerce_page_result(source: Any) -> PagedResult:
    """Coerce arbitrary query results into an offset page result."""
    items = _read_attr(source, 'items')
    total = _read_attr(source, 'total') or 0
    page = _read_attr(source, 'page') or 1
    page_size = _read_attr(source, 'page_size', 'pageSize') or 10
    return PagedResult(
        items=ensure_list_items(items),
        total=int(total),
        page=int(page),
        page_size=int(page_size),
    )


def coerce_cursor_result(source: Any) -> CursorResult:
    """Coerce arbitrary query results into a cursor page result."""
    items = _read_attr(source, 'items')
    page_size = _read_attr(source, 'page_size', 'pageSize') or 10
    next_cursor = _read_attr(source, 'next_cursor', 'nextCursor')
    return CursorResult(items=ensure_list_items(items), page_size=int(page_size), next_cursor=next_cursor)


def sanitize_batch_results(results: Sequence[Mapping[str, Any]] | Sequence[Any]) -> list[dict[str, Any]]:
    """Freeze per-item batch result error shape to the approved whitelist."""
    sanitized: list[dict[str, Any]] = []
    for item in results:
        serialized = serialize_for_response(item)
        if not isinstance(serialized, Mapping):
            sanitized.append({'success': False, 'error': {'title': 'Invalid batch result', 'detail': str(serialized)}})
            continue
        normalized = dict(serialized)
        error = normalized.get('error')
        if isinstance(error, Mapping):
            normalized['error'] = {
                'errorCode': error.get('errorCode') or error.get('error_code'),
                'title': error.get('title'),
                'detail': error.get('detail'),
            }
        sanitized.append(normalized)
    return sanitized
