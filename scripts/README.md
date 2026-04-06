# 脚本目录

根目录 `scripts/` 只负责仓库级启动和安装，不再承载后端内部数据库细节。

## 入口

| 脚本 | 平台 | 作用 |
| --- | --- | --- |
| `setup.sh` | macOS | 首次环境配置，安装依赖并初始化本地环境 |
| `start.sh` | macOS | 日常开发启动，先分发数据库工作流，再启动前后端 |
| `stop.sh` | macOS | 停止本仓库 `start.sh` 拉起或复用的前后端实例 |
| `upgrade.sh` | macOS/Linux | 生产环境升级 |
| `upgrade.bat` | Windows | 生产环境升级 |

## 本地开发

```bash
./scripts/setup.sh
./scripts/start.sh
./scripts/stop.sh
```

`./scripts/start.sh` 的数据库行为已经固定为读取后端状态并执行单一动作：

- `DB_WORKFLOW_MODE=migration` 时执行 `python scripts/db.py deploy --revision head`
- `DB_WORKFLOW_MODE=development` 时执行 `python scripts/db.py dev-sync --invoked-by-startup`

不再支持旧的启动前开发态 fallback，也不再保留额外的启动前同步开关。

## 后端工作流命令

```bash
cd ruoyi-fastapi-backend

python scripts/db.py status
python scripts/db.py dev-sync
python scripts/db.py finalize --message "add project protocol fields"
python scripts/db.py deploy --revision head
python scripts/db.py bootstrap-seed --env dev
python scripts/menu.py check --strict
```

## 生产环境升级

macOS / Linux:

```bash
./scripts/upgrade.sh
```

Windows:

```cmd
scripts\upgrade.bat
```
