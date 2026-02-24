"""
统一错误码定义
遵循双层消息设计：用户消息 + 开发者消息
"""
from enum import IntEnum
from typing import Dict


class ErrorCode(IntEnum):
    """统一错误码枚举（5位数字，分模块）"""
    
    # ==================== 系统级错误 (1xxxx) ====================
    VALIDATION_ERROR = 10001      # 参数校验失败
    REQUIRED_FIELD = 10002        # 必填字段缺失
    INVALID_FORMAT = 10003        # 格式不正确
    INVALID_VALUE = 10004         # 值不合法
    INVALID_INPUT = 10005         # 输入参数不合法
    
    # ==================== 认证授权错误 (2xxxx) ====================
    UNAUTHORIZED = 20001          # 未认证
    TOKEN_EXPIRED = 20002         # Token过期
    TOKEN_INVALID = 20003         # Token无效
    FORBIDDEN = 20004             # 无权限
    LOGIN_FAILED = 20005          # 登录失败
    
    # ==================== 业务错误 - 用户模块 (3xxxx) ====================
    USER_NOT_FOUND = 30001        # 用户不存在
    USER_ALREADY_EXISTS = 30002   # 用户已存在
    USER_DISABLED = 30003         # 用户已禁用
    PASSWORD_INCORRECT = 30004    # 密码错误
    USERNAME_INVALID = 30005      # 用户名不合法
    USER_NAME_ALREADY_EXISTS = 30006  # 用户名已存在
    USER_PHONE_ALREADY_EXISTS = 30007  # 手机号已存在
    USER_EMAIL_ALREADY_EXISTS = 30008  # 邮箱已存在
    ADMIN_USER_OPERATION_FORBIDDEN = 30009  # 不允许操作超级管理员
    DATA_SCOPE_PERMISSION_DENIED = 30010  # 数据权限不足
    INVALID_PASSWORD = 30011      # 无效密码
    
    # ==================== 业务错误 - 角色模块 (4xxxx) ====================
    ROLE_NOT_FOUND = 40001        # 角色不存在
    ROLE_ALREADY_EXISTS = 40002   # 角色已存在
    ROLE_IN_USE = 40003           # 角色正在使用中
    
    # ==================== 业务错误 - 菜单模块 (41xxx) ====================
    MENU_NOT_FOUND = 41001        # 菜单不存在
    MENU_HAS_CHILDREN = 41002     # 菜单存在子菜单
    
    # ==================== 业务错误 - 部门模块 (42xxx) ====================
    DEPT_NOT_FOUND = 42001        # 部门不存在
    DEPT_HAS_CHILDREN = 42002     # 部门存在子部门
    DEPT_HAS_USERS = 42003        # 部门存在用户
    
    # ==================== 业务错误 - 字典模块 (43xxx) ====================
    DICT_NOT_FOUND = 43001        # 字典不存在
    DICT_TYPE_EXISTS = 43002      # 字典类型已存在
    
    # ==================== 业务错误 - 参数配置模块 (431xx) ====================
    CONFIG_NOT_FOUND = 43101      # 参数配置不存在
    CONFIG_BUILTIN_CANNOT_DELETE = 43102  # 内置参数不能删除
    
    # ==================== 业务错误 - 项目模块 (44xxx) ====================
    PROJECT_NOT_FOUND = 44001     # 项目不存在
    PROJECT_NAME_EXISTS = 44002   # 项目名称已存在
    
    # ==================== 业务错误 - 协议模块 (45xxx) ====================
    PROTOCOL_NOT_FOUND = 45001    # 协议不存在
    PROTOCOL_NAME_EXISTS = 45002  # 协议名称已存在
    
    # ==================== 业务错误 - 代码生成模块 (46xxx) ====================
    CODEGEN_OVERWRITE_DISABLED = 46001  # 代码生成覆盖被禁用

    # ==================== 业务错误 - 通用资源模块 (47xxx) ====================
    RESOURCE_NOT_FOUND = 47001    # 资源不存在
    RESOURCE_CONFLICT = 47002     # 资源冲突
    DATA_NOT_FOUND = 47003        # 数据不存在
    DATA_ALREADY_EXISTS = 47004   # 数据已存在
    OPERATION_NOT_ALLOWED = 47005  # 操作不允许
    
    # ==================== 系统错误 (5xxxx) ====================
    SYSTEM_ERROR = 50000          # 系统未知错误
    DATABASE_ERROR = 50001        # 数据库异常
    EXTERNAL_SERVICE_ERROR = 50002  # 外部服务异常
    FILE_UPLOAD_ERROR = 50003     # 文件上传失败
    FILE_DOWNLOAD_ERROR = 50004   # 文件下载失败
    CACHE_ERROR = 50005           # 缓存异常


