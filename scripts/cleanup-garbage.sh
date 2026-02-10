#!/bin/bash
# cleanup-garbage.sh - 清理垃圾文件和临时文件
# 用途：删除测试覆盖率、缓存、备份文件等垃圾文件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}垃圾文件和临时文件清理脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 统计变量
TOTAL_SIZE_BEFORE=0
TOTAL_SIZE_AFTER=0
TOTAL_FILES_DELETED=0

# 计算目录大小（KB）
get_size() {
    if [ -e "$1" ]; then
        du -sk "$1" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

echo -e "${YELLOW}正在扫描垃圾文件...${NC}"
echo ""

# ==================== 1. 测试覆盖率文件 ====================
echo -e "${YELLOW}[1/10] 清理测试覆盖率文件...${NC}"

COVERAGE_SIZE=0
if [ -f ".coverage" ]; then
    SIZE=$(get_size ".coverage")
    COVERAGE_SIZE=$((COVERAGE_SIZE + SIZE))
    rm -f .coverage
    echo -e "${GREEN}  ✓ 删除 .coverage (${SIZE}KB)${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
fi

if [ -d "tests/coverage/" ]; then
    SIZE=$(get_size "tests/coverage/")
    COVERAGE_SIZE=$((COVERAGE_SIZE + SIZE))
    rm -rf tests/coverage/
    echo -e "${GREEN}  ✓ 删除 tests/coverage/ (${SIZE}KB)${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
fi

if [ "$COVERAGE_SIZE" -eq 0 ]; then
    echo -e "${GREEN}  ✓ 未发现测试覆盖率文件${NC}"
else
    echo -e "${GREEN}  ✓ 共清理 ${COVERAGE_SIZE}KB${NC}"
fi

# ==================== 2. .DS_Store 文件 ====================
echo -e "${YELLOW}[2/10] 清理 .DS_Store 文件...${NC}"

DS_COUNT=$(find . -name ".DS_Store" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$DS_COUNT" -gt 0 ]; then
    find . -name ".DS_Store" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ 删除 $DS_COUNT 个 .DS_Store 文件${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + DS_COUNT))
else
    echo -e "${GREEN}  ✓ 未发现 .DS_Store 文件${NC}"
fi

# ==================== 3. Python 缓存 ====================
echo -e "${YELLOW}[3/10] 清理 Python 缓存...${NC}"

PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✓ 删除 $PYCACHE_COUNT 个 __pycache__ 目录${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + PYCACHE_COUNT))
else
    echo -e "${GREEN}  ✓ 未发现 __pycache__ 目录${NC}"
fi

PYC_COUNT=$(find . -name "*.pyc" -o -name "*.pyo" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYC_COUNT" -gt 0 ]; then
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyo" -delete 2>/dev/null
    echo -e "${GREEN}  ✓ 删除 $PYC_COUNT 个 .pyc/.pyo 文件${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + PYC_COUNT))
fi

# ==================== 4. 测试缓存目录 ====================
echo -e "${YELLOW}[4/10] 清理测试缓存目录...${NC}"

TEST_CACHE_SIZE=0
if [ -d "ruoyi-fastapi-backend/.hypothesis/" ]; then
    SIZE=$(get_size "ruoyi-fastapi-backend/.hypothesis/")
    TEST_CACHE_SIZE=$((TEST_CACHE_SIZE + SIZE))
    rm -rf ruoyi-fastapi-backend/.hypothesis/
    echo -e "${GREEN}  ✓ 删除 .hypothesis/ (${SIZE}KB)${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
fi

if [ -d "ruoyi-fastapi-backend/.pytest_cache/" ]; then
    SIZE=$(get_size "ruoyi-fastapi-backend/.pytest_cache/")
    TEST_CACHE_SIZE=$((TEST_CACHE_SIZE + SIZE))
    rm -rf ruoyi-fastapi-backend/.pytest_cache/
    echo -e "${GREEN}  ✓ 删除 .pytest_cache/ (${SIZE}KB)${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
fi

if [ "$TEST_CACHE_SIZE" -eq 0 ]; then
    echo -e "${GREEN}  ✓ 未发现测试缓存目录${NC}"
else
    echo -e "${GREEN}  ✓ 共清理 ${TEST_CACHE_SIZE}KB${NC}"
fi

# ==================== 5. 构建产物 ====================
echo -e "${YELLOW}[5/10] 清理构建产物...${NC}"

if [ -d "ruoyi-fastapi-frontend/dist/" ]; then
    SIZE=$(get_size "ruoyi-fastapi-frontend/dist/")
    rm -rf ruoyi-fastapi-frontend/dist/
    echo -e "${GREEN}  ✓ 删除 dist/ (${SIZE}KB)${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
else
    echo -e "${GREEN}  ✓ 未发现 dist/ 目录${NC}"
fi

# ==================== 6. 备份文件 ====================
echo -e "${YELLOW}[6/10] 清理备份文件...${NC}"

BAK_COUNT=$(find . -name "*.bak" -o -name "*.old" -o -name "*.tmp" -o -name "*~" 2>/dev/null | wc -l | tr -d ' ')
if [ "$BAK_COUNT" -gt 0 ]; then
    find . -name "*.bak" -delete 2>/dev/null
    find . -name "*.old" -delete 2>/dev/null
    find . -name "*.tmp" -delete 2>/dev/null
    find . -name "*~" -delete 2>/dev/null
    echo -e "${GREEN}  ✓ 删除 $BAK_COUNT 个备份文件${NC}"
    TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + BAK_COUNT))
else
    echo -e "${GREEN}  ✓ 未发现备份文件${NC}"
fi

