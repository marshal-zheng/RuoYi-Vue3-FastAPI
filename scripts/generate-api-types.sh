#!/bin/bash
# OpenAPI 类型生成脚本
# 用于从仓库 OpenAPI artifact 自动生成 TypeScript 类型和 API 客户端。
# 默认读取 shared/openapi.json；如需临时从本地后端抓取，请显式传入 --live。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-frontend"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OUTPUT_DIR="$FRONTEND_DIR/src/api/_generated"
OPENAPI_FILE="$PROJECT_ROOT/shared/openapi.json"
OPENAPI_SOURCE="${OPENAPI_SOURCE:-artifact}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --live)
            OPENAPI_SOURCE="live"
            shift
            ;;
        --artifact)
            OPENAPI_SOURCE="artifact"
            shift
            ;;
        --input)
            OPENAPI_FILE="$2"
            shift 2
            ;;
        --backend-url)
            BACKEND_URL="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 2
            ;;
    esac
done

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OpenAPI 类型生成工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [[ "$OPENAPI_SOURCE" == "live" ]]; then
    # 显式本地调试路径：可从运行中的后端刷新 artifact，再生成类型。
    mkdir -p "$(dirname "$OPENAPI_FILE")"
    echo -e "${YELLOW}[1/3] 从本地后端获取 OpenAPI 规范...${NC}"
    echo "      URL: $BACKEND_URL/openapi.json"

    if curl -s --fail "$BACKEND_URL/openapi.json" > "$OPENAPI_FILE"; then
        echo -e "${GREEN}      ✓ OpenAPI 规范获取成功${NC}"
    else
        echo -e "${RED}      ✗ 无法获取 OpenAPI 规范${NC}"
        echo -e "${RED}        请确保后端服务已启动: $BACKEND_URL${NC}"
        exit 1
    fi
elif [[ "$OPENAPI_SOURCE" == "artifact" ]]; then
    echo -e "${YELLOW}[1/3] 读取仓库 OpenAPI artifact...${NC}"
    echo "      文件: $OPENAPI_FILE"

    if [[ ! -f "$OPENAPI_FILE" ]]; then
        echo -e "${RED}      ✗ OpenAPI artifact 不存在${NC}"
        echo -e "${RED}        请先运行: cd ruoyi-fastapi-backend && python scripts/export_openapi.py --output ../shared/openapi.json${NC}"
        exit 1
    fi
    echo -e "${GREEN}      ✓ OpenAPI artifact 已就绪${NC}"
else
    echo -e "${RED}      ✗ 不支持的 OPENAPI_SOURCE: $OPENAPI_SOURCE${NC}"
    echo -e "${RED}        可用值: artifact, live${NC}"
    exit 2
fi

# 步骤2：生成 TypeScript 类型
echo ""
echo -e "${YELLOW}[2/3] 生成 TypeScript 类型...${NC}"
echo "      输出目录: $OUTPUT_DIR"

cd "$FRONTEND_DIR"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 使用锁文件中的 @hey-api/openapi-ts 生成类型，避免 npx 解析线上最新版本导致漂移。
if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/openapi-ts" ]]; then
    echo -e "${RED}      ✗ 未找到本地 @hey-api/openapi-ts CLI${NC}"
    echo -e "${RED}        请先运行: cd ruoyi-fastapi-frontend && yarn install --immutable${NC}"
    exit 1
fi

"$FRONTEND_DIR/node_modules/.bin/openapi-ts" \
    --input "$OPENAPI_FILE" \
    --output "$OUTPUT_DIR" \
    --client @hey-api/client-fetch

node "$FRONTEND_DIR/scripts/postprocess-openapi.mjs" "$OUTPUT_DIR"

echo -e "${GREEN}      ✓ TypeScript 类型生成成功${NC}"

# 步骤3：格式化生成的代码
echo ""
echo -e "${YELLOW}[3/3] 格式化生成的代码...${NC}"

"$FRONTEND_DIR/node_modules/.bin/prettier" \
    --write "$OUTPUT_DIR/**/*.ts" \
    --single-quote \
    --trailing-comma es5 \
    --tab-width 2 \
    --semi \
    --print-width 100
echo -e "${GREEN}      ✓ 代码格式化完成${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  类型生成完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "生成的文件位于: $OUTPUT_DIR"
echo "OpenAPI 来源: $OPENAPI_SOURCE ($OPENAPI_FILE)"
echo ""
echo "使用方法:"
echo "  import type { UserResponse } from '@/api/_generated';"
echo "  import { UserService } from '@/api/_generated';"
echo ""
