#!/bin/bash

# RuoYi-Vue3-FastAPI 快速启动脚本
# 用于日常开发，假设环境已配置完成

set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
BACKEND_ENV_FILE="$PROJECT_ROOT/ruoyi-fastapi-backend/.env.dev"

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

DB_NAME="${DB_NAME:-$(read_backend_env_value DB_DATABASE 'ruoyi-fastapi')}"
if [ "${DB_USER+x}" != "x" ]; then
    DB_USER="$(read_backend_env_value DB_USERNAME 'root')"
fi
if [ "${DB_PASSWORD+x}" != "x" ]; then
    DB_PASSWORD="$(read_backend_env_value DB_PASSWORD 'admin1234')"
fi
DB_HOST="${DB_HOST:-$(read_backend_env_value DB_HOST '127.0.0.1')}"
DB_PORT="${DB_PORT:-$(read_backend_env_value DB_PORT '3306')}"
APP_PORT="${APP_PORT:-$(read_backend_env_value APP_PORT '8088')}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"

BACKEND_PID=''
FRONTEND_PID=''
BACKEND_REUSED=false
FRONTEND_REUSED=false

mysql_exec() {
    if [ -n "$DB_PASSWORD" ]; then
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$@"
    else
        mysql -u "$DB_USER" "$@"
    fi
}

mysql_tcp_exec() {
    if [ -n "$DB_PASSWORD" ]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$@"
    else
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$@"
    fi
}

extract_status_field() {
    local status_output="$1"
    local field_name="$2"
    printf '%s\n' "$status_output" | sed -n "s/^${field_name}=//p" | head -n 1
}

listening_port_pids() {
    local port="$1"
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

first_listening_port_pid() {
    local port="$1"
    listening_port_pids "$port" | head -n 1
}

pid_command() {
    local pid="$1"
    ps -p "$pid" -o command= 2>/dev/null | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

pid_cwd() {
    local pid="$1"
    lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
}

is_pid_running() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

is_backend_process_for_repo() {
    local pid="$1"
    local command_line
    local current_dir
    command_line="$(pid_command "$pid")"
    current_dir="$(pid_cwd "$pid")"
    [ -n "$command_line" ] || return 1
    if [ "$current_dir" = "$PROJECT_ROOT/ruoyi-fastapi-backend" ]; then
        [[ "$command_line" == *'app.py'* || "$command_line" == *'uvicorn'* || "$command_line" == *'Python app.py'* ]]
        return $?
    fi
    [[ "$command_line" == *"$PROJECT_ROOT/ruoyi-fastapi-backend"* ]] || return 1
    [[ "$command_line" == *'app.py'* || "$command_line" == *'uvicorn'* ]]
}

is_frontend_process_for_repo() {
    local pid="$1"
    local command_line
    local current_dir
    command_line="$(pid_command "$pid")"
    current_dir="$(pid_cwd "$pid")"
    [ -n "$command_line" ] || return 1
    if [ "$current_dir" = "$PROJECT_ROOT/ruoyi-fastapi-frontend" ]; then
        [[ "$command_line" == *'vite'* || "$command_line" == *'node '* ]]
        return $?
    fi
    [[ "$command_line" == *"$PROJECT_ROOT/ruoyi-fastapi-frontend"* ]] || return 1
    [[ "$command_line" == *'vite'* ]]
}

wait_for_listener_or_exit() {
    local pid="$1"
    local port="$2"
    local timeout_seconds="$3"
    local attempt=1

    while [ "$attempt" -le "$timeout_seconds" ]; do
        if [ -n "$(first_listening_port_pid "$port")" ]; then
            return 0
        fi
        if ! is_pid_running "$pid"; then
            return 1
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    return 1
}

run_workflow_python_command() {
    local base_command="$1"
    local extra_args="$2"
    local full_command="$base_command"
    if [ -n "$extra_args" ]; then
        full_command="$full_command $extra_args"
    fi
    eval "$full_command"
}

run_backend_db_workflow() {
    local workflow_status
    local workflow_mode
    local startup_action
    local dev_sync_path
    local deploy_path

    echo -e "${BLUE}🗃️ 检查数据库工作流状态...${NC}"
    if ! workflow_status="$(python scripts/db.py status)"; then
        echo -e "${RED}❌ 读取数据库工作流状态失败${NC}"
        exit 1
    fi

    printf '%s\n' "$workflow_status"

    workflow_mode="$(extract_status_field "$workflow_status" "workflow_mode")"
    startup_action="$(extract_status_field "$workflow_status" "startup_action")"
    dev_sync_path="$(extract_status_field "$workflow_status" "dev_sync_path")"
    deploy_path="$(extract_status_field "$workflow_status" "deploy_path")"

    if [ -z "$workflow_mode" ]; then
        echo -e "${RED}❌ 无法解析 workflow_mode，请检查 scripts/db.py status 输出${NC}"
        exit 1
    fi
    if [ -z "$startup_action" ]; then
        echo -e "${RED}❌ 无法解析 startup_action，请检查 scripts/db.py status 输出${NC}"
        exit 1
    fi

    case "$startup_action" in
        dev-sync)
            if [ -z "$dev_sync_path" ]; then
                echo -e "${RED}❌ 无法解析 dev_sync_path，请检查 scripts/db.py status 输出${NC}"
                exit 1
            fi
            echo -e "${BLUE}🗃️ 当前为 ${workflow_mode} 模式，启动前执行统一 dev-sync...${NC}"
            if ! run_workflow_python_command "$dev_sync_path" "--invoked-by-startup"; then
                echo -e "${RED}❌ 启动前 dev-sync 执行失败，请检查声明文件、Atlas/provider 或数据库连接配置${NC}"
                exit 1
            fi
            echo -e "${GREEN}✅ 启动前统一 dev-sync 执行完成${NC}"
            ;;
        deploy)
            if [ -z "$deploy_path" ]; then
                echo -e "${RED}❌ 无法解析 deploy_path，请检查 scripts/db.py status 输出${NC}"
                exit 1
            fi
            echo -e "${BLUE}🗃️ 当前为 ${workflow_mode} 模式，执行正式迁移 deploy --revision head...${NC}"
            if ! run_workflow_python_command "$deploy_path" ""; then
                echo -e "${RED}❌ 正式迁移执行失败，请检查数据库连接与 Alembic 迁移链${NC}"
                exit 1
            fi
            echo -e "${GREEN}✅ 正式迁移执行完成${NC}"
            ;;
        *)
            echo -e "${RED}❌ 不支持的启动工作流动作：$startup_action${NC}"
            exit 1
            ;;
    esac
}

