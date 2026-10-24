"""Helpers for building standardized HTTP contract responses."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from common.http_contracts import coerce_collection_result, coerce_cursor_result, coerce_page_result
from exceptions.exception import SystemException
from utils.response_util import ResponseUtil


def ok_collection_result(result: Any):
    collection = coerce_collection_result(result)
    return ResponseUtil.ok_collection(items=collection.items)


def ok_page_result(result: Any):
    page = coerce_page_result(result)
    return ResponseUtil.ok_page(items=page.items, total=page.total, page=page.page, page_size=page.page_size)


def ok_cursor_result(result: Any):
    page = coerce_cursor_result(result)
    return ResponseUtil.ok_cursor(items=page.items, page_size=page.page_size, next_cursor=page.next_cursor)


def extract_int_value(data: Mapping[str, Any] | None, *keys: str) -> int | None:
    for key in keys:
        value = data.get(key) if data else None
        if value in (None, ''):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def require_int_value(data: Mapping[str, Any] | None, *keys: str, contract_name: str) -> int:
    value = extract_int_value(data, *keys)
    if value is not None:
        return value
    expected_keys = ', '.join(keys)
    raise SystemException(
        developer_message=(
            f'Success contract violation: {contract_name} did not return a resource identifier. '
            f'Expected one of: {expected_keys}'
        )
    )


def import_summary_to_batch_contract(
    details: Sequence[Mapping[str, Any]] | None,
    *,
    item_id_keys: Sequence[str],
    data_keys: Sequence[str] = (),
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    normalized_results: list[dict[str, Any]] = []
    succeeded = 0
    failed = 0

    for item in details or []:
        success = item.get('status') == 'success'
        item_id = next((item.get(key) for key in item_id_keys if item.get(key) not in (None, '')), None)
        payload: dict[str, Any] = {
            'itemId': item_id,
            'success': success,
        }
        for key in item_id_keys:
            if item.get(key) not in (None, ''):
                payload[key] = item.get(key)
        for key in data_keys:
            if item.get(key) not in (None, ''):
                payload[key] = item.get(key)
        if success:
            succeeded += 1
        else:
            failed += 1
            payload['error'] = {
                'title': '导入失败',
                'detail': item.get('message') or '导入失败',
            }
        normalized_results.append(payload)

    return normalized_results, {
        'total': len(normalized_results),
        'succeeded': succeeded,
        'failed': failed,
    }
