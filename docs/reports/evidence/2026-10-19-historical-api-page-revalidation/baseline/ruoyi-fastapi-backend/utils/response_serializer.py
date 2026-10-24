from typing import Any, Mapping

from pydantic import BaseModel

from utils.common_util import CamelCaseUtil


def _camelize_key(key: Any) -> Any:
    if isinstance(key, str):
        return CamelCaseUtil.snake_to_camel(key)
    return key


def serialize_for_response(value: Any) -> Any:
    """
    统一响应序列化出口：
    - BaseModel -> camelCase dict
    - Mapping/List/Tuple/Set -> 递归 camelCase
    - 其他类型原样返回
    """
    if value is None:
        return None

    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, mode="json")

    if isinstance(value, Mapping):
        return {
            _camelize_key(k): serialize_for_response(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [serialize_for_response(item) for item in value]

    return value
