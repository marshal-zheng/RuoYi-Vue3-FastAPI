"""HTTP response factory aligned with message governance contracts."""

from __future__ import annotations

from typing import Any, Mapping, Sequence
from urllib.parse import urljoin

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.background import BackgroundTask

from common.http_contracts import (
    coerce_collection_result,
    coerce_cursor_result,
    coerce_page_result,
    sanitize_batch_results,
)
from config.env import ErrorHandlingConfig
from middlewares.trace_middleware import get_request_id, get_trace_id
from utils.response_serializer import serialize_for_response


def _header_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_headers(headers: Mapping[str, str] | None = None) -> dict[str, str]:
    response_headers: dict[str, str] = {}
    request_id = _header_value(get_request_id())
    trace_id = _header_value(get_trace_id())
    if request_id:
        response_headers['X-Request-Id'] = request_id
    if trace_id:
        response_headers['X-Trace-Id'] = trace_id
    if headers:
        response_headers.update({str(key): str(value) for key, value in headers.items()})
    return response_headers


def _ensure_absolute_location(location: str) -> str:
    candidate = str(location or '').strip()
    if not candidate:
        raise ValueError('Location header must not be empty')
    if candidate.startswith('http://') or candidate.startswith('https://'):
        return candidate
    raise ValueError(f'Location must be an absolute URL, got: {candidate}')


def _problem_type_url(type_slug: str | None) -> str:
    if not type_slug:
        return 'about:blank'
    slug = str(type_slug).strip().strip('/')
    if not slug:
        return 'about:blank'
    base_url = str(ErrorHandlingConfig.problem_type_base_url or '').strip().rstrip('/')
    if not base_url:
        return 'about:blank'
    return f'{base_url}/{slug}'


def _problem_headers(headers: Mapping[str, str] | None = None) -> dict[str, str]:
    response_headers = _normalize_headers(headers)
    response_headers['Content-Type'] = 'application/problem+json'
    return response_headers


