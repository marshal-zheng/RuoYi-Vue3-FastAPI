# API 设计规范

## API 设计原则

### 1. RESTful 风格
- 使用标准 HTTP 方法 (GET, POST, PUT, DELETE)
- 资源导向的 URL 设计
- 统一的响应格式
- 合理的状态码使用

### 2. 统一响应格式
所有 API 返回统一的 JSON 格式:

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {}
}
```

### 3. 版本控制
通过 URL 路径进行版本控制:
- `/api/v1/system/user`
- `/api/v2/system/user`

## URL 设计规范

### 1. 路由前缀

```python
# 系统管理模块
router = APIRouter(prefix="/system/user", tags=["用户管理"])

# 业务模块
router = APIRouter(prefix="/business/project", tags=["项目管理"])

# 监控模块
router = APIRouter(prefix="/monitor/operlog", tags=["操作日志"])
```

### 2. 资源命名

- 使用名词复数形式
- 使用小写字母
- 多个单词用连字符分隔

```
✅ 正确:
/system/users
/system/user-roles
/business/projects

❌ 错误:
/system/getUsers
/system/UserRole
/business/project_list
```

### 3. HTTP 方法映射

| 方法 | 操作 | 示例 |
|------|------|------|
| GET | 查询 | `GET /system/user/list` - 查询列表<br>`GET /system/user/{id}` - 查询详情 |
| POST | 新增 | `POST /system/user` - 新增用户 |
| PUT | 修改 | `PUT /system/user` - 修改用户 |
| DELETE | 删除 | `DELETE /system/user/{id}` - 删除用户 |

## 请求设计

### 1. 查询参数 (Query Parameters)

用于列表查询、筛选、分页:

```python
class UserQueryModel(BaseModel):
    """用户查询模型"""
    user_name: Optional[str] = None
    phonenumber: Optional[str] = None
    status: Optional[str] = None
    dept_id: Optional[int] = None
    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    begin_time: Optional[str] = None
    end_time: Optional[str] = None

@router.get("/list")
async def get_user_list(
    query: UserQueryModel = Depends(),
    service: UserService = Depends()
):
    result = await service.get_user_list(query)
    return ResponseUtil.success(data=result)
```

### 2. 路径参数 (Path Parameters)

用于指定资源 ID:

```python
@router.get("/{user_id}")
async def get_user_detail(
    user_id: int = Path(..., description="用户ID"),
    service: UserService = Depends()
):
    user = await service.get_user_by_id(user_id)
    return ResponseUtil.success(data=user)
```

### 3. 请求体 (Request Body)

用于新增、修改操作:

```python
class UserModel(BaseModel):
    """用户模型"""
    user_id: Optional[int] = None
    user_name: str = Field(..., min_length=1, max_length=30, description="用户账号")
    nick_name: str = Field(..., min_length=1, max_length=30, description="用户昵称")
    email: Optional[str] = Field(None, max_length=50, description="邮箱")
    phonenumber: Optional[str] = Field(None, max_length=11, description="手机号")
    sex: Optional[str] = Field(None, description="性别")
    password: Optional[str] = Field(None, description="密码")
    status: str = Field(default="0", description="状态")
    dept_id: Optional[int] = Field(None, description="部门ID")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")

@router.post("")
async def add_user(
    user: UserModel,
    service: UserService = Depends()
):
    await service.add_user(user)
    return ResponseUtil.success(msg="新增成功")
```

## 响应设计

### 1. 成功响应

```python
from utils.response_util import ResponseUtil

# 成功响应(无数据)
return ResponseUtil.success(msg="操作成功")

# 成功响应(有数据)
return ResponseUtil.success(data={"user_id": 1, "user_name": "admin"})

# 成功响应(列表数据)
return ResponseUtil.success(data={
    "rows": [{"user_id": 1}, {"user_id": 2}],
    "total": 2
})
```

响应格式:
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "rows": [...],
    "total": 100
  }
}
```

### 2. 错误响应