# ==================== 7. 空报告文件 ====================
echo -e "${YELLOW}[7/10] 清理空报告文件...${NC}"

EMPTY_REPORTS=0
if [ -f "docs/reports/P0_COMPLETION_REPORT.md" ]; then
    if [ ! -s "docs/reports/P0_COMPLETION_REPORT.md" ]; then
        rm docs/reports/P0_COMPLETION_REPORT.md
        echo -e "${GREEN}  ✓ 删除空报告 P0_COMPLETION_REPORT.md${NC}"
        EMPTY_REPORTS=$((EMPTY_REPORTS + 1))
        TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
    fi
fi

if [ "$EMPTY_REPORTS" -eq 0 ]; then
    echo -e "${GREEN}  ✓ 未发现空报告文件${NC}"
fi

# ==================== 8. 日志文件（可选） ====================
echo -e "${YELLOW}[8/10] 清理日志文件...${NC}"
echo -e "${BLUE}  ! 是否清理 logs/ 目录？(y/N): ${NC}"
read -t 5 -n 1 CLEAR_LOGS || CLEAR_LOGS="n"
echo ""

if [[ "$CLEAR_LOGS" == "y" || "$CLEAR_LOGS" == "Y" ]]; then
    if [ -d "logs/" ]; then
        SIZE=$(get_size "logs/")
        rm -rf logs/
        echo -e "${GREEN}  ✓ 删除 logs/ (${SIZE}KB)${NC}"
        TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + 1))
    else
        echo -e "${GREEN}  ✓ 未发现 logs/ 目录${NC}"
    fi
else
    echo -e "${YELLOW}  ! 跳过日志清理${NC}"
fi

# ==================== 9. 空目录 ====================
echo -e "${YELLOW}[9/10] 清理空目录...${NC}"

EMPTY_BEFORE=$(find . -type d -empty -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$EMPTY_BEFORE" -gt 0 ]; then
    # 多次执行以删除嵌套的空目录
    for i in {1..3}; do
        find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true
    done
    
    EMPTY_AFTER=$(find . -type d -empty -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
    DELETED=$((EMPTY_BEFORE - EMPTY_AFTER))
    
    if [ "$DELETED" -gt 0 ]; then
        echo -e "${GREEN}  ✓ 删除 $DELETED 个空目录${NC}"
        TOTAL_FILES_DELETED=$((TOTAL_FILES_DELETED + DELETED))
    fi
    
    if [ "$EMPTY_AFTER" -gt 0 ]; then
        echo -e "${YELLOW}  ! 仍有 $EMPTY_AFTER 个空目录无法删除${NC}"
    fi
else
    echo -e "${GREEN}  ✓ 未发现空目录${NC}"
fi

# ==================== 10. node_modules 中的测试文件（可选） ====================
echo -e "${YELLOW}[10/10] 检查 node_modules 测试文件...${NC}"
SPEC_COUNT=$(find ruoyi-fastapi-frontend/node_modules -name "*.spec.js" -o -name "*.spec.ts" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SPEC_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}  ! node_modules 中有 $SPEC_COUNT 个测试文件（npm install 时自动安装，无需清理）${NC}"
else
    echo -e "${GREEN}  ✓ 正常${NC}"
fi

# ==================== 总结 ====================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}清理完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ 总共删除: $TOTAL_FILES_DELETED 个文件/目录${NC}"
echo ""

# ==================== 建议 ====================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}建议检查:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "1. 运行 'git status' 检查是否有误删文件"
echo "2. 运行测试确保项目正常: cd ruoyi-fastapi-backend && pytest"
echo "3. 重新构建前端: cd ruoyi-fastapi-frontend && npm run build"
echo ""

# ==================== 待处理项 ====================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}待手动处理的项目:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查 MIGRATION_FIX.md
if [ -f "ruoyi-fastapi-backend/MIGRATION_FIX.md" ]; then
    echo -e "${BLUE}1. MIGRATION_FIX.md${NC}"
    echo "   位置: ruoyi-fastapi-backend/MIGRATION_FIX.md"
    echo "   建议: 移到 FAQ/ 或删除"
    echo "   命令: mv ruoyi-fastapi-backend/MIGRATION_FIX.md FAQ/"
    echo ""
fi

# 检查 P0 报告
P0_COUNT=$(find docs/reports -name "P0*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$P0_COUNT" -gt 0 ]; then
    echo -e "${BLUE}2. P0 任务报告 ($P0_COUNT 个)${NC}"
    echo "   位置: docs/reports/P0*.md"
    echo "   建议: 移到归档目录"
    echo "   命令: mkdir -p docs/archive/p0-tasks && mv docs/reports/P0*.md docs/archive/p0-tasks/"
    echo ""
fi

# 检查 MSW
if [ -f "ruoyi-fastapi-frontend/public/mockServiceWorker.js" ]; then
    echo -e "${BLUE}3. Mock Service Worker${NC}"
    echo "   位置: ruoyi-fastapi-frontend/public/mockServiceWorker.js"
    echo "   建议: 确认是否仍在使用 MSW"
    echo "   如不使用: rm ruoyi-fastapi-frontend/public/mockServiceWorker.js"
    echo ""
fi

# 检查 AI 工具配置
if [ -d ".agent/" ] || [ -d ".trae/" ]; then
    echo -e "${BLUE}4. AI 工具配置${NC}"
    echo "   位置: .agent/, .trae/"
    echo "   建议: 确认团队是否使用这些工具"
    echo "   如不使用: rm -rf .agent/ .trae/"
    echo ""
fi

echo -e "${GREEN}清理脚本执行完毕！${NC}"
echo ""
