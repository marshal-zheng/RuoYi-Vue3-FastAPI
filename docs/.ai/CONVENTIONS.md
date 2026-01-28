# 命名和目录约定

## 前端约定

### 组件命名

```typescript
// 页面组件 - views/
UserList.vue        // 列表页
UserForm.vue        // 表单页 (新增/编辑)
UserDetail.vue      // 详情页

// 业务组件 - components/
UserTable.vue       // 用户表格
UserSearch.vue      // 用户搜索
UserDialog.vue      // 用户弹窗

// 通用组件
BaseTable.vue       // 基础表格
BaseForm.vue        // 基础表单
BaseDialog.vue      // 基础弹窗
```

### API 文件结构

```typescript
// src/api/system/user.ts
import { http } from '@/api/_shared';
import type { UserModel, UserPageQueryModel } from '@/api/_generated';

/**
 * 用户管理 API
 */
export const userApi = {
  /** 获取用户分页列表 */
  getList: (params: UserPageQueryModel) => 
    http.page<UserModel>('/system/user/list', params),

  /** 获取用户详情 */
  getById: (userId: number) => 
    http.get<UserModel>(`/system/user/${userId}`),

  /** 新增用户 */
  create: (data: AddUserModel) => 
    http.post<void>('/system/user', data),

  /** 更新用户 */
  update: (data: EditUserModel) => 
    http.put<void>('/system/user', data),

  /** 删除用户 */
  remove: (userIds: string) => 
    http.delete<void>(`/system/user/${userIds}`),
} as const;
```

### Composable 结构

```typescript
// src/composables/useUser.ts
import { ref, computed } from 'vue';
import { userApi } from '@/api/system/user';
import type { UserModel } from '@/api/_generated';

export function useUser() {
  const loading = ref(false);
  const userList = ref<UserModel[]>([]);

  const fetchUsers = async () => {
    loading.value = true;
    const { rows } = await userApi.getList({});
    userList.value = rows;
    loading.value = false;
  };

  return {
    loading,
    userList,
    fetchUsers,
  };
}
```

### Pinia Store 结构

```typescript
// src/stores/user.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { UserInfoModel } from '@/api/_generated';

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfoModel | null>(null);
  const token = ref<string>('');

  const setUserInfo = (info: UserInfoModel) => {
    userInfo.value = info;
  };

  const logout = () => {
    userInfo.value = null;
    token.value = '';
  };

  return {
    userInfo,
    token,
    setUserInfo,
    logout,
  };
});
```

## 后端约定

### Controller 结构

```python
# module_admin/controller/user_controller.py
from fastapi import APIRouter, Depends, Query
from module_admin.service.user_service import UserService
from module_admin.entity.vo.user_vo import (
    UserModel,
    UserPageQueryModel,
    AddUserModel,
    EditUserModel,
)
from utils.response_util import ResponseUtil

router = APIRouter(prefix='/system/user', tags=['用户管理'])


@router.get('/list')
async def get_user_list(
    query: UserPageQueryModel = Depends(),
    user_service: UserService = Depends(),
):
    """获取用户分页列表"""
    result = await user_service.get_user_list(query)
    return ResponseUtil.success(result)


@router.get('/{user_id}')
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(),
):
    """获取用户详情"""
    result = await user_service.get_user_by_id(user_id)
    return ResponseUtil.success(data=result)


@router.post('')
async def create_user(
    data: AddUserModel,
    user_service: UserService = Depends(),
):
    """新增用户"""
    await user_service.create_user(data)
    return ResponseUtil.success(msg='新增成功')
```

### Service 结构

