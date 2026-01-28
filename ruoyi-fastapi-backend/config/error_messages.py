"""
双层消息定义
- 用户消息：简洁、友好、可操作
- 开发者消息：详细技术信息
"""
from typing import Dict


# ==================== 用户消息（中文）：简洁、友好、可操作 ====================
USER_MESSAGES_ZH: Dict[int, str] = {
    # 系统级错误
    10001: "参数校验失败",
    10002: "必填字段缺失",
    10003: "格式不正确",
    10004: "值不合法",
    
    # 认证授权错误
    20001: "未认证，请先登录",
    20002: "登录已过期，请重新登录",
    20003: "登录信息无效，请重新登录",
    20004: "权限不足，无法执行此操作",
    20005: "用户名或密码错误",
    
    # 业务错误 - 用户模块
    30001: "用户不存在",
    30002: "该用户名已被使用，请换一个试试",
    30003: "该用户已被禁用",
    30004: "密码错误",
    30005: "用户名格式不正确",
    
    # 业务错误 - 角色模块
    40001: "角色不存在",
    40002: "该角色已存在",
    40003: "该角色正在使用中，无法删除",
    
    # 业务错误 - 菜单模块
    41001: "菜单不存在",
    41002: "该菜单存在子菜单，无法删除",
    
    # 业务错误 - 部门模块
    42001: "部门不存在",
    42002: "该部门存在子部门，无法删除",
    42003: "该部门存在用户，无法删除",
    
    # 业务错误 - 字典模块
    43001: "字典不存在",
    43002: "该字典类型已存在",
    
    # 业务错误 - 项目模块
    44001: "项目不存在",
    44002: "该项目名称已存在",
    
    # 业务错误 - 协议模块
    45001: "协议不存在",
    45002: "该协议名称已存在",
    
    # 系统错误：通用化，不暴露技术细节
    50000: "系统繁忙，请稍后重试",
    50001: "系统繁忙，请稍后重试",  # 数据库错误
    50002: "系统繁忙，请稍后重试",  # 外部服务错误
    50003: "文件上传失败，请重试",
    50004: "文件下载失败，请重试",
    50005: "系统繁忙，请稍后重试",  # 缓存错误
}


# ==================== 用户消息（英文）：简洁、友好、可操作 ====================
USER_MESSAGES_EN: Dict[int, str] = {
    # 系统级错误
    10001: "Validation failed",
    10002: "Required field missing",
    10003: "Invalid format",
    10004: "Invalid value",
    
    # 认证授权错误
    20001: "Unauthorized, please login",
    20002: "Session expired, please login again",
    20003: "Invalid session, please login again",
    20004: "Permission denied",
    20005: "Invalid username or password",
    
    # 业务错误 - 用户模块
    30001: "User not found",
    30002: "Username already exists, please try another one",
    30003: "User is disabled",
    30004: "Incorrect password",
    30005: "Invalid username format",
    
    # 业务错误 - 角色模块
    40001: "Role not found",
    40002: "Role already exists",
    40003: "Role is in use and cannot be deleted",
    
    # 业务错误 - 菜单模块
    41001: "Menu not found",
    41002: "Menu has children and cannot be deleted",
    
    # 业务错误 - 部门模块
    42001: "Department not found",
    42002: "Department has children and cannot be deleted",
    42003: "Department has users and cannot be deleted",
    
    # 业务错误 - 字典模块
    43001: "Dictionary not found",
    43002: "Dictionary type already exists",
    
    # 业务错误 - 项目模块
    44001: "Project not found",
    44002: "Project name already exists",
    
    # 业务错误 - 协议模块
    45001: "Protocol not found",
    45002: "Protocol name already exists",
    
    # 系统错误：通用化
    50000: "System is busy, please try again later",
    50001: "System is busy, please try again later",
    50002: "System is busy, please try again later",
    50003: "File upload failed, please try again",
    50004: "File download failed, please try again",
    50005: "System is busy, please try again later",
}


# ==================== 开发者消息：详细技术信息（仅用于日志和开发环境）====================
DEVELOPER_MESSAGES: Dict[int, str] = {
    # 系统级错误：与用户消息相同或略详细
    10001: "Request parameter validation failed",
    10002: "Required field missing: {field}",
    10003: "Invalid format for field: {field}",
    10004: "Invalid value for field: {field}, value={value}",
    
    # 认证授权错误
    20001: "Authentication token missing or invalid",
    20002: "Authentication token expired at {expired_at}",
    20003: "Authentication token is invalid: {reason}",
    20004: "User does not have permission to access: {resource}",
    20005: "Login failed for user: {username}",
    
    # 业务错误 - 用户模块
    30001: "User with id={user_id} not found in database",
    30002: "User with username='{username}' already exists in database",
    30003: "User with id={user_id} is disabled, status={status}",
    30004: "Password verification failed for user: {username}",
    30005: "Username '{username}' does not match required pattern",
    
    # 业务错误 - 角色模块
    40001: "Role with id={role_id} not found in database",
    40002: "Role with name='{role_name}' already exists in database",
    40003: "Role with id={role_id} is assigned to {user_count} users",
    
    # 业务错误 - 菜单模块
    41001: "Menu with id={menu_id} not found in database",
    41002: "Menu with id={menu_id} has {children_count} children",
    
    # 业务错误 - 部门模块
    42001: "Department with id={dept_id} not found in database",
    42002: "Department with id={dept_id} has {children_count} children",
    42003: "Department with id={dept_id} has {user_count} users",
    
    # 业务错误 - 字典模块
    43001: "Dictionary with type='{dict_type}' not found in database",
    43002: "Dictionary with type='{dict_type}' already exists in database",
    
    # 业务错误 - 项目模块
    44001: "Project with id={project_id} not found in database",
    44002: "Project with name='{project_name}' already exists in database",
    
    # 业务错误 - 协议模块
    45001: "Protocol with id={protocol_id} not found in database",
    45002: "Protocol with name='{protocol_name}' already exists in database",
    
    # 系统错误：详细技术原因
    50000: "Internal server error: {error_detail}",
    50001: "Database operation failed: {error_detail}",
    50002: "External service call failed: service={service_name}, error={error_detail}",
    50003: "File upload failed: {error_detail}",
    50004: "File download failed: {error_detail}",
    50005: "Cache operation failed: {error_detail}",
}


def get_user_message(code: int, lang: str = "zh", **kwargs) -> str:
    """
    获取用户消息（前端展示）
    
    Args:
        code: 错误码
        lang: 语言（zh/en）
        **kwargs: 模板变量
        
    Returns:
        用户友好的错误消息
    """
    messages = USER_MESSAGES_ZH if lang == "zh" else USER_MESSAGES_EN
    template = messages.get(code, messages.get(50000))
    
    # 用户消息通常不需要变量替换（已经通用化）
    # 但保留此功能以支持特殊场景
    try:
        return template.format(**kwargs) if kwargs else template
    except KeyError:
        return template


def get_developer_message(code: int, **kwargs) -> str:
    """
    获取开发者消息（日志记录和开发环境）
    
    Args:
        code: 错误码
        **kwargs: 模板变量
        
    Returns:
        详细的技术错误消息
    """
    template = DEVELOPER_MESSAGES.get(code, DEVELOPER_MESSAGES.get(50000))
    
    try:
        return template.format(**kwargs) if kwargs else template
    except KeyError:
        # 如果变量缺失，返回原始模板
        return template