class ErrorType(str):
    """错误类型"""
    VALIDATION = "VALIDATION"          # 校验错误
    AUTHENTICATION = "AUTHENTICATION"  # 认证错误
    AUTHORIZATION = "AUTHORIZATION"    # 授权错误
    BUSINESS = "BUSINESS"              # 业务错误
    SYSTEM = "SYSTEM"                  # 系统错误


class ErrorCodeInfo:
    """错误码信息（RFC 7807 标准）"""
    
    def __init__(
        self,
        code: int,
        title: str,              # 简短错误标题（RFC 7807 title字段）
        detail: str,             # 详细错误描述（RFC 7807 detail字段）
        http_status: int,
        error_type: str,
        error_code_name: str
    ):
        self.code = code
        self.title = title
        self.detail = detail
        self.http_status = http_status
        self.error_type = error_type
        self.error_code_name = error_code_name


# 错误码映射表（双层消息）
ERROR_CODE_MAP: Dict[int, ErrorCodeInfo] = {
    # ==================== 系统级错误 ====================
    ErrorCode.VALIDATION_ERROR: ErrorCodeInfo(
        code=10001,
        title="参数校验失败",
        detail="请检查输入的信息是否正确",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="VALIDATION_ERROR"
    ),
    ErrorCode.REQUIRED_FIELD: ErrorCodeInfo(
        code=10002,
        title="必填字段缺失",
        detail="请填写所有必填字段",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="REQUIRED_FIELD"
    ),
    ErrorCode.INVALID_FORMAT: ErrorCodeInfo(
        code=10003,
        title="格式不正确",
        detail="请检查输入格式是否正确",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="INVALID_FORMAT"
    ),
    ErrorCode.INVALID_VALUE: ErrorCodeInfo(
        code=10004,
        title="值不合法",
        detail="输入的值不符合要求，请重新输入",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="INVALID_VALUE"
    ),
    ErrorCode.INVALID_INPUT: ErrorCodeInfo(
        code=10005,
        title="输入不合法",
        detail="请检查输入内容是否正确",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="INVALID_INPUT"
    ),
    
    # ==================== 认证授权错误 ====================
    ErrorCode.UNAUTHORIZED: ErrorCodeInfo(
        code=20001,
        title="未认证",
        detail="请先登录后再进行操作",
        http_status=401,
        error_type=ErrorType.AUTHENTICATION,
        error_code_name="UNAUTHORIZED"
    ),
    ErrorCode.TOKEN_EXPIRED: ErrorCodeInfo(
        code=20002,
        title="登录已过期",
        detail="您的登录已过期，请重新登录",
        http_status=401,
        error_type=ErrorType.AUTHENTICATION,
        error_code_name="TOKEN_EXPIRED"
    ),
    ErrorCode.TOKEN_INVALID: ErrorCodeInfo(
        code=20003,
        title="登录信息无效",
        detail="登录信息无效，请重新登录",
        http_status=401,
        error_type=ErrorType.AUTHENTICATION,
        error_code_name="TOKEN_INVALID"
    ),
    ErrorCode.FORBIDDEN: ErrorCodeInfo(
        code=20004,
        title="权限不足",
        detail="您没有权限执行此操作",
        http_status=403,
        error_type=ErrorType.AUTHORIZATION,
        error_code_name="FORBIDDEN"
    ),
    ErrorCode.LOGIN_FAILED: ErrorCodeInfo(
        code=20005,
        title="登录失败",
        detail="用户名或密码错误，请重试",
        http_status=401,
        error_type=ErrorType.AUTHENTICATION,
        error_code_name="LOGIN_FAILED"
    ),
    
    # ==================== 业务错误 - 用户模块 ====================
    ErrorCode.USER_NOT_FOUND: ErrorCodeInfo(
        code=30001,
        title="用户不存在",
        detail="未找到该用户，请确认用户信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_NOT_FOUND"
    ),
    ErrorCode.USER_ALREADY_EXISTS: ErrorCodeInfo(
        code=30002,
        title="用户已存在",
        detail="该用户名已被使用，请换一个试试",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_ALREADY_EXISTS"
    ),
    ErrorCode.USER_DISABLED: ErrorCodeInfo(
        code=30003,
        title="用户已禁用",
        detail="该用户已被禁用，无法登录",
        http_status=403,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_DISABLED"
    ),
    ErrorCode.PASSWORD_INCORRECT: ErrorCodeInfo(
        code=30004,
        title="密码错误",
        detail="密码不正确，请重新输入",
        http_status=401,
        error_type=ErrorType.AUTHENTICATION,
        error_code_name="PASSWORD_INCORRECT"
    ),
    ErrorCode.USERNAME_INVALID: ErrorCodeInfo(
        code=30005,
        title="用户名格式不正确",
        detail="用户名格式不符合要求，请重新输入",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="USERNAME_INVALID"
    ),
    ErrorCode.USER_NAME_ALREADY_EXISTS: ErrorCodeInfo(
        code=30006,
        title="用户名已存在",
        detail="该用户名已被使用，请更换后重试",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_NAME_ALREADY_EXISTS"
    ),
    ErrorCode.USER_PHONE_ALREADY_EXISTS: ErrorCodeInfo(
        code=30007,
        title="手机号已存在",
        detail="该手机号已被使用，请更换后重试",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_PHONE_ALREADY_EXISTS"
    ),
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: ErrorCodeInfo(
        code=30008,
        title="邮箱已存在",
        detail="该邮箱已被使用，请更换后重试",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_EMAIL_ALREADY_EXISTS"
    ),
    ErrorCode.ADMIN_USER_OPERATION_FORBIDDEN: ErrorCodeInfo(
        code=30009,
        title="不允许操作超级管理员",
        detail="超级管理员账号受保护，当前操作被拒绝",
        http_status=403,
        error_type=ErrorType.AUTHORIZATION,
        error_code_name="ADMIN_USER_OPERATION_FORBIDDEN"
    ),
    ErrorCode.DATA_SCOPE_PERMISSION_DENIED: ErrorCodeInfo(
        code=30010,
        title="数据权限不足",
        detail="当前账号无权访问该数据",
        http_status=403,
        error_type=ErrorType.AUTHORIZATION,
        error_code_name="DATA_SCOPE_PERMISSION_DENIED"
    ),
    ErrorCode.INVALID_PASSWORD: ErrorCodeInfo(
        code=30011,
        title="密码不符合要求",
        detail="请检查密码格式后重试",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="INVALID_PASSWORD"
    ),
    
    # ==================== 业务错误 - 角色模块 ====================
    ErrorCode.ROLE_NOT_FOUND: ErrorCodeInfo(
        code=40001,
        title="角色不存在",
        detail="未找到该角色，请确认角色信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="ROLE_NOT_FOUND"
    ),
    ErrorCode.ROLE_ALREADY_EXISTS: ErrorCodeInfo(
        code=40002,
        title="角色已存在",
        detail="该角色名称已存在，请使用其他名称",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="ROLE_ALREADY_EXISTS"
    ),
    ErrorCode.ROLE_IN_USE: ErrorCodeInfo(
        code=40003,
        title="角色正在使用",
        detail="该角色正在使用中，无法删除",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="ROLE_IN_USE"
    ),
    
    # ==================== 业务错误 - 菜单模块 ====================
    ErrorCode.MENU_NOT_FOUND: ErrorCodeInfo(
        code=41001,
        title="菜单不存在",
        detail="未找到该菜单，请确认菜单信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="MENU_NOT_FOUND"
    ),
    ErrorCode.MENU_HAS_CHILDREN: ErrorCodeInfo(
        code=41002,
        title="菜单存在子菜单",
        detail="该菜单存在子菜单，请先删除子菜单",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="MENU_HAS_CHILDREN"
    ),
    
    # ==================== 业务错误 - 部门模块 ====================
    ErrorCode.DEPT_NOT_FOUND: ErrorCodeInfo(
        code=42001,
        title="部门不存在",
        detail="未找到该部门，请确认部门信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="DEPT_NOT_FOUND"
    ),
    ErrorCode.DEPT_HAS_CHILDREN: ErrorCodeInfo(
        code=42002,
        title="部门存在子部门",
        detail="该部门存在子部门，请先删除子部门",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="DEPT_HAS_CHILDREN"
    ),
    ErrorCode.DEPT_HAS_USERS: ErrorCodeInfo(
        code=42003,
        title="部门存在用户",
        detail="该部门存在用户，请先移除用户",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="DEPT_HAS_USERS"
    ),
    
    # ==================== 业务错误 - 字典模块 ====================
    ErrorCode.DICT_NOT_FOUND: ErrorCodeInfo(
        code=43001,
        title="字典不存在",
        detail="未找到该字典，请确认字典信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="DICT_NOT_FOUND"
    ),
    ErrorCode.DICT_TYPE_EXISTS: ErrorCodeInfo(
        code=43002,
        title="字典类型已存在",
        detail="该字典类型已存在，请使用其他类型",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="DICT_TYPE_EXISTS"
    ),
    
    # ==================== 业务错误 - 参数配置模块 ====================
    ErrorCode.CONFIG_NOT_FOUND: ErrorCodeInfo(
        code=43101,
        title="参数配置不存在",
        detail="未找到该参数配置，请确认配置信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="CONFIG_NOT_FOUND"
    ),
    ErrorCode.CONFIG_BUILTIN_CANNOT_DELETE: ErrorCodeInfo(
        code=43102,
        title="内置参数不能删除",
        detail="系统内置参数不允许删除",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="CONFIG_BUILTIN_CANNOT_DELETE"
    ),
    
    # ==================== 业务错误 - 项目模块 ====================
    ErrorCode.PROJECT_NOT_FOUND: ErrorCodeInfo(
        code=44001,
        title="项目不存在",
        detail="未找到该项目，请确认项目信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="PROJECT_NOT_FOUND"
    ),
    ErrorCode.PROJECT_NAME_EXISTS: ErrorCodeInfo(
        code=44002,
        title="项目名称已存在",
        detail="该项目名称已存在，请使用其他名称",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="PROJECT_NAME_EXISTS"
    ),
    
    # ==================== 业务错误 - 协议模块 ====================
    ErrorCode.PROTOCOL_NOT_FOUND: ErrorCodeInfo(
        code=45001,
        title="协议不存在",
        detail="未找到该协议，请确认协议信息",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="PROTOCOL_NOT_FOUND"
    ),
    ErrorCode.PROTOCOL_NAME_EXISTS: ErrorCodeInfo(
        code=45002,
        title="协议名称已存在",
        detail="该协议名称已存在，请使用其他名称",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="PROTOCOL_NAME_EXISTS"
    ),
    
    # ==================== 业务错误 - 代码生成模块 ====================
    ErrorCode.CODEGEN_OVERWRITE_DISABLED: ErrorCodeInfo(
        code=46001,
        title="代码生成失败",
        detail="系统配置不允许覆盖本地文件",
        http_status=403,
        error_type=ErrorType.BUSINESS,
        error_code_name="CODEGEN_OVERWRITE_DISABLED"
    ),
    ErrorCode.RESOURCE_NOT_FOUND: ErrorCodeInfo(
        code=47001,
        title="资源不存在",
        detail="请求的资源不存在，请确认后重试",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="RESOURCE_NOT_FOUND"
    ),
    ErrorCode.RESOURCE_CONFLICT: ErrorCodeInfo(
        code=47002,
        title="资源冲突",
        detail="请求与当前资源状态冲突",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="RESOURCE_CONFLICT"
    ),
    ErrorCode.DATA_NOT_FOUND: ErrorCodeInfo(
        code=47003,
        title="数据不存在",
        detail="未查询到对应数据，请确认后重试",
        http_status=404,
        error_type=ErrorType.BUSINESS,
        error_code_name="DATA_NOT_FOUND"
    ),
    ErrorCode.DATA_ALREADY_EXISTS: ErrorCodeInfo(
        code=47004,
        title="数据已存在",
        detail="数据已存在，请勿重复创建",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="DATA_ALREADY_EXISTS"
    ),
    ErrorCode.OPERATION_NOT_ALLOWED: ErrorCodeInfo(
        code=47005,
        title="操作不允许",
        detail="当前状态下不允许执行该操作",
        http_status=403,
        error_type=ErrorType.BUSINESS,
        error_code_name="OPERATION_NOT_ALLOWED"
    ),
    
    # ==================== 系统错误 ====================
    ErrorCode.SYSTEM_ERROR: ErrorCodeInfo(
        code=50000,
        title="系统繁忙，请稍后重试",
        detail="系统繁忙，请稍后重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="SYSTEM_ERROR"
    ),
    ErrorCode.DATABASE_ERROR: ErrorCodeInfo(
        code=50001,
        title="系统繁忙，请稍后重试",
        detail="系统繁忙，请稍后重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="DATABASE_ERROR"
    ),
    ErrorCode.EXTERNAL_SERVICE_ERROR: ErrorCodeInfo(
        code=50002,
        title="系统繁忙，请稍后重试",
        detail="系统繁忙，请稍后重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="EXTERNAL_SERVICE_ERROR"
    ),
    ErrorCode.FILE_UPLOAD_ERROR: ErrorCodeInfo(
        code=50003,
        title="文件上传失败",
        detail="文件上传失败，请重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="FILE_UPLOAD_ERROR"
    ),
    ErrorCode.FILE_DOWNLOAD_ERROR: ErrorCodeInfo(
        code=50004,
        title="文件下载失败",
        detail="文件下载失败，请重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="FILE_DOWNLOAD_ERROR"
    ),
    ErrorCode.CACHE_ERROR: ErrorCodeInfo(
        code=50005,
        title="系统繁忙，请稍后重试",
        detail="系统繁忙，请稍后重试",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="CACHE_ERROR"
    ),
}


def get_error_info(code: int) -> ErrorCodeInfo:
    """获取错误码信息"""
    return ERROR_CODE_MAP.get(code, ERROR_CODE_MAP[ErrorCode.SYSTEM_ERROR])
