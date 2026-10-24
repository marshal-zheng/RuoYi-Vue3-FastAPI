"""Helpers for command result payload boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_BANNED_SUCCESS_MESSAGE_KEYS = {'message', 'msg'}


def command_result_data(service_result: Any) -> dict[str, Any]:
    """Extract non-message business data from a service result."""
    raw_result = getattr(service_result, 'result', None)
    if raw_result is None:
        return {}
    if isinstance(raw_result, Mapping):
        return {key: value for key, value in raw_result.items() if key not in _BANNED_SUCCESS_MESSAGE_KEYS}
    if hasattr(raw_result, 'model_dump'):
        dumped = raw_result.model_dump(by_alias=True, exclude_none=True)
        return {key: value for key, value in dumped.items() if key not in _BANNED_SUCCESS_MESSAGE_KEYS}
    return {}
