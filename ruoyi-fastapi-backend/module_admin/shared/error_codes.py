"""
统一错误码体系

错误码分类：
- 200: 成功
- 4xxx: 客户端错误
- 5xxx: 业务错误
- 9xxx: 系统错误
"""

from enum import IntEnum
from exceptions.exception import ServiceException


class ErrorCode(IntEnum):
    """统一错误码枚举"""

    # ==================== 成功 ====================
    SUCCESS = 200

    # ==================== 客户端错误 4xxx ====================
    BAD_REQUEST = 4000  # 请求参数错误
    UNAUTHORIZED = 4001  # 未认证
    TOKEN_EXPIRED = 4002  # Token过期
    FORBIDDEN = 4003  # 无权限
    NOT_FOUND = 4004  # 资源不存在
    METHOD_NOT_ALLOWED = 4005  # 方法不允许
    VALIDATION_ERROR = 4022  # 参数校验失败
    TOO_MANY_REQUESTS = 4029  # 请求过于频繁

    # ==================== 用户相关 50xx ====================
    USER_NOT_FOUND = 5001  # 用户不存在
    USER_ALREADY_EXISTS = 5002  # 用户已存在
    INVALID_PASSWORD = 5003  # 密码错误
    USER_DISABLED = 5004  # 用户已禁用
    USER_DELETED = 5005  # 用户已删除
    INVALID_CAPTCHA = 5006  # 验证码错误
    CAPTCHA_EXPIRED = 5007  # 验证码过期
    PASSWORD_NOT_MATCH = 5008  # 两次密码不一致

    # ==================== 角色相关 51xx ====================
    ROLE_NOT_FOUND = 5101  # 角色不存在
    ROLE_ALREADY_EXISTS = 5102  # 角色已存在
    ROLE_HAS_USERS = 5103  # 角色已分配用户，无法删除
    ROLE_KEY_EXISTS = 5104  # 角色标识已存在

    # ==================== 部门相关 52xx ====================
    DEPT_NOT_FOUND = 5201  # 部门不存在
    DEPT_HAS_CHILDREN = 5202  # 部门存在子部门，无法删除
    DEPT_HAS_USERS = 5203  # 部门存在用户，无法删除

    # ==================== 菜单相关 53xx ====================
    MENU_NOT_FOUND = 5301  # 菜单不存在
    MENU_HAS_CHILDREN = 5302  # 菜单存在子菜单，无法删除
    MENU_ASSIGNED_TO_ROLE = 5303  # 菜单已分配给角色，无法删除

    # ==================== 文件相关 54xx ====================
    FILE_NOT_FOUND = 5401  # 文件不存在
    FILE_UPLOAD_FAILED = 5402  # 文件上传失败
    FILE_TYPE_NOT_ALLOWED = 5403  # 文件类型不允许
    FILE_SIZE_EXCEEDED = 5404  # 文件大小超限

    # ==================== 业务通用 55xx ====================
    DATA_NOT_FOUND = 5501  # 数据不存在
    DATA_ALREADY_EXISTS = 5502  # 数据已存在
    DATA_STATUS_ERROR = 5503  # 数据状态异常
    OPERATION_NOT_ALLOWED = 5504  # 操作不允许

    # ==================== 系统错误 9xxx ====================
    INTERNAL_ERROR = 9000  # 内部错误
    DATABASE_ERROR = 9001  # 数据库错误
    REDIS_ERROR = 9002  # Redis错误
    THIRD_PARTY_ERROR = 9003  # 第三方服务错误
    CONFIG_ERROR = 9004  # 配置错误


class BusinessException(ServiceException):
    """
    业务异常基类

    使用示例:
        raise BusinessException(ErrorCode.USER_NOT_FOUND, '用户不存在')
        raise UserNotFoundException(user_id=1)
    """

    def __init__(self, code: ErrorCode | int, message: str):
        resolved_code = code if isinstance(code, int) else code.value
        super().__init__(message=message, code=resolved_code)


# ==================== 用户相关异常 ====================

class UserNotFoundException(BusinessException):
    """用户不存在异常"""

    def __init__(self, user_id: int | str | None = None):
        message = f'用户不存在: {user_id}' if user_id else '用户不存在'
        super().__init__(ErrorCode.USER_NOT_FOUND, message)


class UserAlreadyExistsException(BusinessException):
    """用户已存在异常"""

    def __init__(self, user_name: str | None = None):
        message = f'用户已存在: {user_name}' if user_name else '用户已存在'
        super().__init__(ErrorCode.USER_ALREADY_EXISTS, message)


class InvalidPasswordException(BusinessException):
    """密码错误异常"""

    def __init__(self):
        super().__init__(ErrorCode.INVALID_PASSWORD, '密码错误')


class UserDisabledException(BusinessException):
    """用户已禁用异常"""

    def __init__(self, user_name: str | None = None):
        message = f'用户已禁用: {user_name}' if user_name else '用户已禁用'
        super().__init__(ErrorCode.USER_DISABLED, message)


# ==================== 通用异常 ====================

class DataNotFoundException(BusinessException):
    """数据不存在异常"""

    def __init__(self, entity: str = '数据', id: int | str | None = None):
        message = f'{entity}不存在: {id}' if id else f'{entity}不存在'
        super().__init__(ErrorCode.DATA_NOT_FOUND, message)


class DataAlreadyExistsException(BusinessException):
    """数据已存在异常"""

    def __init__(self, entity: str = '数据', name: str | None = None):
        message = f'{entity}已存在: {name}' if name else f'{entity}已存在'
        super().__init__(ErrorCode.DATA_ALREADY_EXISTS, message)


class OperationNotAllowedException(BusinessException):
    """操作不允许异常"""

    def __init__(self, message: str = '操作不允许'):
        super().__init__(ErrorCode.OPERATION_NOT_ALLOWED, message)


class ValidationException(BusinessException):
    """参数校验异常"""

    def __init__(self, message: str = '参数校验失败'):
        super().__init__(ErrorCode.VALIDATION_ERROR, message)
