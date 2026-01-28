# 项目上下文 - AI 开发指南

## 项目概述

企业级中后台管理系统，采用前后端分离架构。基于 RuoYi 框架，使用 Vue3 + FastAPI 技术栈。

## 技术栈

### 前端

- **框架**: Vue 3.4 + TypeScript 5.x
- **构建**: Vite 5.x
- **状态管理**: Pinia 2.x
- **UI 组件库**: Element Plus 2.7 + @zxio/zxui
- **图表/可视化**: ECharts 5.x + AntV X6/G2Plot
- **样式**: Tailwind CSS 4.x
- **测试**: Vitest + Testing Library

### 后端

- **框架**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.0 (异步)
- **验证**: Pydantic 2.x
- **数据库**: MySQL / PostgreSQL
- **缓存**: Redis
- **任务调度**: APScheduler
- **数据库迁移**: Alembic

## 目录结构

### 前端 (ruoyi-fastapi-frontend)

```
src/
├── api/                    # API 层
│   ├── _generated/         # OpenAPI 自动生成的类型和客户端
│   ├── _shared/            # 共享类型和 HTTP 客户端
│   │   ├── types/          # 通用类型定义
│   │   └── http-client.ts  # 类型安全的请求封装
│   ├── system/             # 系统管理 API
│   ├── project/            # 项目管理 API
│   └── ...
├── components/             # 全局组件
├── composables/            # 组合式函数
├── directive/              # 自定义指令
├── hooks/                  # 自定义 Hooks
├── layout/                 # 布局组件
├── plugins/                # 插件
├── router/                 # 路由配置
├── stores/                 # Pinia 状态管理
├── utils/                  # 工具函数
└── views/                  # 页面视图
```

### 后端 (ruoyi-fastapi-backend)

```
├── config/                 # 配置
│   ├── database.py         # 数据库配置
│   ├── env.py              # 环境变量配置
│   └── ...
├── module_admin/           # 管理模块
│   ├── controller/         # 控制器层 (路由)
│   ├── service/            # 服务层 (业务逻辑)
│   ├── dao/                # 数据访问层
│   ├── entity/
│   │   ├── do/             # 数据对象 (ORM 模型)
│   │   └── vo/             # 值对象 (Pydantic 模型)
│   └── shared/             # 共享模块
│       ├── error_codes.py  # 统一错误码
│       └── response.py     # 统一响应模型
├── alembic/                # 数据库迁移
│   └── versions/           # 迁移文件
├── exceptions/             # 异常处理
├── middlewares/            # 中间件
└── utils/                  # 工具函数
```

## 核心约定

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 前端 API 函数 | camelCase | `getUserList`, `createProject` |
| 后端路由函数 | snake_case | `get_user_list`, `create_project` |
| 类型接口 | PascalCase | `UserResponse`, `PageRequest` |
| Vue 组件 | PascalCase.vue | `UserList.vue`, `ProjectForm.vue` |
| Composable | use + PascalCase | `useUser`, `useTable` |
| Pinia Store | use + PascalCase + Store | `useUserStore` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |

### Pydantic 模型命名

| 类型 | 后缀 | 示例 |
|------|------|------|
| 基础实体 | Model | `UserModel`, `RoleModel` |
| 查询请求 | QueryModel / PageQueryModel | `UserQueryModel`, `UserPageQueryModel` |
| 新增请求 | AddXxxModel | `AddUserModel` |
| 编辑请求 | EditXxxModel | `EditUserModel` |
| 删除请求 | DeleteXxxModel | `DeleteUserModel` |
| 响应模型 | ResponseModel | `UserResponseModel` |

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 前端 API | kebab-case.ts | `user.ts`, `project-version.ts` |
| 后端控制器 | snake_case_controller.py | `user_controller.py` |
| 后端服务 | snake_case_service.py | `user_service.py` |
| ORM 模型 | snake_case_do.py | `user_do.py` |
| Pydantic 模型 | snake_case_vo.py | `user_vo.py` |

## 开发模式

### API 类型共享流程

```
1. 定义 Pydantic 模型 (后端)
   ↓
2. FastAPI 自动生成 OpenAPI
   ↓
3. 运行 npm run api:generate
   ↓
4. 生成 TypeScript 类型 (前端 src/api/_generated/)
   ↓
5. 前端使用生成的类型
```

### 数据库迁移流程

```bash
# 生成迁移文件
cd ruoyi-fastapi-backend
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### Git Hooks

安装: `bash scripts/setup-hooks.sh`

- **post-merge**: pull 代码后自动执行 `alembic upgrade head`

## 禁止事项

1. **不使用 any 类型** - 所有变量必须有明确类型
2. **不在 controller 中写业务逻辑** - 业务逻辑放在 service 层
3. **不手动定义已自动生成的类型** - 使用 `_generated/` 中的类型
4. **不使用 console.log 调试** - 使用适当的日志工具
5. **不忽略 TypeScript/mypy 错误** - 修复而不是忽略

## 常用命令

### 前端

```bash
npm run dev              # 开发服务器
npm run type-check       # 类型检查
npm run type-check:strict # 严格类型检查 (新代码)
npm run api:generate     # 生成 API 类型
npm run test             # 运行测试
npm run lint             # 代码检查
```

### 后端

```bash
# 开发
python server.py --env dev

# 代码检查 (需先安装 requirements-dev.txt)
ruff check .
mypy .

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "描述"
```

## 错误码规范

| 范围 | 类型 | 示例 |
|------|------|------|
| 200 | 成功 | SUCCESS |
| 4xxx | 客户端错误 | BAD_REQUEST, UNAUTHORIZED |
| 50xx | 用户相关 | USER_NOT_FOUND, INVALID_PASSWORD |
| 51xx | 角色相关 | ROLE_NOT_FOUND |
| 52xx | 部门相关 | DEPT_NOT_FOUND |
| 9xxx | 系统错误 | INTERNAL_ERROR, DATABASE_ERROR |

详见: `module_admin/shared/error_codes.py`

## 响应格式

### 标准响应

```json
{
  "code": 200,
  "msg": "success",
  "data": { ... }
}
```

### 分页响应

```json
{
  "code": 200,
  "msg": "success",
  "rows": [...],
  "total": 100
}
```

## 相关文档

- [CONVENTIONS.md](./CONVENTIONS.md) - 详细命名和目录约定
- [PATTERNS.md](./PATTERNS.md) - 代码模式库
