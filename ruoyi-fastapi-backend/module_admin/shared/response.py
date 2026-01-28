"""
统一响应模型

命名规范：
- 请求模型: XxxRequest (如 UserQueryRequest, UserCreateRequest)
- 响应模型: XxxResponse (如 UserResponse, UserListResponse)
- 实体模型: Xxx (如 User, Role, Dept)
- 分页响应: PageResponse[T]
- API响应: ApiResponse[T]
"""

from typing import Generic, TypeVar, Any
from pydantic import Field
from module_admin.entity.vo.base import CamelModelBase

T = TypeVar('T')


class ApiResponse(CamelModelBase, Generic[T]):
    """
    统一API响应结构

    使用示例:
        ApiResponse[UserResponse](code=200, msg='success', data=user)
        ApiResponse[list[UserResponse]](code=200, msg='success', data=users)
    """

    code: int = Field(default=200, description='响应状态码')
    msg: str = Field(default='success', description='响应消息')
    data: T | None = Field(default=None, description='响应数据')


class PageResponse(CamelModelBase, Generic[T]):
    """
    分页响应结构

    使用示例:
        PageResponse[UserResponse](rows=users, total=100)
    """

    rows: list[T] = Field(default_factory=list, description='数据列表')
    total: int = Field(default=0, description='总记录数')
    code: int = Field(default=200, description='响应状态码')
    msg: str = Field(default='success', description='响应消息')


class SuccessResponse(ApiResponse[Any]):
    """
    成功响应快捷类

    使用示例:
        return SuccessResponse(msg='操作成功')
    """

    code: int = Field(default=200, description='响应状态码')
    msg: str = Field(default='操作成功', description='响应消息')


class ErrorResponse(ApiResponse[None]):
    """
    错误响应快捷类

    使用示例:
        return ErrorResponse(code=500, msg='操作失败')
    """

    code: int = Field(default=500, description='响应状态码')
    msg: str = Field(default='操作失败', description='响应消息')
    data: None = Field(default=None, description='响应数据')


# ============================================================
# Pydantic 模型命名规范
# ============================================================
#
# 1. 请求模型 (Request)
#    - 查询请求: XxxQueryRequest (如 UserQueryRequest)
#    - 分页查询: XxxPageQueryRequest (如 UserPageQueryRequest)
#    - 创建请求: XxxCreateRequest (如 UserCreateRequest)
#    - 更新请求: XxxUpdateRequest (如 UserUpdateRequest)
#    - 删除请求: XxxDeleteRequest (如 UserDeleteRequest)
#
# 2. 响应模型 (Response)
#    - 单体响应: XxxResponse (如 UserResponse)
#    - 列表响应: XxxListResponse (如 UserListResponse)
#    - 详情响应: XxxDetailResponse (如 UserDetailResponse)
#
# 3. 实体模型 (Entity)
#    - 基础实体: Xxx (如 User, Role, Dept)
#    - 关联实体: XxxYyy (如 UserRole, UserPost)
#
# 4. 泛型响应
#    - API响应: ApiResponse[T]
#    - 分页响应: PageResponse[T]
#
# 5. 命名转换
#    - Python 字段: snake_case (如 user_name, create_time)
#    - JSON 字段: camelCase (通过 alias_generator=to_camel)
#
# ============================================================
