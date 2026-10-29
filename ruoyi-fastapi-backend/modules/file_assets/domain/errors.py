"""Stable RFC 9457 problem types for file assets; reason codes never echo file content or storage errors."""

from __future__ import annotations

from config.error_codes import ErrorCode, ErrorType
from exceptions.exception import AppException


class FileAssetError(AppException):
    http_status_code = 422
    error_code_value = ErrorCode.FILE_ASSET_INVALID
    problem_slug = 'file-asset-invalid'
    error_type_value = ErrorType.VALIDATION
    default_message = '文件内容不合法'

    def __init__(
        self,
        reason: str,
        user_message: str | None = None,
        *,
        developer_message: str | None = None,
        field: str | None = None,
        retry_after: int | None = None,
    ):
        self.reason = reason
        headers = {'Retry-After': str(retry_after)} if retry_after is not None else None
        super().__init__(
            user_message=user_message or self.default_message,
            developer_message=developer_message or f'file asset rejected: {reason}',
            error_code=self.error_code_value,
            http_status=self.http_status_code,
            error_type=self.error_type_value,
            error_code_name=self.problem_slug,
            field=field,
            problem_extensions={'reasonCode': reason},
            headers=headers,
        )


class AssetNotFoundError(FileAssetError):
    http_status_code = 404
    error_code_value = ErrorCode.FILE_ASSET_NOT_FOUND
    problem_slug = 'file-asset-not-found'
    error_type_value = ErrorType.BUSINESS
    default_message = '文件不存在或无权访问'

    def __init__(self, reason: str = 'ASSET_NOT_FOUND', **kwargs):
        super().__init__(reason, **kwargs)


class AssetConflictError(FileAssetError):
    http_status_code = 409
    error_code_value = ErrorCode.FILE_ASSET_CONFLICT
    problem_slug = 'file-asset-conflict'
    error_type_value = ErrorType.BUSINESS
    default_message = '文件已被使用、已过期或状态已变化'


class AssetTooLargeError(FileAssetError):
    http_status_code = 413
    error_code_value = ErrorCode.FILE_ASSET_TOO_LARGE
    problem_slug = 'file-asset-too-large'
    default_message = '文件大小超出允许范围'


class AssetUnsupportedTypeError(FileAssetError):
    http_status_code = 415
    error_code_value = ErrorCode.FILE_ASSET_UNSUPPORTED_TYPE
    problem_slug = 'file-asset-unsupported-type'
    default_message = '文件类型不在允许范围内'


class AssetInvalidError(FileAssetError):
    pass


class AssetPermissionDeniedError(FileAssetError):
    http_status_code = 403
    error_code_value = ErrorCode.FORBIDDEN
    problem_slug = 'forbidden'
    error_type_value = ErrorType.AUTHORIZATION
    default_message = '没有上传或保存该文件的权限'

    def __init__(self, reason: str = 'PERMISSION_DENIED', **kwargs):
        super().__init__(reason, **kwargs)


class AssetQuotaExceededError(FileAssetError):
    http_status_code = 429
    error_code_value = ErrorCode.FILE_ASSET_QUOTA_EXCEEDED
    problem_slug = 'file-asset-quota-exceeded'
    error_type_value = ErrorType.BUSINESS
    default_message = '未保存的上传文件过多，请先保存或删除后再上传'


class AssetReceiveTimeoutError(FileAssetError):
    http_status_code = 408
    error_code_value = ErrorCode.FILE_ASSET_RECEIVE_TIMEOUT
    problem_slug = 'file-asset-receive-timeout'
    default_message = '上传接收超时，请重试'

    def __init__(self, reason: str = 'RECEIVE_TIMEOUT', **kwargs):
        super().__init__(reason, **kwargs)


class FileAssetsUnavailableError(FileAssetError):
    http_status_code = 503
    error_code_value = ErrorCode.FILE_ASSETS_UNAVAILABLE
    problem_slug = 'file-assets-unavailable'
    error_type_value = ErrorType.SYSTEM
    default_message = '文件服务暂不可用，请稍后重试'

    def __init__(self, reason: str = 'STORAGE_UNAVAILABLE', *, retry_after: int | None = 30, **kwargs):
        super().__init__(reason, retry_after=retry_after, **kwargs)
