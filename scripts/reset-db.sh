#!/bin/bash

# ============================================================
# RuoYi-Vue3-FastAPI 数据库重置脚本
# 功能：一键重置数据库并导入所有模块SQL脚本
# 使用：./scripts/reset-db.sh
# ============================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数（可根据实际情况修改）
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-admin1234}"
DB_NAME="${DB_NAME:-ruoyi-fastapi}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SQL_ROOT="$PROJECT_ROOT/ruoyi-fastapi-backend/sql"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuoYi-Vue3-FastAPI 数据库重置工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}配置信息：${NC}"
echo -e "  数据库用户: ${DB_USER}"
echo -e "  数据库名称: ${DB_NAME}"
echo -e "  管理员账号: ${ADMIN_USER}"
echo -e "  管理员密码: ${ADMIN_PASSWORD}"
echo ""

# MySQL 执行函数
mysql_exec() {
    if [ -n "$DB_PASSWORD" ]; then
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$@" 2>/dev/null
    else
        mysql -u "$DB_USER" "$@" 2>/dev/null
    fi
}

# 检查 MySQL 是否可用
echo -e "${BLUE}🔍 检查 MySQL 连接...${NC}"
if ! mysql_exec -e "SELECT 1;" &>/dev/null; then
    echo -e "${RED}❌ MySQL 连接失败，请检查：${NC}"
    echo -e "   1. MySQL 服务是否已启动"
    echo -e "   2. 用户名和密码是否正确"
    echo -e "   3. 当前用户是否有权限访问 MySQL"
    exit 1
fi
echo -e "${GREEN}✅ MySQL 连接正常${NC}"
echo ""

# 检查 SQL 文件是否存在
echo -e "${BLUE}🔍 检查 SQL 文件...${NC}"
SQL_FILES=(
    "$SQL_ROOT/ruoyi-fastapi.sql"
    "$SQL_ROOT/project.sql"
    "$SQL_ROOT/device.sql"
    "$SQL_ROOT/protocol.sql"
    "$SQL_ROOT/simulation.sql"
)

for sql_file in "${SQL_FILES[@]}"; do
    if [ ! -f "$sql_file" ]; then
        echo -e "${RED}❌ SQL 文件不存在: $sql_file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ 所有 SQL 文件检查通过${NC}"
echo ""

# 确认操作
echo -e "${YELLOW}⚠️  警告：此操作将删除现有数据库并重新创建！${NC}"
read -p "确认继续？(y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi
echo ""

# 1. 删除并重建数据库
echo -e "${BLUE}🗑️  删除现有数据库...${NC}"
mysql_exec -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;" || true
echo -e "${GREEN}✅ 数据库已删除${NC}"

echo -e "${BLUE}📦 创建新数据库...${NC}"
mysql_exec -e "CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo -e "${GREEN}✅ 数据库创建成功${NC}"
echo ""

# 2. 导入所有 SQL 脚本
echo -e "${BLUE}📥 开始导入 SQL 脚本...${NC}"
echo ""

SQL_NAMES=(
    "00-ruoyi-fastapi.sql (基础系统)"
    "01-project.sql (工程模块)"
    "02-device.sql (设备模块)"
    "03-protocol.sql (协议模块)"
    "04-simulation.sql (仿真模块)"
)

for i in "${!SQL_FILES[@]}"; do
    sql_file="${SQL_FILES[$i]}"
    sql_name="${SQL_NAMES[$i]}"
    
    echo -e "${BLUE}   ↪ 导入 $sql_name...${NC}"
    if mysql_exec "$DB_NAME" < "$sql_file"; then
        echo -e "${GREEN}   ✅ $sql_name 导入完成${NC}"
    else
        echo -e "${RED}   ❌ $sql_name 导入失败${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✅ 所有 SQL 脚本导入完成${NC}"
echo ""

# 3. 更新管理员密码
echo -e "${BLUE}🔐 更新管理员密码...${NC}"

# 检查 Python 和 bcrypt
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，无法生成密码哈希${NC}"
    exit 1
fi

# 检查 bcrypt 模块
if ! python3 -c "import bcrypt" &>/dev/null; then
    echo -e "${YELLOW}⚠️  bcrypt 模块未安装，正在安装...${NC}"
    pip3 install bcrypt &>/dev/null || {
        echo -e "${RED}❌ bcrypt 安装失败，请手动安装: pip3 install bcrypt${NC}"
        exit 1
    }
fi

# 生成密码哈希
HASH_PWD=$(python3 -c "import bcrypt; print(bcrypt.hashpw('$ADMIN_PASSWORD'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))")

# 更新密码
if mysql_exec "$DB_NAME" -e "UPDATE sys_user SET password = '$HASH_PWD' WHERE user_name = '$ADMIN_USER';"; then
    echo -e "${GREEN}✅ 密码更新成功${NC}"
else
    echo -e "${RED}❌ 密码更新失败${NC}"
    exit 1
fi
echo ""

# 4. 验证密码
echo -e "${BLUE}✅ 验证密码设置...${NC}"
DB_HASH=$(mysql_exec "$DB_NAME" -e "SELECT password FROM sys_user WHERE user_name = '$ADMIN_USER';" | tail -1)

if python3 -c "import bcrypt; import sys; result = bcrypt.checkpw('$ADMIN_PASSWORD'.encode('utf-8'), '$DB_HASH'.encode('utf-8')); sys.exit(0 if result else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ 密码验证成功${NC}"
else
    echo -e "${RED}❌ 密码验证失败${NC}"
    exit 1
fi
echo ""

# 5. 检查数据库表
echo -e "${BLUE}📊 检查数据库表...${NC}"
TABLE_COUNT=$(mysql_exec "$DB_NAME" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME';" | tail -1)
echo -e "${GREEN}✅ 数据库表总数: $TABLE_COUNT${NC}"
echo ""

# 完成
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ 数据库重置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📋 登录信息：${NC}"
echo -e "  用户名: ${ADMIN_USER}"
echo -e "  密码: ${ADMIN_PASSWORD}"
echo ""
echo -e "${BLUE}💡 提示：${NC}"
echo -e "  - 可以通过环境变量自定义配置："
echo -e "    DB_USER=root DB_PASSWORD=yourpass DB_NAME=ruoyi-fastapi ./scripts/reset-db.sh"
echo ""
