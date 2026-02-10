#!/bin/bash
# cleanup.sh - 项目清理脚本
# 用途：清理项目中的临时文件、缓存文件和空目录

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}项目清理脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 统计函数
count_files() {
    find . -name "$1" -type f 2>/dev/null | wc -l | tr -d ' '
}

count_dirs() {
    find . -type d -name "$1" 2>/dev/null | wc -l | tr -d ' '
}

# 1. 删除系统缓存文件
echo -e "${YELLOW}[1/8] 清理系统缓存文件...${NC}"
DS_STORE_COUNT=$(count_files ".DS_Store")
if [ "$DS_STORE_COUNT" -gt 0 ]; then
    find . -name ".DS_Store" -type f -delete
    echo -e "${GREEN}✓ 删除 $DS_STORE_COUNT 个 .DS_Store 文件${NC}"
else
    echo -e "${GREEN}✓ 未发现 .DS_Store 文件${NC}"
fi

# 2. 删除 Python 缓存
echo -e "${YELLOW}[2/8] 清理 Python 缓存...${NC}"
PYCACHE_COUNT=$(count_dirs "__pycache__")
PYC_COUNT=$(count_files "*.pyc")

if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}✓ 删除 $PYCACHE_COUNT 个 __pycache__ 目录${NC}"
fi

if [ "$PYC_COUNT" -gt 0 ]; then
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyo" -delete 2>/dev/null
    echo -e "${GREEN}✓ 删除 $PYC_COUNT 个 .pyc/.pyo 文件${NC}"
fi

if [ "$PYCACHE_COUNT" -eq 0 ] && [ "$PYC_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ 未发现 Python 缓存文件${NC}"
fi

# 3. 删除测试缓存
echo -e "${YELLOW}[3/8] 清理测试缓存...${NC}"
CLEANED=0

if [ -d "ruoyi-fastapi-backend/.hypothesis/" ]; then
    rm -rf ruoyi-fastapi-backend/.hypothesis/
    echo -e "${GREEN}✓ 删除 .hypothesis/ 目录${NC}"
    CLEANED=1
fi

if [ -d "ruoyi-fastapi-backend/.pytest_cache/" ]; then
    rm -rf ruoyi-fastapi-backend/.pytest_cache/
    echo -e "${GREEN}✓ 删除 .pytest_cache/ 目录${NC}"
    CLEANED=1
fi

if [ "$CLEANED" -eq 0 ]; then
    echo -e "${GREEN}✓ 未发现测试缓存目录${NC}"
fi

# 4. 删除构建产物
echo -e "${YELLOW}[4/8] 清理构建产物...${NC}"
if [ -d "ruoyi-fastapi-frontend/dist/" ]; then
    DIST_SIZE=$(du -sh ruoyi-fastapi-frontend/dist/ 2>/dev/null | cut -f1)
    rm -rf ruoyi-fastapi-frontend/dist/
    echo -e "${GREEN}✓ 删除 dist/ 目录 ($DIST_SIZE)${NC}"
else
    echo -e "${GREEN}✓ 未发现 dist/ 目录${NC}"
fi

# 5. 删除备份文件
echo -e "${YELLOW}[5/8] 清理备份文件...${NC}"
BAK_COUNT=$(count_files "*.bak")
OLD_COUNT=$(count_files "*.old")
TMP_COUNT=$(count_files "*.tmp")

TOTAL_BACKUP=0

if [ "$BAK_COUNT" -gt 0 ]; then
    find . -name "*.bak" -delete 2>/dev/null
    echo -e "${GREEN}✓ 删除 $BAK_COUNT 个 .bak 文件${NC}"
    TOTAL_BACKUP=$((TOTAL_BACKUP + BAK_COUNT))
fi

if [ "$OLD_COUNT" -gt 0 ]; then
    find . -name "*.old" -delete 2>/dev/null
    echo -e "${GREEN}✓ 删除 $OLD_COUNT 个 .old 文件${NC}"
    TOTAL_BACKUP=$((TOTAL_BACKUP + OLD_COUNT))
fi

if [ "$TMP_COUNT" -gt 0 ]; then
    find . -name "*.tmp" -delete 2>/dev/null
    echo -e "${GREEN}✓ 删除 $TMP_COUNT 个 .tmp 文件${NC}"
    TOTAL_BACKUP=$((TOTAL_BACKUP + TMP_COUNT))
fi

find . -name "*~" -delete 2>/dev/null || true

if [ "$TOTAL_BACKUP" -eq 0 ]; then
    echo -e "${GREEN}✓ 未发现备份文件${NC}"
fi

# 6. 删除空报告
echo -e "${YELLOW}[6/8] 清理空报告文件...${NC}"
if [ -f "docs/reports/P0_COMPLETION_REPORT.md" ]; then
    if [ ! -s "docs/reports/P0_COMPLETION_REPORT.md" ]; then
        rm docs/reports/P0_COMPLETION_REPORT.md
        echo -e "${GREEN}✓ 删除空报告文件 P0_COMPLETION_REPORT.md${NC}"
    else
        echo -e "${GREEN}✓ P0_COMPLETION_REPORT.md 不为空，保留${NC}"
    fi
else
    echo -e "${GREEN}✓ 未发现空报告文件${NC}"
fi

# 7. 删除空目录
echo -e "${YELLOW}[7/8] 清理空目录...${NC}"
EMPTY_BEFORE=$(find . -type d -empty -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$EMPTY_BEFORE" -gt 0 ]; then
    # 多次执行以删除嵌套的空目录
    for i in {1..3}; do
        find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true
    done
    
    EMPTY_AFTER=$(find . -type d -empty -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
    DELETED=$((EMPTY_BEFORE - EMPTY_AFTER))
    
    if [ "$DELETED" -gt 0 ]; then
        echo -e "${GREEN}✓ 删除 $DELETED 个空目录${NC}"
    else
        echo -e "${GREEN}✓ 未能删除空目录（可能被保护）${NC}"
    fi
    
    if [ "$EMPTY_AFTER" -gt 0 ]; then
        echo -e "${YELLOW}! 仍有 $EMPTY_AFTER 个空目录无法删除${NC}"
    fi
else
    echo -e "${GREEN}✓ 未发现空目录${NC}"
fi

# 8. 清理日志（可选，默认注释）
echo -e "${YELLOW}[8/8] 清理日志文件（可选）...${NC}"
echo -e "${YELLOW}! 跳过日志清理（如需清理请取消注释脚本中的相关代码）${NC}"
# if [ -d "logs/" ]; then
#     LOG_SIZE=$(du -sh logs/ 2>/dev/null | cut -f1)
#     rm -rf logs/
#     echo -e "${GREEN}✓ 删除 logs/ 目录 ($LOG_SIZE)${NC}"
# fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}清理完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}建议执行以下命令检查：${NC}"
echo "  git status           # 检查是否有误删文件"
echo "  find . -type d -empty  # 检查剩余的空目录"
echo ""