```python
# module_admin/service/user_service.py
from module_admin.dao.user_dao import UserDao
from module_admin.entity.vo.user_vo import (
    UserModel,
    UserPageQueryModel,
    AddUserModel,
)
from module_admin.shared import BusinessException, ErrorCode


class UserService:
    def __init__(self, user_dao: UserDao = Depends()):
        self.user_dao = user_dao

    async def get_user_list(self, query: UserPageQueryModel):
        """获取用户分页列表"""
        return await self.user_dao.get_user_list(query)

    async def get_user_by_id(self, user_id: int) -> UserModel:
        """获取用户详情"""
        user = await self.user_dao.get_user_by_id(user_id)
        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND, f'用户不存在: {user_id}')
        return UserModel.model_validate(user)

    async def create_user(self, data: AddUserModel):
        """新增用户"""
        # 检查用户名是否存在
        existing = await self.user_dao.get_user_by_name(data.user_name)
        if existing:
            raise BusinessException(ErrorCode.USER_ALREADY_EXISTS, f'用户已存在: {data.user_name}')
        await self.user_dao.create_user(data)
```

### DAO 结构

```python
# module_admin/dao/user_dao.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.user_vo import UserPageQueryModel


class UserDao:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_user_list(self, query: UserPageQueryModel):
        """获取用户分页列表"""
        stmt = select(SysUser).where(SysUser.del_flag == '0')
        
        if query.user_name:
            stmt = stmt.where(SysUser.user_name.like(f'%{query.user_name}%'))
        
        # 分页
        stmt = stmt.offset((query.page_num - 1) * query.page_size)
        stmt = stmt.limit(query.page_size)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_by_id(self, user_id: int) -> SysUser | None:
        """根据 ID 获取用户"""
        stmt = select(SysUser).where(SysUser.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

### Pydantic 模型结构

```python
# module_admin/entity/vo/user_vo.py
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional


class UserModel(BaseModel):
    """用户基础模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: Optional[int] = Field(default=None, description='用户ID')
    user_name: Optional[str] = Field(default=None, description='用户名')
    nick_name: Optional[str] = Field(default=None, description='昵称')


class UserQueryModel(UserModel):
    """用户查询模型"""
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


class UserPageQueryModel(UserQueryModel):
    """用户分页查询模型"""
    page_num: int = Field(default=1, ge=1, description='页码')
    page_size: int = Field(default=10, ge=1, le=100, description='每页数量')


class AddUserModel(UserModel):
    """新增用户模型"""
    password: str = Field(..., description='密码')
    role_ids: list[int] = Field(default=[], description='角色ID列表')
```

### ORM 模型结构

```python
# module_admin/entity/do/user_do.py
from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base


class SysUser(Base):
    """用户表"""
    __tablename__ = 'sys_user'

    user_id = Column(Integer, primary_key=True, comment='用户ID')
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    email = Column(String(50), default='', comment='邮箱')
    phonenumber = Column(String(11), default='', comment='手机号')
    status = Column(String(1), default='0', comment='状态 0正常 1停用')
    del_flag = Column(String(1), default='0', comment='删除标志 0存在 2删除')
    create_time = Column(DateTime, comment='创建时间')
    update_time = Column(DateTime, comment='更新时间')
```

## 数据库迁移约定

### 迁移文件命名

```
YYYYMMDD_HHMMSS_描述.py

示例:
20240115_100000_add_user_phone.py
20240116_143000_create_project_table.py
```

### 迁移文件结构

```python
"""add user phone field

Revision ID: xxx
Revises: yyy
Create Date: 2024-01-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx'
down_revision = 'yyy'


def upgrade() -> None:
    """升级：添加 phone 字段"""
    op.add_column('sys_user', sa.Column('phone', sa.String(20), comment='手机号'))
    op.create_index('idx_user_phone', 'sys_user', ['phone'])


def downgrade() -> None:
    """回滚：删除 phone 字段"""
    op.drop_index('idx_user_phone', 'sys_user')
    op.drop_column('sys_user', 'phone')
```

## 异常处理约定

```python
# 使用统一错误码
from module_admin.shared import BusinessException, ErrorCode

# 业务异常
raise BusinessException(ErrorCode.USER_NOT_FOUND, f'用户不存在: {user_id}')

# 使用预定义异常类
from module_admin.shared.error_codes import UserNotFoundException
raise UserNotFoundException(user_id)
```
