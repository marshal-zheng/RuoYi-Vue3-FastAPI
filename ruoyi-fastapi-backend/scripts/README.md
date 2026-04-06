# 后端脚本目录

顶层 `scripts/` 现在只保留稳定入口，内部实现和低频工具已分层收敛。

## 公开入口

| 入口 | 作用 |
| --- | --- |
| `db.py` | 统一数据库工作流入口：`status` / `dev-sync` / `finalize` / `deploy` / `verify` / `wait-db` / `bootstrap-seed` |
| `menu.py` | 统一菜单声明入口：`add` / `remove` / `check` |

## 目录分层

| 目录 | 作用 |
| --- | --- |
| `internal/` | `db.py`、`menu.py` 的内部实现模块，不作为公开 CLI |
| `manual/` | 低频人工工具和一次性迁移脚本 |
| `seed_data/` | 启动期 bootstrap 数据和受管声明文件 |

## 数据库工作流

```bash
cd ruoyi-fastapi-backend

# 查看当前工作流状态
python scripts/db.py status

# 显式开发态同步（仅 DB_WORKFLOW_MODE=development 时可用）
python scripts/db.py dev-sync

# 生成正式 Alembic migration + release bundle
python scripts/db.py finalize --message "描述"

# 正式环境执行迁移与发布
python scripts/db.py deploy --revision head

# 只校验工作流，不执行发布
python scripts/db.py verify --ci

# 等待数据库可连接
python scripts/db.py wait-db

# 仅执行启动期 bootstrap 种子
python scripts/db.py bootstrap-seed --env dev
```

### 工作流边界

- 默认模式是 `DB_WORKFLOW_MODE=migration`。
- 只有显式设置 `DB_WORKFLOW_MODE=development`，才允许执行 `python scripts/db.py dev-sync`。
- 正式受管声明只认 `capabilities/modules/*.module.yaml` 与 `scripts/seed_data/release-plan.yaml`。
- `scripts/seed_data/menus.registry.yaml`、`base/dict_types.yaml`、`base/dict_data.yaml`、`base/configs.yaml` 只保留空壳占位；非空会被 `menu.py check` / `db.py verify --ci` 阻断。
- `./scripts/start.sh` 在开发态只认统一 `dev-sync`，不再支持旧的启动前开发态开关。
- 共享环境、容器启动、测试、预发、生产和客户升级只允许走 `deploy`。
- `python scripts/db.py status` 现在只输出轻量路由状态；深度检查统一走 `python scripts/db.py verify --ci`。

## 菜单声明

```bash
cd ruoyi-fastapi-backend

# 新增模块内菜单声明（自动分配 menu_id，可选自动写入 role_grants）
python scripts/menu.py add --module platform --parent-key platform.menu.1 --menu-name 示例页面 --path demo --component system/demo/index --grant-role common

# 删除模块内菜单声明
python scripts/menu.py remove --module platform --menu-key platform.menu.100 --cascade

# 校验模块声明，同时阻断 legacy 双写回流
python scripts/menu.py check
```

说明：

- `menu.py add/remove/check` 现在只操作 `capabilities/modules/*.module.yaml`。
- `--module` 是唯一 ownership 入口；`menu_id` 由脚手架自动维护，不再作为 CLI 输入。
- `release-plan.yaml` 继续只做模块级启用/禁用选择，不在 `menu.py` 中编辑对象级选择。

## 低频工具

```bash
# 索引分析
python scripts/manual/analyze_indexes.py --format markdown

# 生成 baseline bundle scaffold
python scripts/manual/generate_baseline_bundle.py --bundle-id 20260402_001_datasource-baseline --schema-revision 20260402_workflow_metadata

# 一次性导出 legacy 中心化声明到某个模块 manifest
python scripts/manual/migrate_legacy_managed_data.py --module platform --gate-config-key capability.platform.enabled --gate-default-enabled

# 敏感数据 hash 回填
python scripts/data_migrations/backfill_sensitive_hash.py
```

其余治理脚本、性能基准和一次性手工工具已从当前公开入口清理，不再保留为主仓库脚本面的一部分。
