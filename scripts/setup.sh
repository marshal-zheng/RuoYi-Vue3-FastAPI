#!/bin/bash

# RuoYi-Vue3-FastAPI 一键初始化脚本
# 适用于 macOS，本脚本应保持可重复执行

set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
BACKEND_ROOT="$PROJECT_ROOT/ruoyi-fastapi-backend"
FRONTEND_ROOT="$PROJECT_ROOT/ruoyi-fastapi-frontend"
BACKEND_ENV_FILE="$BACKEND_ROOT/.env.dev"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

read_backend_env_value() {
    local key="$1"
    local default_value="$2"

    if [ ! -f "$BACKEND_ENV_FILE" ]; then
        printf '%s\n' "$default_value"
        return
    fi

    local raw_line
    raw_line="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$BACKEND_ENV_FILE" | tail -n 1 || true)"
    if [ -z "$raw_line" ]; then
        printf '%s\n' "$default_value"
        return
    fi

    raw_line="${raw_line#*=}"
    raw_line="$(printf '%s' "$raw_line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    raw_line="${raw_line#\'}"
    raw_line="${raw_line%\'}"
    raw_line="${raw_line#\"}"
    raw_line="${raw_line%\"}"
    printf '%s\n' "$raw_line"
}

write_backend_env_value() {
    local key="$1"
    local value="$2"
    local escaped_value
    escaped_value="$(printf '%s' "$value" | sed -e 's/[\/&]/\\&/g')"

    if [ ! -f "$BACKEND_ENV_FILE" ]; then
        return
    fi

    if grep -Eq "^[[:space:]]*${key}[[:space:]]*=" "$BACKEND_ENV_FILE"; then
        sed -i '' -E "s|^[[:space:]]*${key}[[:space:]]*=.*$|${key} = '${escaped_value}'|" "$BACKEND_ENV_FILE"
    else
        printf "\n%s = '%s'\n" "$key" "$value" >> "$BACKEND_ENV_FILE"
    fi
}

DB_NAME="${DB_NAME:-$(read_backend_env_value DB_DATABASE 'ruoyi-fastapi')}"
DB_USER="${DB_USER:-$(read_backend_env_value DB_USERNAME 'root')}"
DB_PASSWORD="${DB_PASSWORD:-$(read_backend_env_value DB_PASSWORD 'admin1234')}"
DB_HOST="${DB_HOST:-$(read_backend_env_value DB_HOST '127.0.0.1')}"
DB_PORT="${DB_PORT:-$(read_backend_env_value DB_PORT '3306')}"
DB_WORKFLOW_MODE="${DB_WORKFLOW_MODE:-$(read_backend_env_value DB_WORKFLOW_MODE 'development')}"
APP_PORT="${APP_PORT:-$(read_backend_env_value APP_PORT '8088')}"
MYSQL_ACTIVE_PASSWORD="$DB_PASSWORD"

mysql_exec_with_password() {
    local password="$1"
    shift
    if [ -n "$password" ]; then
        MYSQL_PWD="$password" mysql -u "$DB_USER" "$@"
    else
        mysql -u "$DB_USER" "$@"
    fi
}

mysql_exec() {
    mysql_exec_with_password "$MYSQL_ACTIVE_PASSWORD" "$@"
}

mysql_tcp_exec_with_password() {
    local password="$1"
    shift
    if [ -n "$password" ]; then
        MYSQL_PWD="$password" mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$@"
    else
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$@"
    fi
}

mysql_tcp_exec() {
    mysql_tcp_exec_with_password "$MYSQL_ACTIVE_PASSWORD" "$@"
}

wait_for_mysql_login() {
    local password="$1"
    local attempts="${2:-20}"

    while [ "$attempts" -gt 0 ]; do
        if mysql_exec_with_password "$password" -e 'SELECT 1' >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempts=$((attempts - 1))
    done

    return 1
}

wait_for_mysql_tcp_login() {
    local password="$1"
    local attempts="${2:-20}"

    while [ "$attempts" -gt 0 ]; do
        if mysql_tcp_exec_with_password "$password" -e 'SELECT 1' >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempts=$((attempts - 1))
    done

    return 1
}

mysql_data_dir() {
    printf '%s/var/mysql' "$(brew --prefix)"
}

