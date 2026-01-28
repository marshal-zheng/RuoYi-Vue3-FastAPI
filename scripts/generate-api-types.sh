#!/bin/bash
# OpenAPI 类型生成脚本
# 用于从后端 OpenAPI 规范自动生成 TypeScript 类型和 API 客户端
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-frontend"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OUTPUT_DIR="$FRONTEND_DIR/src/api/_generated"
OPENAPI_FILE="$PROJECT_ROOT/shared/openapi.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OpenAPI 类型生成工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 确保 shared 目录存在
mkdir -p "$PROJECT_ROOT/shared"

# 步骤1：从后端获取 OpenAPI 规范
echo -e "${YELLOW}[1/3] 从后端获取 OpenAPI 规范...${NC}"
echo "      URL: $BACKEND_URL/openapi.json"

if curl -s --fail "$BACKEND_URL/openapi.json" > "$OPENAPI_FILE"; then
    echo -e "${GREEN}      ✓ OpenAPI 规范获取成功${NC}"
else
    echo -e "${RED}      ✗ 无法获取 OpenAPI 规范${NC}"
    echo -e "${RED}        请确保后端服务已启动: $BACKEND_URL${NC}"
    exit 1
fi

# 步骤2：生成 TypeScript 类型
echo ""
echo -e "${YELLOW}[2/3] 生成 TypeScript 类型...${NC}"
echo "      输出目录: $OUTPUT_DIR"

cd "$FRONTEND_DIR"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 使用 @hey-api/openapi-ts 生成类型
npx @hey-api/openapi-ts \
    --input "$OPENAPI_FILE" \
    --output "$OUTPUT_DIR" \
    --client @hey-api/client-axios \
    --types \
    --services

echo -e "${GREEN}      ✓ TypeScript 类型生成成功${NC}"

# 步骤3：格式化生成的代码
echo ""
echo -e "${YELLOW}[3/3] 格式化生成的代码...${NC}"

if command -v prettier &> /dev/null; then
    prettier --write "$OUTPUT_DIR/**/*.ts" 2>/dev/null || true
    echo -e "${GREEN}      ✓ 代码格式化完成${NC}"
else
    echo -e "${YELLOW}      ⚠ prettier 未安装，跳过格式化${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  类型生成完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "生成的文件位于: $OUTPUT_DIR"
echo ""
echo "使用方法:"
echo "  import type { UserResponse } from '@/api/_generated';"
echo "  import { UserService } from '@/api/_generated';"
echo ""
