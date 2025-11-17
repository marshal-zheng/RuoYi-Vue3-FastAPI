# 🚀 RuoYi-Vue3-FastAPI 快速启动指南

本项目提供了一键式自动化脚本，让小白用户能够快速搭建和启动整个开发环境。

## 📋 系统要求

- **操作系统**: macOS (脚本专为 macOS 优化)
- **网络**: 需要稳定的网络连接下载依赖
- **权限**: 需要管理员权限安装系统依赖

## 🎯 一键启动 (推荐)

### 首次使用

```bash
# 1. 克隆项目到本地
git clone <项目地址>
cd RuoYi-Vue3-FastAPI

# 2. 运行一键安装脚本
./setup.sh
```

**脚本会自动完成以下操作：**
- ✅ 检查并安装 Homebrew
- ✅ 安装系统依赖 (MySQL, Redis, Node.js, Python3)
- ✅ 启动并配置数据库服务
- ✅ 创建并导入项目数据库
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖到虚拟环境
- ✅ 安装前端依赖
- ✅ 询问是否立即启动项目

### 日常开发

环境配置完成后，日常开发只需运行：

```bash
./start.sh
```

## 📁 脚本说明

### `setup.sh` - 环境初始化脚本

**功能**: 完整的环境搭建，包括系统依赖安装和项目配置

**使用场景**: 
- 首次使用项目
- 重新配置开发环境
- 系统重装后恢复环境

**执行时间**: 约 10-30 分钟 (取决于网络速度)

### `start.sh` - 快速启动脚本

**功能**: 快速启动已配置好的开发环境

**使用场景**:
- 日常开发启动
- 环境已配置完成的情况

**执行时间**: 约 30 秒

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost:80
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: MySQL (localhost:3306)
- **缓存**: Redis (localhost:6379)

## 👤 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: MySQL 8.0+
- **缓存**: Redis 5.0+
- **ORM**: SQLAlchemy
- **环境**: Python 虚拟环境 (venv)

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **UI库**: Element Plus
- **包管理**: Yarn/NPM

## 🔧 手动操作 (高级用户)

如果你想手动配置环境，可以参考以下步骤：

### 1. 安装系统依赖

```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install mysql redis node python
```

### 2. 配置数据库

```bash
# 启动服务
brew services start mysql
brew services start redis

# 创建数据库
mysql -u root -e "CREATE DATABASE \`ruoyi-fastapi\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入数据
mysql -u root ruoyi-fastapi < ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

### 3. 配置后端

```bash
cd ruoyi-fastapi-backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python app.py
```

### 4. 配置前端

```bash
cd ruoyi-fastapi-frontend

# 安装依赖
yarn install  # 或 npm install

# 启动前端
yarn dev      # 或 npm run dev
```

## ❓ 常见问题

### Q: 脚本执行失败怎么办？

A: 检查以下几点：
1. 确保网络连接正常
2. 确保有管理员权限
3. 检查是否为 macOS 系统
4. 查看错误日志，根据提示解决

### Q: 端口被占用怎么办？

A: 检查端口占用情况：
```bash
# 检查端口占用
lsof -i :80    # 前端端口
lsof -i :8000  # 后端端口
lsof -i :3306  # MySQL端口
lsof -i :6379  # Redis端口

# 杀死占用进程
kill -9 <PID>
```

### Q: 数据库连接失败？

A: 尝试以下解决方案：
```bash
# 重启 MySQL 服务
brew services restart mysql

# 检查 MySQL 状态
brew services list | grep mysql

# 重新初始化数据库
mysqld --initialize-insecure
```

### Q: 虚拟环境相关问题？

A: 确保依赖安装在虚拟环境中：
```bash
cd ruoyi-fastapi-backend
source venv/bin/activate
pip list  # 查看已安装的包
```

## 🆘 获取帮助

如果遇到问题，请：
1. 查看脚本输出的错误信息
2. 检查系统日志
3. 参考本文档的常见问题部分
4. 联系项目维护者

## 📝 注意事项

1. **虚拟环境**: 所有 Python 依赖都安装在虚拟环境中，不会污染系统环境
2. **数据安全**: 脚本会创建新的数据库，不会影响现有数据
3. **端口冲突**: 确保相关端口未被占用
4. **网络要求**: 首次运行需要下载大量依赖，请确保网络稳定
5. **权限要求**: 安装系统依赖需要管理员权限

---

🎉 **祝你使用愉快！**
