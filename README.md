# Vue3 快速开发框架

基于 Vue3 + FastAPI 前后端分离的企业级快速开发框架

## 技术栈

### 前端
- Vue 3
- Element Plus
- TypeScript
- Vite

### 后端
- FastAPI
- SQLAlchemy
- MySQL / PostgreSQL
- Redis
- OAuth2 & JWT

## 系统要求

- Python ≥ 3.9
- Node.js ≥ 16
- MySQL ≥ 5.7 或 PostgreSQL
- Redis ≥ 5.0

## 核心功能

### 权限管理
- **用户管理**：系统用户配置和管理
- **角色管理**：角色菜单权限分配、数据范围权限划分
- **菜单管理**：系统菜单、操作权限、按钮权限配置
- **部门管理**：组织机构管理（公司、部门、小组）
- **岗位管理**：用户岗位职务配置

### 系统管理
- **字典管理**：系统固定数据维护
- **参数管理**：系统动态参数配置
- **通知公告**：系统公告信息发布

### 日志监控
- **操作日志**：系统操作日志记录和查询
- **登录日志**：登录日志记录，包含异常登录
- **在线用户**：活跃用户状态监控
- **服务监控**：CPU、内存、磁盘等系统信息监控
- **缓存监控**：Redis 缓存信息查询和统计

### 开发工具
- **定时任务**：在线任务调度管理，包含执行日志
- **代码生成**：根据数据库表一键生成前后端代码
- **系统接口**：自动生成 API 接口文档
- **表单构建**：可视化表单设计器

## 快速开始

### 方式一：仅启动前端（最快）

前端是完全独立的 Vue3 项目，可以单独开发：

```bash
cd ruoyi-fastapi-frontend

# 安装依赖
yarn install

# 启动开发服务器
yarn dev
```

前端访问：http://localhost:80

> 前端使用 Vite 构建，支持热更新。修改代码后会自动刷新浏览器。
> 
> 注意：仅启动前端时，需要确保后端服务已运行，或配置 Mock 数据。

**常用命令：**
```bash
yarn build:prod      # 生产环境构建
yarn build:stage     # 预发布环境构建
yarn type-check      # TypeScript 类型检查
yarn lint            # 代码检查
yarn test            # 运行测试
```

### 方式二：Docker 本地开发（推荐）

使用 Docker Compose 一键启动完整开发环境，无需手动配置数据库和 Redis：

```bash
# 启动所有服务（前端 + 后端 + MySQL + Redis）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务访问地址：
- 前端：http://localhost:80
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

> 详细 Docker 使用说明请查看 [DOCKER_USAGE.md](./DOCKER_USAGE.md)

### 方式三：一键启动脚本

适合已有本地 MySQL 和 Redis 环境的开发者：

```bash
# 首次使用 - 自动安装所有依赖并配置环境
./setup.sh

# 日常开发 - 快速启动前后端服务
./start.sh
```

> 详细说明请查看 [QUICK_START.md](./QUICK_START.md)

### 方式四：手动启动完整环境

#### 1. 准备环境

确保已安装：
- Python ≥ 3.9
- Node.js ≥ 16
- MySQL ≥ 5.7 或 PostgreSQL
- Redis ≥ 5.0

#### 2. 初始化数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE \`ruoyi-fastapi\` CHARACTER SET utf8mb4;"

# 导入初始数据
mysql -u root -p ruoyi-fastapi < ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

#### 3. 启动后端

```bash
cd ruoyi-fastapi-backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.dev .env.dev.local  # 复制配置文件
vim .env.dev.local          # 修改数据库和 Redis 连接信息

# 启动开发服务器
python app.py --env=dev
```

后端服务：
- API 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

#### 4. 启动前端

```bash
cd ruoyi-fastapi-frontend

# 安装依赖
yarn install

# 启动开发服务器
yarn dev
```

前端访问：http://localhost:80

### 默认账号

- 用户名：`admin`
- 密码：`admin123`

## 生产部署

### 前端

```bash
cd ruoyi-fastapi-frontend
yarn build:prod
```

构建产物在 `dist` 目录，部署到 Nginx 等 Web 服务器。

### 后端

```bash
# 配置生产环境
vim .env.prod

# 使用 Gunicorn + Uvicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 项目结构

```
vue3-fastapi/
├── ruoyi-fastapi-frontend/    # Vue3 前端项目（独立模块）
├── ruoyi-fastapi-backend/     # FastAPI 后端项目
├── docker-compose.yml         # Docker 编排配置
├── setup.sh                   # 环境初始化脚本
├── start.sh                   # 快速启动脚本
├── QUICK_START.md            # 详细启动指南
├── DOCKER_USAGE.md           # Docker 使用指南
└── README.md                 # 项目说明
```

### 使用 Docker 开发的优势

- ✅ 无需手动安装 MySQL、Redis
- ✅ 环境一致性，避免"在我机器上能跑"问题
- ✅ 一键启动/停止所有服务
- ✅ 数据持久化，重启不丢失
- ✅ 支持热更新，代码修改实时生效

## License

MIT License