# RuoYi-Vue3-FastAPI

基于 Vue3 + FastAPI 前后端分离的快速开发框架

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
- MySQL ≥ 5.7 或 PostgreSQL
- Node.js ≥ 16
- Redis

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

### 前端启动

```bash
# 进入前端目录
cd ruoyi-fastapi-frontend

# 安装依赖
npm install
# 或使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 启动开发服务器
npm run dev
```

前端默认运行在 `http://localhost:80`

### 后端启动

#### 1. 安装依赖

```bash
# 进入后端目录
cd ruoyi-fastapi-backend

# MySQL 数据库
pip install -r requirements.txt

# PostgreSQL 数据库
pip install -r requirements-pg.txt
```

#### 2. 配置环境

编辑 `.env.dev` 文件，配置数据库和 Redis 连接信息：

```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=ruoyi-fastapi

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

#### 3. 初始化数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE `ruoyi-fastapi` DEFAULT CHARACTER SET utf8mb4;"

# 导入 SQL 文件
# MySQL
mysql -u root -p ruoyi-fastapi < sql/ruoyi-fastapi.sql

# PostgreSQL
psql -U postgres -d ruoyi-fastapi -f sql/ruoyi-fastapi-pg.sql
```

#### 4. 启动后端服务

```bash
# 开发环境
python app.py --env=dev

# 生产环境
python app.py --env=prod
```

后端 API 文档访问：`http://localhost:8000/docs`

### 默认账号

- 用户名：`admin`
- 密码：`admin123`

## 生产部署

### 前端构建

```bash
cd ruoyi-fastapi-frontend

# 构建生产环境
npm run build:prod

# 构建测试环境
npm run build:stage
```

构建产物在 `dist` 目录下，可部署到 Nginx 等 Web 服务器。

### 后端部署

1. 编辑 `.env.prod` 配置生产环境参数
2. 使用生产级 ASGI 服务器（如 Gunicorn + Uvicorn）：

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## License

MIT License