```python
from exceptions.exception import ServiceException

# 业务异常
raise ServiceException(message="用户名已存在")

# 权限异常
raise PermissionException(message="无权限访问")

# 参数异常
raise ParamException(message="参数错误")
```

错误响应格式:
```json
{
  "code": 500,
  "msg": "用户名已存在",
  "data": null
}
```

### 3. 状态码规范

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 操作成功 |
| 400 | 参数错误 | 请求参数验证失败 |
| 401 | 未认证 | 未登录或 Token 失效 |
| 403 | 无权限 | 没有访问权限 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 500 | 服务器错误 | 业务异常或系统错误 |

## 完整 API 示例

### 用户管理 API

```python
from fastapi import APIRouter, Depends, Path, Query
from typing import List
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import UserQueryModel, UserModel
from module_admin.service.user_service import UserService
from utils.response_util import ResponseUtil

router = APIRouter(prefix="/system/user", tags=["用户管理"])

@router.get(
    "/list",
    summary="获取用户列表",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:list"))]
)
@Log(title="用户管理", business_type=1)
async def get_user_list(
    query: UserQueryModel = Depends(),
    service: UserService = Depends()
):
    """
    获取用户列表
    
    参数:
    - user_name: 用户名(模糊查询)
    - phonenumber: 手机号
    - status: 状态
    - dept_id: 部门ID
    - page_num: 页码
    - page_size: 每页数量
    - begin_time: 开始时间
    - end_time: 结束时间
    
    返回:
    - rows: 用户列表
    - total: 总数
    """
    result = await service.get_user_list(query)
    return ResponseUtil.success(data=result)

@router.get(
    "/{user_id}",
    summary="获取用户详情",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:query"))]
)
async def get_user_detail(
    user_id: int = Path(..., description="用户ID"),
    service: UserService = Depends()
):
    """
    获取用户详情
    
    参数:
    - user_id: 用户ID
    
    返回:
    - 用户详细信息
    """
    user = await service.get_user_by_id(user_id)
    return ResponseUtil.success(data=user)

@router.post(
    "",
    summary="新增用户",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:add"))]
)
@Log(title="用户管理", business_type=2)
async def add_user(
    user: UserModel,
    service: UserService = Depends()
):
    """
    新增用户
    
    参数:
    - user: 用户信息
    
    返回:
    - 操作结果
    """
    await service.add_user(user)
    return ResponseUtil.success(msg="新增成功")

@router.put(
    "",
    summary="修改用户",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:edit"))]
)
@Log(title="用户管理", business_type=3)
async def update_user(
    user: UserModel,
    service: UserService = Depends()
):
    """
    修改用户
    
    参数:
    - user: 用户信息
    
    返回:
    - 操作结果
    """
    await service.update_user(user)
    return ResponseUtil.success(msg="修改成功")

@router.delete(
    "/{user_ids}",
    summary="删除用户",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:remove"))]
)
@Log(title="用户管理", business_type=4)
async def delete_user(
    user_ids: str = Path(..., description="用户ID,多个用逗号分隔"),
    service: UserService = Depends()
):
    """
    删除用户
    
    参数:
    - user_ids: 用户ID列表(逗号分隔)
    
    返回:
    - 操作结果
    """
    ids = [int(id) for id in user_ids.split(",")]
    await service.delete_users(ids)
    return ResponseUtil.success(msg="删除成功")

@router.put(
    "/resetPwd",
    summary="重置密码",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:resetPwd"))]
)
@Log(title="用户管理", business_type=3)
async def reset_password(
    user_id: int = Query(..., description="用户ID"),
    password: str = Query(..., description="新密码"),
    service: UserService = Depends()
):
    """
    重置用户密码
    
    参数:
    - user_id: 用户ID
    - password: 新密码
    
    返回:
    - 操作结果
    """
    await service.reset_password(user_id, password)
    return ResponseUtil.success(msg="重置成功")

@router.put(
    "/changeStatus",
    summary="修改用户状态",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:edit"))]
)
@Log(title="用户管理", business_type=3)
async def change_status(
    user_id: int = Query(..., description="用户ID"),
    status: str = Query(..., description="状态"),
    service: UserService = Depends()
):
    """
    修改用户状态
    
    参数:
    - user_id: 用户ID
    - status: 状态(0正常 1停用)
    
    返回:
    - 操作结果
    """
    await service.change_status(user_id, status)
    return ResponseUtil.success(msg="修改成功")
```

