#!/bin/bash

# RuoYi-Vue3-FastAPI 快速启动脚本
# 用于日常开发，假设环境已配置完成

set -e

SQL_DIR="ruoyi-fastapi-backend/sql"
DB_NAME="${DB_NAME:-ruoyi-fastapi}"
if [ "${DB_USER+x}" != "x" ]; then
    DB_USER="root"
fi
if [ "${DB_PASSWORD+x}" != "x" ]; then
    DB_PASSWORD="admin1234"
fi

mysql_exec() {
    if [ -n "$DB_PASSWORD" ]; then
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$@"
    else
        mysql -u "$DB_USER" "$@"
    fi
}

apply_sql_updates() {
    if [ ! -d "$SQL_DIR" ]; then
        echo -e "${YELLOW}⚠️  SQL 目录不存在：$SQL_DIR${NC}"
        return
    fi

    sql_found=false

    while IFS= read -r sql_file; do
        sql_found=true
        if [[ $(basename "$sql_file") == *"-pg.sql" ]]; then
            continue
        fi
        echo -e "${BLUE}   ↪ $(basename "$sql_file")${NC}"
        mysql_exec "$DB_NAME" < "$sql_file"
    done < <(find "$SQL_DIR" -maxdepth 1 -type f -name "update_*.sql" | sort)

    if [ "$sql_found" = false ]; then
        echo -e "${YELLOW}ℹ️  未检测到需要执行的增量 SQL 脚本${NC}"
        return
    fi

    echo -e "${GREEN}✅ 增量 SQL 执行完成${NC}"
}

echo "🚀 启动 RuoYi-Vue3-FastAPI 项目"
echo "=============================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
if ! mysql_exec -e "USE \`$DB_NAME\`; SELECT 1;" &> /dev/null; then
    echo -e "${RED}❌ 数据库连接失败，请先运行 ./setup.sh${NC}"
    exit 1
fi

apply_sql_updates

# 验证 Redis 连接
if ! redis-cli ping | grep -q PONG; then
    echo -e "${RED}❌ Redis 连接失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 所有服务正常${NC}"

# 启动后端服务
echo -e "${BLUE}🐍 启动后端服务...${NC}"
cd ruoyi-fastapi-backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先运行 ./setup.sh${NC}"
    exit 1
fi

# 激活虚拟环境并启动后端
source venv/bin/activate
python app.py &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
cd ..

# 等待后端启动
echo -e "${YELLOW}⏳ 等待后端服务启动...${NC}"
sleep 5

# 启动前端服务
echo -e "${BLUE}🎨 启动前端服务...${NC}"
cd ruoyi-fastapi-frontend

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${RED}❌ 前端依赖未安装，请先运行 ./setup.sh${NC}"
    exit 1
fi

# 启动前端
if command -v yarn &> /dev/null; then
    yarn dev &
else
    npm run dev &
fi
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
cd ..

echo ""
echo -e "${GREEN}🎉 项目启动完成！${NC}"
echo -e "${BLUE}📋 访问地址：${NC}"
echo -e "  • 前端: ${YELLOW}http://localhost:80${NC}"
echo -e "  • 后端: ${YELLOW}http://localhost:8000${NC}"
echo -e "  • API文档: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}👤 默认账号：${NC}"
echo -e "  • 用户名: ${YELLOW}admin${NC}"
echo -e "  • 密码: ${YELLOW}admin123${NC}"
echo ""
echo -e "${YELLOW}💡 按 Ctrl+C 停止所有服务${NC}"
echo ""

# 创建停止函数
stop_services() {
    echo -e "\n${YELLOW}🛑 正在停止服务...${NC}"
    
    # 停止后端和前端进程
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
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