class ResponseUtil:
    """Explicit response factory for resource-oriented success and RFC 9457 errors."""

    @classmethod
    def ok_resource(cls, resource: Any, *, headers: Mapping[str, str] | None = None) -> JSONResponse:
        if isinstance(resource, (list, tuple, set)):
            collection = coerce_collection_result(resource)
            return cls.ok_collection(items=collection.items, headers=headers)

        serialized = serialize_for_response(resource)
        if isinstance(serialized, Mapping):
            if 'results' in serialized and 'summary' in serialized:
                return cls.batch_result(
                    results=serialized.get('results') or [],
                    summary=serialized.get('summary') or {},
                    headers=headers,
                )
            if 'nextCursor' in serialized:
                cursor = coerce_cursor_result(serialized)
                return cls.ok_cursor(
                    items=cursor.items,
                    page_size=cursor.page_size,
                    next_cursor=cursor.next_cursor,
                    headers=headers,
                )
            if 'total' in serialized and 'items' in serialized:
                page = coerce_page_result(serialized)
                return cls.ok_page(
                    items=page.items,
                    total=page.total,
                    page=page.page,
                    page_size=page.page_size,
                    headers=headers,
                )
            if 'items' in serialized and 'total' not in serialized:
                collection = coerce_collection_result(serialized)
                return cls.ok_collection(items=collection.items, headers=headers)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(serialized),
            headers=_normalize_headers(headers),
        )

    @classmethod
    def ok_collection(
        cls,
        *,
        items: Sequence[Any],
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        payload = {'items': serialize_for_response(list(items))}
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(payload),
            headers=_normalize_headers(headers),
        )

    @classmethod
    def ok_page(
        cls,
        *,
        items: Sequence[Any],
        total: int,
        page: int,
        page_size: int,
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        payload = {
            'items': serialize_for_response(list(items)),
            'total': int(total),
            'page': int(page),
            'pageSize': int(page_size),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(payload),
            headers=_normalize_headers(headers),
        )

    @classmethod
    def ok_cursor(
        cls,
        *,
        items: Sequence[Any],
        page_size: int,
        next_cursor: str | None,
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        payload = {
            'items': serialize_for_response(list(items)),
            'pageSize': int(page_size),
            'nextCursor': next_cursor,
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(payload),
            headers=_normalize_headers(headers),
        )

    @classmethod
    def created_resource(
        cls,
        resource: Any,
        *,
        location: str,
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        response_headers = _normalize_headers(headers)
        response_headers['Location'] = _ensure_absolute_location(location)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder(serialize_for_response(resource)),
            headers=response_headers,
        )

    @classmethod
    def accepted_job(
        cls,
        job: Mapping[str, Any] | Any,
        *,
        location: str,
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        response_headers = _normalize_headers(headers)
        response_headers['Location'] = _ensure_absolute_location(location)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=jsonable_encoder(serialize_for_response(job)),
            headers=response_headers,
        )

    @classmethod
    def batch_result(
        cls,
        *,
        results: Sequence[Mapping[str, Any]] | Sequence[Any],
        summary: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        payload = {
            'results': sanitize_batch_results(results),
            'summary': serialize_for_response(summary),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(payload),
            headers=_normalize_headers(headers),
        )

    @classmethod
    def no_content(cls, *, headers: Mapping[str, str] | None = None) -> Response:
        return Response(status_code=status.HTTP_204_NO_CONTENT, headers=_normalize_headers(headers))

    @classmethod
    def problem_details(
        cls,
        *,
        request: Request,
        http_status: int,
        title: str,
        detail: str | None = None,
        type_slug: str | None = None,
        error_code: int | str | None = None,
        errors: Sequence[Mapping[str, Any]] | None = None,
        headers: Mapping[str, str] | None = None,
        extensions: Mapping[str, Any] | None = None,
    ) -> JSONResponse:
        payload: dict[str, Any] = {
            'type': _problem_type_url(type_slug),
            'title': title,
            'status': int(http_status),
            'detail': detail or title,
            'instance': str(request.url.path),
        }
        request_id = _header_value(get_request_id())
        trace_id = _header_value(get_trace_id())
        if error_code is not None:
            payload['errorCode'] = error_code
        if request_id:
            payload['requestId'] = request_id
        if trace_id:
            payload['traceId'] = trace_id
        if extensions:
            payload.update({key: value for key, value in extensions.items() if key not in payload})
        if errors:
            payload['errors'] = serialize_for_response(list(errors))
        return JSONResponse(
            status_code=int(http_status),
            content=jsonable_encoder(payload),
            headers=_problem_headers(headers),
        )

    @classmethod
    def validation_problem(
        cls,
        *,
        request: Request,
        errors: Sequence[Mapping[str, Any]],
        title: str = '参数验证失败',
        detail: str = '请检查输入字段',
        error_code: int | str | None = 10001,
        type_slug: str | None = 'validation-error',
        headers: Mapping[str, str] | None = None,
    ) -> JSONResponse:
        normalized_errors = []
        for item in errors:
            normalized_errors.append(
                {
                    'field': item.get('field', 'unknown'),
                    'message': item.get('message', 'Validation failed'),
                    'code': item.get('code'),
                }
            )
        return cls.problem_details(
            request=request,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title=title,
            detail=detail,
            type_slug=type_slug,
            error_code=error_code,
            errors=normalized_errors,
            headers=headers,
        )

    @classmethod
    def streaming(
        cls,
        *,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        return StreamingResponse(
            status_code=status.HTTP_200_OK,
            content=data,
            headers=_normalize_headers(headers),
            media_type=media_type,
            background=background,
        )

    @staticmethod
    def build_absolute_location(request: Request, path: str) -> str:
        """Build an absolute location URL from the current request."""
        candidate = str(path or '').strip()
        if candidate.startswith('http://') or candidate.startswith('https://'):
            return candidate
        base_url = str(request.base_url)
        return urljoin(base_url, candidate.lstrip('/'))
