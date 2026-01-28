#!/bin/bash
# Git Hooks 安装脚本
#
# 用法: bash scripts/setup-hooks.sh
#
# 功能：
#   安装 Git hooks，实现开发环境自动化：
#   - post-merge: pull 代码后自动同步数据库

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Git Hooks 安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否在 git 仓库中
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo -e "${YELLOW}错误: 未找到 .git/hooks 目录${NC}"
    echo "请确保在项目根目录执行此脚本"
    exit 1
fi

# 安装 post-merge hook
echo "安装 post-merge hook..."
cp "$SCRIPT_DIR/hooks/post-merge" "$GIT_HOOKS_DIR/post-merge"
chmod +x "$GIT_HOOKS_DIR/post-merge"
echo -e "${GREEN}✓ post-merge hook 已安装${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "已安装的 hooks:"
echo "  - post-merge: pull 代码后自动同步数据库"
echo ""
echo "提示:"
echo "  当其他开发者提交了数据库迁移文件，"
echo "  你 pull 代码后会自动执行 alembic upgrade head"
echo ""
