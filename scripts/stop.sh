#!/bin/bash

set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
BACKEND_ENV_FILE="$PROJECT_ROOT/ruoyi-fastapi-backend/.env.dev"
STOP_TIMEOUT_SECONDS="${STOP_TIMEOUT_SECONDS:-10}"

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

APP_PORT="${APP_PORT:-$(read_backend_env_value APP_PORT '8088')}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"

listening_port_pids() {
    local port="$1"
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

pid_command() {
    local pid="$1"
    ps -p "$pid" -o command= 2>/dev/null | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

pid_cwd() {
    local pid="$1"
    lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
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

find_repo_backend_pid() {
    local pid
    for pid in $(listening_port_pids "$APP_PORT"); do
        if is_backend_process_for_repo "$pid"; then
            printf '%s\n' "$pid"
            return
        fi
    done
}

find_repo_frontend_pid() {
    local pid
    for pid in $(listening_port_pids "$FRONTEND_PORT"); do
        if is_frontend_process_for_repo "$pid"; then
            printf '%s\n' "$pid"
            return
        fi
    done
}

wait_for_process_stop() {
    local pid="$1"
    local timeout_seconds="$2"
    local attempt=1

    while [ "$attempt" -le "$timeout_seconds" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    return 1
}

stop_repo_process() {
    local pid="$1"
    local label="$2"

    kill -TERM "$pid" 2>/dev/null || true
    if wait_for_process_stop "$pid" "$STOP_TIMEOUT_SECONDS"; then
        printf '✅ 已停止%s (PID: %s)\n' "$label" "$pid"
        return 0
    fi

    printf '❌ %s停止超时，请手动处理 (PID: %s)\n' "$label" "$pid" >&2
    return 1
}

echo '🛑 停止 RuoYi-Vue3-FastAPI 开发服务'
echo '==================================='

STOPPED_ANY=false

BACKEND_PID="$(find_repo_backend_pid)"
if [ -n "$BACKEND_PID" ]; then
    stop_repo_process "$BACKEND_PID" '后端服务'
    STOPPED_ANY=true
else
    echo "ℹ️ 未发现可停止的后端实例（端口 ${APP_PORT}）"
fi

FRONTEND_PID="$(find_repo_frontend_pid)"
if [ -n "$FRONTEND_PID" ]; then
    stop_repo_process "$FRONTEND_PID" '前端服务'
    STOPPED_ANY=true
else
    echo "ℹ️ 未发现可停止的前端实例（端口 ${FRONTEND_PORT}）"
fi

if [ "$STOPPED_ANY" = false ]; then
    echo 'ℹ️ 当前没有由本仓库 start.sh 管理的前后端实例在运行'
fi

echo '💡 默认不会停止 MySQL / Redis；如需扩展，再补独立参数即可'