mysql_datadir_initialized() {
    local data_dir
    data_dir="$(mysql_data_dir)"

    [ -d "$data_dir" ] || return 1
    [ -n "$(find "$data_dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]
}

initialize_mysql_datadir() {
    local data_dir
    data_dir="$(mysql_data_dir)"

    mkdir -p "$data_dir"
    mysqld --initialize-insecure --user="$(id -un)" --datadir="$data_dir"
}

sql_escape() {
    printf '%s' "$1" | sed "s/'/''/g"
}

ensure_mysql_root_access() {
    local current_password="$1"
    local target_password="$2"
    local escaped_password
    escaped_password="$(sql_escape "$target_password")"

    if [ "$DB_USER" != 'root' ]; then
        return 0
    fi

    local statement=""
    if [ -n "$target_password" ]; then
        statement="ALTER USER 'root'@'localhost' IDENTIFIED BY '${escaped_password}'; "
    fi
    statement="${statement}CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '${escaped_password}'; "
    statement="${statement}ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '${escaped_password}'; "
    statement="${statement}GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION; "
    statement="${statement}FLUSH PRIVILEGES;"

    mysql_exec_with_password "$current_password" -e "$statement"
}

install_brew_formula() {
    local binary_name="$1"
    local formula_name="$2"

    if command -v "$binary_name" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ${formula_name} 已安装${NC}"
        return
    fi

    echo -e "${YELLOW}📥 安装 ${formula_name}...${NC}"
    brew install "$formula_name"
}

echo "🚀 RuoYi-Vue3-FastAPI 一键初始化脚本"
echo "======================================"
echo "项目目录: $PROJECT_ROOT"

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ 此脚本仅支持 macOS 系统${NC}"
    exit 1
fi

echo -e "${BLUE}📦 检查 Homebrew...${NC}"
if ! command -v brew >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Homebrew 未安装，正在安装...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}✅ Homebrew 已安装${NC}"
fi

echo -e "${BLUE}🔧 检查系统依赖...${NC}"
install_brew_formula mysql mysql
install_brew_formula redis redis
install_brew_formula node node
install_brew_formula python3 python
if [ "$DB_WORKFLOW_MODE" = 'development' ]; then
    install_brew_formula atlas atlas
fi

echo -e "${BLUE}🚀 启动系统服务...${NC}"
brew services start mysql
brew services start redis

echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 3

echo -e "${BLUE}🔍 检查 MySQL 连接...${NC}"
if wait_for_mysql_login "$DB_PASSWORD" 8; then
    MYSQL_ACTIVE_PASSWORD="$DB_PASSWORD"
    echo -e "${GREEN}✅ MySQL 已使用当前配置连接成功${NC}"
else
    if wait_for_mysql_login '' 8; then
        echo -e "${YELLOW}ℹ️  检测到本机 MySQL root 当前为空密码${NC}"
        MYSQL_ACTIVE_PASSWORD=''
        if [ "$DB_USER" = 'root' ] && [ -n "$DB_PASSWORD" ]; then
            echo -e "${BLUE}⚙️  对齐 root 本地密码与后端配置，并补齐 127.0.0.1 访问账号...${NC}"
            ensure_mysql_root_access '' "$DB_PASSWORD"
            MYSQL_ACTIVE_PASSWORD="$DB_PASSWORD"
        fi
    else
        if mysql_datadir_initialized; then
            echo -e "${RED}❌ MySQL 数据目录已存在，但当前凭据无法登录${NC}"
            echo -e "${YELLOW}   ↪ 当前脚本使用 DB_USER=${DB_USER}，请检查 ${BACKEND_ENV_FILE} 中的 DB_USERNAME/DB_PASSWORD${NC}"
            echo -e "${YELLOW}   ↪ 或在执行前导出正确的 DB_USER/DB_PASSWORD 后重试${NC}"
            exit 1
        fi

        echo -e "${YELLOW}⚙️  检测到 MySQL 数据目录尚未初始化，开始初始化...${NC}"
        brew services stop mysql >/dev/null 2>&1 || true
        initialize_mysql_datadir
        brew services start mysql

        if ! wait_for_mysql_login '' 20; then
            echo -e "${RED}❌ MySQL 初始化后仍无法连接，请检查 brew services logs mysql${NC}"
            exit 1
        fi

        MYSQL_ACTIVE_PASSWORD=''
        if [ "$DB_USER" = 'root' ]; then
            echo -e "${BLUE}⚙️  配置 root 本地密码与 127.0.0.1 访问账号...${NC}"
            ensure_mysql_root_access '' "$DB_PASSWORD"
            MYSQL_ACTIVE_PASSWORD="$DB_PASSWORD"
        fi
    fi
