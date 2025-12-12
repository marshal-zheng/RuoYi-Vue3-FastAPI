#!/bin/bash

# RuoYi-Vue3-FastAPI 一键启动脚本
# 适用于 macOS 系统

set -e  # 遇到错误立即退出

# 切换到项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

SQL_ROOT="$PROJECT_ROOT/ruoyi-fastapi-backend/sql"
SQL_INIT_FILE="$SQL_ROOT/ruoyi-fastapi.sql"
DB_NAME="${DB_NAME:-ruoyi-fastapi}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"

mysql_exec() {
    if [ -n "$DB_PASSWORD" ]; then
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$@"
    else
        mysql -u "$DB_USER" "$@"
    fi
}

apply_sql_updates() {
    if [ ! -d "$SQL_ROOT" ]; then
        echo -e "${YELLOW}⚠️  SQL 目录不存在：$SQL_ROOT${NC}"
        return
    fi

    sql_found=false

    while IFS= read -r sql_file; do
        sql_found=true
        rel_path=${sql_file#"$SQL_ROOT/"}
        echo -e "${BLUE}   ↪ ${rel_path}${NC}"
        mysql_exec "$DB_NAME" < "$sql_file"
    done < <(find "$SQL_ROOT" -maxdepth 1 -type f -name "*.sql" ! -name "ruoyi-fastapi*.sql" | sort)

    if [ "$sql_found" = false ]; then
        echo -e "${YELLOW}ℹ️  未检测到需要执行的增量 SQL 脚本${NC}"
        return
    fi

    echo -e "${GREEN}✅ 增量 SQL 执行完成${NC}"
}

echo "🚀 RuoYi-Vue3-FastAPI 一键启动脚本"
echo "======================================"
echo "项目目录: $PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为 macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ 此脚本仅支持 macOS 系统${NC}"
    exit 1
fi

# 检查 Homebrew
echo -e "${BLUE}📦 检查 Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew 未安装，正在安装...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}✅ Homebrew 已安装${NC}"
fi

# 检查并安装系统依赖
echo -e "${BLUE}🔧 检查系统依赖...${NC}"

# 检查 MySQL
if ! brew list mysql &> /dev/null; then
    echo -e "${YELLOW}📥 安装 MySQL...${NC}"
    brew install mysql
else
    echo -e "${GREEN}✅ MySQL 已安装${NC}"
fi

# 检查 Redis
if ! brew list redis &> /dev/null; then
    echo -e "${YELLOW}📥 安装 Redis...${NC}"
    brew install redis
else
    echo -e "${GREEN}✅ Redis 已安装${NC}"
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}📥 安装 Node.js...${NC}"
    brew install node
else
    echo -e "${GREEN}✅ Node.js 已安装${NC}"
fi

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}📥 安装 Python3...${NC}"
    brew install python
else
    echo -e "${GREEN}✅ Python3 已安装${NC}"
fi

# 启动服务
echo -e "${BLUE}🚀 启动系统服务...${NC}"
brew services start mysql
brew services start redis

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查 MySQL 连接
echo -e "${BLUE}🔍 检查 MySQL 连接...${NC}"
if ! mysql_exec -e "SELECT 1" &> /dev/null; then
    echo -e "${YELLOW}⚙️  初始化 MySQL...${NC}"
    mysqld --initialize-insecure
    brew services restart mysql
    sleep 5
fi

# 创建数据库
echo -e "${BLUE}🗄️  配置数据库...${NC}"
mysql_exec -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入数据
if [ -f "$SQL_INIT_FILE" ]; then
    echo -e "${BLUE}📊 导入数据库数据...${NC}"
    mysql_exec "$DB_NAME" < "$SQL_INIT_FILE"
    echo -e "${GREEN}✅ 数据库数据导入完成${NC}"
else
    echo -e "${RED}❌ 数据库文件不存在${NC}"
    exit 1
fi

apply_sql_updates

# 验证 Redis 连接
echo -e "${BLUE}🔍 检查 Redis 连接...${NC}"
if redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis 连接正常${NC}"
else
    echo -e "${RED}❌ Redis 连接失败${NC}"
    exit 1
fi

# 设置后端环境
echo -e "${BLUE}🐍 配置后端环境...${NC}"
cd "$PROJECT_ROOT/ruoyi-fastapi-backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 创建 Python 虚拟环境...${NC}"
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo -e "${BLUE}📥 安装后端依赖...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ 后端依赖安装完成${NC}"

# 配置后端数据库连接
echo -e "${BLUE}⚙️  配置后端数据库连接...${NC}"
if [ -f ".env.dev" ]; then
    # 修改数据库密码为空（因为我们初始化MySQL时没有设置密码）
    sed -i '' "s/DB_PASSWORD = 'mysqlroot'/DB_PASSWORD = ''/g" .env.dev
    # 修改后端端口为8000（与前端代理配置一致）
    sed -i '' "s/APP_PORT = 9099/APP_PORT = 8000/g" .env.dev
    echo -e "${GREEN}✅ 后端配置已更新${NC}"
else
    echo -e "${RED}❌ 后端配置文件不存在${NC}"
    exit 1
fi

# 返回项目根目录
cd "$PROJECT_ROOT"

# 设置前端环境
echo -e "${BLUE}🎨 配置前端环境...${NC}"
cd "$PROJECT_ROOT/ruoyi-fastapi-frontend"

# 修正前端代理配置
echo -e "${BLUE}⚙️  配置前端代理...${NC}"
if [ -f "vite.config.js" ]; then
    # 修改代理端口为8000
    sed -i '' "s/target: 'http:\/\/127.0.0.1:9099'/target: 'http:\/\/127.0.0.1:8000'/g" vite.config.js
    echo -e "${GREEN}✅ 前端代理配置已更新${NC}"
fi

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📥 安装前端依赖...${NC}"
    if command -v yarn &> /dev/null; then
        yarn install
    else
        npm install
    fi
else
    echo -e "${GREEN}✅ 前端依赖已安装${NC}"
fi

# 返回项目根目录
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}🎉 环境配置完成！${NC}"
echo -e "${BLUE}📋 使用说明：${NC}"
echo -e "  • 运行 ${YELLOW}./scripts/start.sh${NC} 启动项目"
echo -e "  • 前端地址: ${YELLOW}http://localhost:80${NC}"
echo -e "  • 后端地址: ${YELLOW}http://localhost:8000${NC}"
echo -e "  • 默认账号: ${YELLOW}admin${NC} 密码: ${YELLOW}admin123${NC}"
echo ""
echo -e "${YELLOW}💡 提示: 首次运行可能需要等待几分钟来下载依赖${NC}"
echo ""

# 询问是否立即启动
read -p "是否现在启动项目？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$PROJECT_ROOT/scripts/start.sh"
fi
