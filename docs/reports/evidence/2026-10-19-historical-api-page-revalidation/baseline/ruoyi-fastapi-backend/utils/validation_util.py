import inspect
import functools
from fastapi import status
from pydantic_validation_decorator import FieldValidationError, ValidateFields as _ValidateFields
from exceptions.exception import ValidationException


def ValidateFields(*args, **kwargs):
    """
    Wrap pydantic_validation_decorator.ValidateFields to raise ValidationException
    for validation errors, which will be handled by the global exception handler
    to return RFC 7807 format responses.
    """
    decorator = _ValidateFields(*args, **kwargs)

    def wrapper(func):
        validated_func = decorator(func)

        @functools.wraps(validated_func)
        async def inner(*inner_args, **inner_kwargs):
            try:
                result = validated_func(*inner_args, **inner_kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result
            except FieldValidationError as exc:
                # 抛出 ValidationException，由全局异常处理器处理
                # 添加 errors 字段以符合 RFC 7807 校验错误格式
                raise ValidationException(
                    user_message=exc.message,
                    developer_message=f"Field validation failed: {exc.message}",
                    field="unknown",
                    errors=[{
                        "field": "unknown",
                        "message": exc.message,
                        "code": "FIELD_VALIDATION_ERROR"
                    }]
                )

        return inner

    return wrapper