## API 文档

### 自动生成文档

FastAPI 自动生成交互式 API 文档:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 文档注释规范

```python
@router.get("/list", summary="获取用户列表")
async def get_user_list(
    user_name: str = Query(None, description="用户名"),
    page_num: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """
    获取用户列表
    
    详细说明:
    - 支持按用户名模糊查询
    - 支持分页查询
    - 需要 system:user:list 权限
    
    参数说明:
    - user_name: 用户名,支持模糊查询
    - page_num: 页码,从1开始
    - page_size: 每页数量,最大100
    
    返回格式:
    ```json
    {
      "code": 200,
      "msg": "操作成功",
      "data": {
        "rows": [...],
        "total": 100
      }
    }
    ```
    """
    pass
```

## 权限控制

### 接口权限

```python
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

@router.get(
    "/list",
    dependencies=[Depends(CheckUserInterfaceAuth("system:user:list"))]
)
async def get_user_list(...):
    pass
```

### 数据权限

```python
from module_admin.aspect.data_scope import GetDataScope

@router.get("/list")
async def get_user_list(
    data_scope: str = Depends(GetDataScope("SysUser")),
    service: UserService = Depends()
):
    # data_scope 包含数据权限 SQL
    result = await service.get_user_list_with_scope(data_scope)
    return ResponseUtil.success(data=result)
```

## 日志记录

### 操作日志

```python
from module_admin.annotation.log_annotation import Log

@router.post("")
@Log(title="用户管理", business_type=2)  # business_type: 1查询 2新增 3修改 4删除
async def add_user(...):
    pass
```

## 异常处理

### 业务异常

```python
from exceptions.exception import ServiceException

async def add_user(self, user: UserModel):
    # 检查用户名是否存在
    existing = await self.user_dao.get_user_by_username(user.user_name)
    if existing:
        raise ServiceException(message="用户名已存在")
    
    # 检查手机号是否存在
    if user.phonenumber:
        existing = await self.user_dao.get_user_by_phone(user.phonenumber)
        if existing:
            raise ServiceException(message="手机号已被使用")
    
    # 保存用户
    await self.user_dao.add_user(user)
```

### 全局异常处理

系统自动捕获并处理异常,返回统一格式:

```json
{
  "code": 500,
  "msg": "用户名已存在",
  "data": null
}
```

## API 测试

### 使用 Swagger UI

1. 访问 http://localhost:8000/docs
2. 点击 API 端点
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"

### 使用 curl

```bash
# 获取用户列表
curl -X GET "http://localhost:8000/system/user/list?page_num=1&page_size=10" \
  -H "Authorization: Bearer <token>"

# 新增用户
curl -X POST "http://localhost:8000/system/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_name": "test",
    "nick_name": "测试用户",
    "password": "123456"
  }'
```

## 最佳实践

### 1. 使用 Pydantic 模型验证
```python
class UserModel(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=30)
    email: Optional[str] = Field(None, regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

### 2. 统一响应格式
```python
return ResponseUtil.success(data=result)
return ResponseUtil.error(msg="操作失败")
```

### 3. 添加权限控制
```python
dependencies=[Depends(CheckUserInterfaceAuth("system:user:list"))]
```

### 4. 记录操作日志
```python
@Log(title="用户管理", business_type=2)
```

### 5. 编写清晰的文档注释
```python
"""
获取用户列表
...
"""
```

## 下一步

- [权限认证](./06-权限认证.md) - 理解权限系统
- [开发规范](./07-开发规范.md) - 编码标准
