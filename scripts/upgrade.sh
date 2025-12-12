#!/bin/bash

# 生产环境一键升级脚本 (Mac/Linux)
# 用于拉取最新代码并重新构建部署 Docker 容器

set -e

echo "=========================================="
echo "       生产环境一键升级脚本"
echo "=========================================="

# 切换到项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
echo "项目目录: $PROJECT_ROOT"

echo ""
echo "[1/3] 正在拉取最新代码..."
echo "------------------------------------------"
git pull

echo ""
echo "[2/3] 正在停止并清理旧容器..."
echo "------------------------------------------"
docker compose -f docker-compose.prod.yml down --volumes --rmi local

echo ""
echo "[3/3] 正在重新构建并启动容器..."
echo "------------------------------------------"
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=========================================="
echo "       升级完成！"
echo "=========================================="
echo ""
echo "查看容器状态: docker compose -f docker-compose.prod.yml ps"
echo "查看日志: docker compose -f docker-compose.prod.yml logs -f"
