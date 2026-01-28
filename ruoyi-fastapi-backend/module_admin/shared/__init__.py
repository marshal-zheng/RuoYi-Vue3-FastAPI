"""
共享模块入口
提供统一的响应类型、错误码、工具函数等
"""

from module_admin.shared.response import (
    ApiResponse,
    PageResponse,
    SuccessResponse,
    ErrorResponse,
)
from module_admin.shared.error_codes import ErrorCode, BusinessException

__all__ = [
    'ApiResponse',
    'PageResponse',
    'SuccessResponse',
    'ErrorResponse',
    'ErrorCode',
    'BusinessException',
]
