# 代码模式库

本文档收集项目中常用的代码模式，供 AI 和开发者参考。

## 前端模式

### 1. 表格页面模式

```vue
<template>
  <div class="app-container">
    <!-- 搜索区域 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="用户名" prop="userName">
        <el-input v-model="queryParams.userName" placeholder="请输入用户名" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">搜索</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" @click="handleAdd" v-hasPermi="['system:user:add']">
          新增
        </el-button>
      </el-col>
    </el-row>

    <!-- 表格 -->
    <el-table v-loading="loading" :data="userList">
      <el-table-column label="用户名" prop="userName" />
      <el-table-column label="昵称" prop="nickName" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <!-- 表单内容 -->
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { userApi } from '@/api/system/user';
import type { UserModel } from '@/api/_generated';

const loading = ref(false);
const userList = ref<UserModel[]>([]);
const total = ref(0);

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  userName: '',
});

const getList = async () => {
  loading.value = true;
  const res = await userApi.getList(queryParams);
  userList.value = res.rows;
  total.value = res.total;
  loading.value = false;
};

const handleQuery = () => {
  queryParams.pageNum = 1;
  getList();
};

const resetQuery = () => {
  queryParams.userName = '';
  handleQuery();
};

// 初始化
getList();
</script>
```

### 2. 表单弹窗模式

```vue
<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';

interface Props {
  visible: boolean;
  data?: UserModel | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  'update:visible': [value: boolean];
  'success': [];
}>();

const formRef = ref<FormInstance>();
const loading = ref(false);

const isEdit = computed(() => !!props.data?.userId);
const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户');

const form = reactive({
  userId: undefined as number | undefined,
  userName: '',
  nickName: '',
});

const rules: FormRules = {
  userName: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
};

// 监听 visible 变化，初始化表单
watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(form, props.data);
  } else {
    formRef.value?.resetFields();
  }
});

const submitForm = async () => {
  await formRef.value?.validate();
  loading.value = true;
  
  if (isEdit.value) {
    await userApi.update(form);
  } else {
    await userApi.create(form);
  }
  
  loading.value = false;
  emit('update:visible', false);
  emit('success');
};
</script>
```

### 3. 组合式函数模式 (useTable)

```typescript
// src/composables/useTable.ts
import { ref, reactive, watch } from 'vue';
import type { ApiResponse, PageResponse } from '@/api/_shared/types/common';

interface UseTableOptions<T, Q> {
  api: (params: Q) => Promise<PageResponse<T> & { code: number; msg: string }>;
  defaultParams?: Partial<Q>;
  immediate?: boolean;
}

export function useTable<T, Q extends { pageNum: number; pageSize: number }>({
  api,
  defaultParams = {},
  immediate = true,
}: UseTableOptions<T, Q>) {
  const loading = ref(false);
  const list = ref<T[]>([]) as Ref<T[]>;
  const total = ref(0);

  const params = reactive({
    pageNum: 1,
    pageSize: 10,
    ...defaultParams,
  }) as Q;

  const fetch = async () => {
    loading.value = true;
    const res = await api(params);
    list.value = res.rows;
    total.value = res.total;
    loading.value = false;
  };

  const search = () => {
    params.pageNum = 1;
    fetch();
  };

  const reset = (resetParams: Partial<Q> = {}) => {
    Object.assign(params, { pageNum: 1, pageSize: 10, ...defaultParams, ...resetParams });
    fetch();
  };

  if (immediate) {
    fetch();
  }

  return {
    loading,
    list,
    total,
    params,
    fetch,
    search,
    reset,
  };
}
```

## 后端模式

### 1. 分页查询模式

```python
# DAO 层
async def get_list_with_page(
    self,
    query: UserPageQueryModel,
) -> tuple[list[SysUser], int]:
    """分页查询用户列表"""
    # 基础查询
    stmt = select(SysUser).where(SysUser.del_flag == '0')
    count_stmt = select(func.count()).select_from(SysUser).where(SysUser.del_flag == '0')
    
    # 动态条件
    if query.user_name:
        condition = SysUser.user_name.like(f'%{query.user_name}%')
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    
    if query.status:
        stmt = stmt.where(SysUser.status == query.status)
        count_stmt = count_stmt.where(SysUser.status == query.status)
    
    # 排序
    stmt = stmt.order_by(SysUser.create_time.desc())
    
    # 分页
    stmt = stmt.offset((query.page_num - 1) * query.page_size).limit(query.page_size)
    
    # 执行查询
    result = await self.db.execute(stmt)
    count_result = await self.db.execute(count_stmt)
    
    return result.scalars().all(), count_result.scalar()


# Service 层
async def get_user_list(self, query: UserPageQueryModel):
    """获取用户分页列表"""
    users, total = await self.user_dao.get_list_with_page(query)
    return {
        'rows': [UserModel.model_validate(u) for u in users],
        'total': total,
    }
```

