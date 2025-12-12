# 脚本目录

本目录包含项目的各类运维和开发脚本。

## 脚本列表

| 脚本 | 平台 | 说明 |
|------|------|------|
| `setup.sh` | macOS | 首次环境配置，安装依赖、初始化数据库 |
| `start.sh` | macOS | 日常开发启动，启动前后端服务 |
| `upgrade.sh` | macOS/Linux | 生产环境一键升级 |
| `upgrade.bat` | Windows | 生产环境一键升级 |

## 使用方法

### 本地开发 (macOS)

```bash
# 首次配置环境
./scripts/setup.sh

# 日常启动项目
./scripts/start.sh
```

### 生产环境升级

**macOS/Linux:**
```bash
./scripts/upgrade.sh
```

**Windows:**
```cmd
scripts\upgrade.bat
```

升级脚本会自动执行：
1. `git pull` - 拉取最新代码
2. `docker compose down` - 停止并清理旧容器
3. `docker compose up -d --build` - 重新构建并启动容器