echo "🚀 启动 RuoYi-Vue3-FastAPI 项目"
echo "=============================="
echo "项目目录: $PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 兼容旧菜单热同步环境变量，但统一工作流已接管开发态生效路径
LEGACY_DEV_MENU_SYNC="${DEV_MENU_SYNC:-false}"
LEGACY_VITE_DEV_MENU_SYNC="${VITE_DEV_MENU_SYNC:-0}"
LEGACY_VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS="${VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS:-1000}"
export DEV_MENU_SYNC=false
export VITE_DEV_MENU_SYNC=0
export VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS=0

echo -e "${BLUE}🧭 统一数据库工作流已接管开发态同步；旧菜单热同步开关仅保留兼容占位${NC}"
echo -e "${BLUE}   ↪ 兼容占位: DEV_MENU_SYNC=${LEGACY_DEV_MENU_SYNC}, VITE_DEV_MENU_SYNC=${LEGACY_VITE_DEV_MENU_SYNC}, 旧轮询=${LEGACY_VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS}ms${NC}"

# 检查并启动系统服务
echo -e "${BLUE}🔍 检查系统服务...${NC}"

# 启动 MySQL
if ! brew services list | grep mysql | grep -q started; then
    echo -e "${YELLOW}🚀 启动 MySQL...${NC}"
    brew services start mysql
    sleep 2
else
    echo -e "${GREEN}✅ MySQL 已运行${NC}"
fi

# 启动 Redis
if ! brew services list | grep redis | grep -q started; then
    echo -e "${YELLOW}🚀 启动 Redis...${NC}"
    brew services start redis
    sleep 2
else
    echo -e "${GREEN}✅ Redis 已运行${NC}"
fi

# 验证数据库连接
echo -e "${BLUE}🔍 验证数据库连接...${NC}"
if ! mysql_tcp_exec -e "USE \`$DB_NAME\`; SELECT 1;" &> /dev/null; then
    echo -e "${RED}❌ 数据库 TCP 连接失败：${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}${NC}"
    echo -e "${YELLOW}   ↪ start.sh 现在按后端真实连接方式校验，避免 socket 通过但 dev-sync 失败${NC}"
    echo -e "${YELLOW}   ↪ 如刚升级脚本，请先重新运行 ./scripts/setup.sh 以补齐 root@127.0.0.1 等本地 TCP 账号${NC}"
    exit 1
fi

# 验证 Redis 连接
if ! redis-cli ping | grep -q PONG; then
    echo -e "${RED}❌ Redis 连接失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 所有服务正常${NC}"

# 启动后端服务
echo -e "${BLUE}🐍 启动后端服务...${NC}"
cd "$PROJECT_ROOT/ruoyi-fastapi-backend"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先运行 ./scripts/setup.sh${NC}"
    exit 1
fi

# 激活虚拟环境并启动后端
source venv/bin/activate

run_backend_db_workflow