fi

if [ "$DB_USER" = 'root' ]; then
    ensure_mysql_root_access "$MYSQL_ACTIVE_PASSWORD" "$MYSQL_ACTIVE_PASSWORD"
fi

write_backend_env_value DB_USERNAME "$DB_USER"
write_backend_env_value DB_PASSWORD "$MYSQL_ACTIVE_PASSWORD"
write_backend_env_value DB_DATABASE "$DB_NAME"

export DB_USERNAME="$DB_USER"
export DB_PASSWORD="$MYSQL_ACTIVE_PASSWORD"
export DB_DATABASE="$DB_NAME"
export DB_WORKFLOW_MODE="$DB_WORKFLOW_MODE"

echo -e "${BLUE}🗄️  配置数据库...${NC}"
mysql_exec -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo -e "${GREEN}✅ 数据库 ${DB_NAME} 已就绪${NC}"

echo -e "${BLUE}🔍 验证后端将使用的数据库 TCP 连接...${NC}"
if ! wait_for_mysql_tcp_login "$MYSQL_ACTIVE_PASSWORD" 8; then
    echo -e "${RED}❌ 后端数据库 TCP 连接失败：${DB_USER}@${DB_HOST}:${DB_PORT}${NC}"
    echo -e "${YELLOW}   ↪ MySQL CLI 可能能通过本地 socket 登录，但后端 dev-sync/deploy 走的是 TCP${NC}"
    echo -e "${YELLOW}   ↪ 请检查 MySQL 用户授权，确保 ${DB_USER}@127.0.0.1 可用${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端数据库 TCP 连接正常${NC}"

echo -e "${BLUE}🔍 检查 Redis 连接...${NC}"
if redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis 连接正常${NC}"
else
    echo -e "${RED}❌ Redis 连接失败${NC}"
    exit 1
fi

echo -e "${BLUE}🐍 配置后端环境...${NC}"
cd "$BACKEND_ROOT"

if [ ! -d 'venv' ]; then
    echo -e "${YELLOW}📦 创建 Python 虚拟环境...${NC}"
    python3 -m venv venv
fi

echo -e "${BLUE}📥 安装后端依赖...${NC}"
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ 后端依赖安装完成${NC}"

echo -e "${BLUE}🗃️  执行统一数据库初始化工作流...${NC}"
python scripts/db.py wait-db
python scripts/db.py deploy --revision head
python scripts/db.py bootstrap-seed --env dev
if [ "$DB_WORKFLOW_MODE" = 'development' ]; then
    python scripts/db.py dev-sync
fi
echo -e "${GREEN}✅ 数据库工作流初始化完成${NC}"

deactivate

echo -e "${BLUE}🎨 配置前端环境...${NC}"
cd "$FRONTEND_ROOT"

if [ ! -d 'node_modules' ]; then
    echo -e "${BLUE}📥 安装前端依赖...${NC}"
    if command -v yarn >/dev/null 2>&1; then
        yarn install
    else
        npm install
    fi
else
    echo -e "${GREEN}✅ 前端依赖已安装${NC}"
fi

cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}🎉 环境配置完成！${NC}"
echo -e "${BLUE}📋 使用说明：${NC}"
echo -e "  • 运行 ${YELLOW}./scripts/start.sh${NC} 启动项目"
echo -e "  • 前端地址: ${YELLOW}http://localhost:80${NC}"
echo -e "  • 后端地址: ${YELLOW}http://localhost:${APP_PORT}${NC}"
echo -e "  • 默认账号: ${YELLOW}admin${NC} 密码: ${YELLOW}admin123${NC}"
echo ""
echo -e "${YELLOW}💡 提示: 再次执行本脚本会走幂等流程，不会再尝试重新初始化已有 MySQL 数据目录${NC}"
echo ""

read -p "是否现在启动项目？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$PROJECT_ROOT/scripts/start.sh"
fi