### 2. 事务模式

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user_with_roles(
    self,
    data: AddUserModel,
    db: AsyncSession,
):
    """创建用户并关联角色 (事务)"""
    async with db.begin():
        # 创建用户
        user = SysUser(**data.model_dump(exclude={'role_ids'}))
        db.add(user)
        await db.flush()  # 获取自增 ID
        
        # 创建角色关联
        for role_id in data.role_ids:
            user_role = SysUserRole(user_id=user.user_id, role_id=role_id)
            db.add(user_role)
        
        # 事务自动提交
```

### 3. 依赖注入模式

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from config.get_db import get_db


class UserDao:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db


class UserService:
    def __init__(self, user_dao: UserDao = Depends()):
        self.user_dao = user_dao


@router.get('/list')
async def get_user_list(
    query: UserPageQueryModel = Depends(),
    user_service: UserService = Depends(),
):
    return await user_service.get_user_list(query)
```

### 4. 缓存模式

```python
from config.get_redis import get_redis
import json

CACHE_KEY_USER = 'user:{user_id}'
CACHE_TTL = 3600  # 1小时


async def get_user_by_id_cached(self, user_id: int) -> UserModel | None:
    """获取用户 (带缓存)"""
    redis = await get_redis()
    cache_key = CACHE_KEY_USER.format(user_id=user_id)
    
    # 尝试从缓存获取
    cached = await redis.get(cache_key)
    if cached:
        return UserModel.model_validate_json(cached)
    
    # 从数据库获取
    user = await self.user_dao.get_user_by_id(user_id)
    if user:
        user_model = UserModel.model_validate(user)
        # 写入缓存
        await redis.setex(cache_key, CACHE_TTL, user_model.model_dump_json())
        return user_model
    
    return None


async def invalidate_user_cache(self, user_id: int):
    """清除用户缓存"""
    redis = await get_redis()
    await redis.delete(CACHE_KEY_USER.format(user_id=user_id))
```

### 5. 异常处理模式

```python
from module_admin.shared import BusinessException, ErrorCode

# 在 Service 层抛出业务异常
async def get_user_by_id(self, user_id: int) -> UserModel:
    user = await self.user_dao.get_user_by_id(user_id)
    if not user:
        raise BusinessException(ErrorCode.USER_NOT_FOUND, f'用户不存在: {user_id}')
    if user.status == '1':
        raise BusinessException(ErrorCode.USER_DISABLED, f'用户已禁用: {user.user_name}')
    return UserModel.model_validate(user)


# 全局异常处理器 (exceptions/handle.py)
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content={'code': exc.code, 'msg': exc.message, 'data': None},
    )
```

## 测试模式

### 前端单元测试

```typescript
// tests/components/UserTable.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import UserTable from '@/components/UserTable.vue';

describe('UserTable', () => {
  it('renders user list correctly', async () => {
    const users = [
      { userId: 1, userName: 'admin', nickName: '管理员' },
      { userId: 2, userName: 'test', nickName: '测试用户' },
    ];

    const wrapper = mount(UserTable, {
      props: { data: users },
    });

    expect(wrapper.findAll('tr').length).toBe(users.length + 1); // +1 for header
    expect(wrapper.text()).toContain('admin');
    expect(wrapper.text()).toContain('测试用户');
  });
});
```

### 后端单元测试

```python
# tests/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from module_admin.service.user_service import UserService
from module_admin.shared import BusinessException, ErrorCode


@pytest.fixture
def mock_user_dao():
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_dao):
    service = UserService.__new__(UserService)
    service.user_dao = mock_user_dao
    return service


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service, mock_user_dao):
    # Arrange
    mock_user = MagicMock(user_id=1, user_name='admin', status='0')
    mock_user_dao.get_user_by_id.return_value = mock_user

    # Act
    result = await user_service.get_user_by_id(1)

    # Assert
    assert result.user_id == 1
    assert result.user_name == 'admin'


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service, mock_user_dao):
    # Arrange
    mock_user_dao.get_user_by_id.return_value = None

    # Act & Assert
    with pytest.raises(BusinessException) as exc_info:
        await user_service.get_user_by_id(999)
    
    assert exc_info.value.code == ErrorCode.USER_NOT_FOUND
```
