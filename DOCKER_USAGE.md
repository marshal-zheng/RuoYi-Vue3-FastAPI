# Docker 使用指南 / Docker Usage Guide

本项目提供了开发环境和生产环境的 Docker Compose 配置。

## 快速开始 / Quick Start

### 开发环境 (Development)

开发环境支持代码热更新，修改代码后自动重启服务。

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up

# 后台运行
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷（慎用）
docker-compose -f docker-compose.dev.yml down -v
```

### 生产环境 (Production)

生产环境使用优化的构建配置，不挂载源代码。

```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

## 环境配置 / Environment Configuration

### 开发环境特性

- ✅ 代码热更新（前端和后端）
- ✅ 源代码挂载到容器
- ✅ 自动初始化数据库
- ✅ 开发工具和调试支持
- ✅ 详细的日志输出

**挂载目录：**
- 前端：`./ruoyi-fastapi-frontend` → `/app`
- 后端：`./ruoyi-fastapi-backend` → `/app`

**排除目录：**
- 前端：`node_modules`, `dist`
- 后端：`__pycache__`, `.pytest_cache`, `venv`

### 生产环境特性

- ✅ 优化的构建配置
- ✅ 资源限制和预留
- ✅ 自动重启策略
- ✅ 性能优化的数据库配置
- ✅ Redis 内存限制和淘汰策略

## 服务访问 / Service Access

### 开发环境端口

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| 前端 | 80 | http://localhost |
| 后端 API | 8000 | http://localhost:8000 |
| API 文档 (Swagger) | 8000 | http://localhost:8000/docs |
| API 文档 (ReDoc) | 8000 | http://localhost:8000/redoc |
| OpenAPI JSON | 8000 | http://localhost:8000/openapi.json |
| MySQL | 3307 | localhost:3307 |
| Redis | 6379 | localhost:6379 |

**注意：** Docker 环境中后端直接暴露，不使用 `/dev-api` 前缀。前端通过 Vite 代理访问后端时会自动添加前缀。

### 生产环境端口

与开发环境相同，但服务经过优化。

## 常用命令 / Common Commands

### 重新构建镜像

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml build

# 生产环境
docker-compose -f docker-compose.prod.yml build

# 强制重新构建（不使用缓存）
docker-compose -f docker-compose.dev.yml build --no-cache
```

### 查看服务状态

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml ps

# 生产环境
docker-compose -f docker-compose.prod.yml ps
```

### 进入容器

```bash
# 进入后端容器
docker exec -it ruoyi-backend-dev sh    # 开发环境
docker exec -it ruoyi-backend-prod sh   # 生产环境

# 进入前端容器
docker exec -it ruoyi-frontend-dev sh   # 开发环境
docker exec -it ruoyi-frontend-prod sh  # 生产环境

# 进入数据库容器
docker exec -it ruoyi-mysql-dev mysql -uroot -proot
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend

# 查看最近 100 行日志
docker-compose -f docker-compose.dev.yml logs --tail=100 backend
```

### 数据库操作

```bash
# 导入 SQL 文件（开发环境会自动导入 sql 目录下的文件）
docker exec -i ruoyi-mysql-dev mysql -uroot -proot ruoyi-fastapi < ./ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql

# 备份数据库
docker exec ruoyi-mysql-dev mysqldump -uroot -proot ruoyi-fastapi > backup.sql

# 连接 Redis
docker exec -it ruoyi-redis-dev redis-cli -a redis123456
```

## 开发工作流 / Development Workflow

### 1. 首次启动

```bash
# 复制环境变量文件
cp .env.example .env

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动（约 30-60 秒）
docker-compose -f docker-compose.dev.yml logs -f
```

### 2. 日常开发

- 修改前端代码：保存后自动热更新，浏览器自动刷新
- 修改后端代码：保存后自动重启 FastAPI 服务
- 修改依赖：需要重新构建镜像

### 3. 安装新依赖

**前端：**
```bash
# 方式 1：在容器内安装
docker exec -it ruoyi-frontend-dev yarn add <package-name>

# 方式 2：本地安装后重启
cd ruoyi-fastapi-frontend
yarn add <package-name>
docker-compose -f docker-compose.dev.yml restart frontend
```

**后端：**
```bash
# 方式 1：在容器内安装
docker exec -it ruoyi-backend-dev pip install <package-name>

# 方式 2：更新 requirements.txt 后重新构建
cd ruoyi-fastapi-backend
echo "<package-name>" >> requirements.txt
docker-compose -f docker-compose.dev.yml build backend
docker-compose -f docker-compose.dev.yml up -d backend
```

## 故障排查 / Troubleshooting

### 端口被占用

```bash
# 查看端口占用
lsof -i :80
lsof -i :8000
lsof -i :3307

# 修改 docker-compose 文件中的端口映射
# 例如：将 "80:80" 改为 "8080:80"
```

### 容器无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.dev.yml logs backend

# 检查容器状态
docker-compose -f docker-compose.dev.yml ps

# 重新构建并启动
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

### 数据库连接失败

```bash
# 检查数据库是否就绪
docker exec ruoyi-mysql-dev mysqladmin ping -h localhost -uroot -proot

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs mysql

# 等待数据库完全启动（healthcheck）
docker-compose -f docker-compose.dev.yml ps
```

### 热更新不生效

**前端：**
- 检查文件是否正确挂载：`docker exec ruoyi-frontend-dev ls -la /app`
- 检查 Vite 配置中的 `server.watch` 选项
- 重启容器：`docker-compose -f docker-compose.dev.yml restart frontend`

**后端：**
- 检查 `APP_RELOAD=true` 环境变量
- 检查文件是否正确挂载：`docker exec ruoyi-backend-dev ls -la /app`
- 查看后端日志确认是否检测到文件变化

### 清理 Docker 资源

```bash
# 停止并删除容器、网络
docker-compose -f docker-compose.dev.yml down

# 删除所有数据卷（会丢失数据）
docker-compose -f docker-compose.dev.yml down -v

# 清理未使用的镜像
docker image prune -a

# 清理所有未使用的资源
docker system prune -a --volumes
```

## 性能优化 / Performance Optimization

### 开发环境

- 使用 `:cached` 挂载选项提高 macOS 性能
- 排除 `node_modules` 和 `__pycache__` 等目录
- 使用 `.dockerignore` 减少构建上下文

### 生产环境

- 多阶段构建减小镜像体积
- 资源限制防止单个服务占用过多资源
- 健康检查确保服务可用性
- 自动重启策略提高可靠性

## 环境变量 / Environment Variables

创建 `.env` 文件来自定义配置：

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=your_secure_password

# Redis 配置
REDIS_PASSWORD=your_redis_password

# 应用环境
APP_ENV=prod
```

## 注意事项 / Notes

1. **开发环境数据持久化**：开发环境的数据库和 Redis 数据存储在 Docker 卷中，删除卷会丢失数据
2. **生产环境安全**：生产环境请修改默认密码，使用 `.env` 文件管理敏感信息
3. **资源限制**：生产环境配置了资源限制，根据实际情况调整
4. **网络隔离**：开发和生产环境使用不同的 Docker 网络，可以同时运行
5. **日志管理**：生产环境建议配置日志轮转和集中日志收集

## 参考资料 / References

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Vite 服务器选项](https://vitejs.dev/config/server-options.html)
