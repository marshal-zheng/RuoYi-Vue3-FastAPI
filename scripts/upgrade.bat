@echo off
chcp 65001 >nul
setlocal

REM 生产环境一键升级脚本 (Windows)
REM 用于拉取最新代码并重新构建部署 Docker 容器

echo ==========================================
echo        生产环境一键升级脚本
echo ==========================================

REM 切换到项目根目录
cd /d "%~dp0.."
echo 项目目录: %cd%

echo.
echo [1/3] 正在拉取最新代码...
echo ------------------------------------------
git pull
if %errorlevel% neq 0 (
    echo 错误: git pull 失败
    pause
    exit /b 1
)

echo.
echo [2/3] 正在停止并清理旧容器...
echo ------------------------------------------
docker compose -f docker-compose.prod.yml down --volumes --rmi local
if %errorlevel% neq 0 (
    echo 错误: 停止容器失败
    pause
    exit /b 1
)

echo.
echo [3/3] 正在重新构建并启动容器...
echo ------------------------------------------
docker compose -f docker-compose.prod.yml up -d --build
if %errorlevel% neq 0 (
    echo 错误: 启动容器失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo        升级完成！
echo ==========================================
echo.
echo 查看容器状态: docker compose -f docker-compose.prod.yml ps
echo 查看日志: docker compose -f docker-compose.prod.yml logs -f
echo.
pause