EXISTING_BACKEND_PID="$(first_listening_port_pid "$APP_PORT")"
if [ -n "$EXISTING_BACKEND_PID" ]; then
    EXISTING_BACKEND_COMMAND="$(pid_command "$EXISTING_BACKEND_PID")"
    if is_backend_process_for_repo "$EXISTING_BACKEND_PID"; then
        BACKEND_REUSED=true
        echo -e "${YELLOW}♻️ 检测到已有后端实例，复用端口 ${APP_PORT} (PID: $EXISTING_BACKEND_PID)${NC}"
    else
        echo -e "${RED}❌ 后端端口 ${APP_PORT} 已被其他进程占用 (PID: $EXISTING_BACKEND_PID)${NC}"
        if [ -n "$EXISTING_BACKEND_COMMAND" ]; then
            echo -e "${YELLOW}   ↪ 占用命令: ${EXISTING_BACKEND_COMMAND}${NC}"
        fi
        exit 1
    fi
else
    python app.py &
    BACKEND_PID=$!
    if ! wait_for_listener_or_exit "$BACKEND_PID" "$APP_PORT" 15; then
        echo -e "${RED}❌ 后端服务启动失败，端口 ${APP_PORT} 未进入监听状态${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID, Port: $APP_PORT)${NC}"
fi
cd "$PROJECT_ROOT"

# 启动前端服务
echo -e "${BLUE}🎨 启动前端服务...${NC}"
cd "$PROJECT_ROOT/ruoyi-fastapi-frontend"

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${RED}❌ 前端依赖未安装，请先运行 ./scripts/setup.sh${NC}"
    exit 1
fi

EXISTING_FRONTEND_PID="$(first_listening_port_pid "$FRONTEND_PORT")"
if [ -n "$EXISTING_FRONTEND_PID" ]; then
    EXISTING_FRONTEND_COMMAND="$(pid_command "$EXISTING_FRONTEND_PID")"
    if is_frontend_process_for_repo "$EXISTING_FRONTEND_PID"; then
        FRONTEND_REUSED=true
        echo -e "${YELLOW}♻️ 检测到已有前端实例，复用端口 ${FRONTEND_PORT} (PID: $EXISTING_FRONTEND_PID)${NC}"
    else
        echo -e "${RED}❌ 前端端口 ${FRONTEND_PORT} 已被其他进程占用 (PID: $EXISTING_FRONTEND_PID)${NC}"
        if [ -n "$EXISTING_FRONTEND_COMMAND" ]; then
            echo -e "${YELLOW}   ↪ 占用命令: ${EXISTING_FRONTEND_COMMAND}${NC}"
        fi
        exit 1
    fi
else
    ./node_modules/.bin/vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort &
    FRONTEND_PID=$!
    if ! wait_for_listener_or_exit "$FRONTEND_PID" "$FRONTEND_PORT" 15; then
        echo -e "${RED}❌ 前端服务启动失败，端口 ${FRONTEND_PORT} 未进入监听状态${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)${NC}"
fi
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}🎉 项目启动完成！${NC}"
echo -e "${BLUE}📋 访问地址：${NC}"
echo -e "  • 前端: ${YELLOW}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  • 后端: ${YELLOW}http://localhost:${APP_PORT}${NC}"
echo -e "  • API文档: ${YELLOW}http://localhost:${APP_PORT}/docs${NC}"
if [ "$BACKEND_REUSED" = true ] || [ "$FRONTEND_REUSED" = true ]; then
    echo ""
    echo -e "${YELLOW}♻️ 已复用现有实例；按 Ctrl+C 只会停止本次脚本新启动的进程${NC}"
fi
echo ""
echo -e "${BLUE}👤 默认账号：${NC}"
echo -e "  • 用户名: ${YELLOW}admin${NC}"
echo -e "  • 密码: ${YELLOW}admin123${NC}"
echo ""
if [ -n "$BACKEND_PID" ] || [ -n "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}💡 按 Ctrl+C 停止所有服务${NC}"
    echo ""
else
    echo -e "${YELLOW}💡 本次仅复用已有实例，脚本现在退出；如需停止服务请结束对应现有进程${NC}"
    echo ""
    exit 0
fi

# 创建停止函数
stop_services() {
    echo -e "\n${YELLOW}🛑 正在停止服务...${NC}"
    
    # 停止后端和前端进程
    if [ -n "$BACKEND_PID" ] && [ "$BACKEND_REUSED" != true ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
    
    if [ -n "$FRONTEND_PID" ] && [ "$FRONTEND_REUSED" != true ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    fi
    
    echo -e "${GREEN}🎉 所有服务已停止${NC}"
    exit 0
}

# 设置信号处理
trap stop_services INT TERM

# 等待用户中断
wait
