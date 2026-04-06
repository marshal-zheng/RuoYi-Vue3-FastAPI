# 数据库管理

本项目的数据库工作流已经收敛到单一入口 `python scripts/db.py ...`。

## 工作流边界

- 默认模式是 `DB_WORKFLOW_MODE=migration`。
- 只有显式设置 `DB_WORKFLOW_MODE=development`，才允许执行开发态 `dev-sync`。
- 开发态同步命令是 `python scripts/db.py dev-sync`。
- 准备进入协作、测试、预发、生产或客户交付前，必须执行 `python scripts/db.py finalize --message "<描述>"`。
- 共享环境和交付环境只允许执行 `python scripts/db.py deploy --revision head`。

## 推荐命令

```bash
cd ruoyi-fastapi-backend

# 查看当前状态
python scripts/db.py status

# 个人开发库同步
python scripts/db.py dev-sync

# 生成正式 migration + release bundle
python scripts/db.py finalize --message "add simulation audit tables"

# 正式环境部署
python scripts/db.py deploy --revision head

# 启动期 bootstrap 数据
python scripts/db.py bootstrap-seed --env dev
```

`python scripts/db.py status` 只用于快速读取当前工作流路由，不再触发深度数据库检查；如需校验 drift 和发布状态，使用 `python scripts/db.py verify --ci`。

## Alembic 底层命令

正式交付请优先使用 `db.py`。以下命令仅保留给底层维护与排障：

```bash
alembic current
alembic history
alembic downgrade -1
```

## 数据文件结构

```
scripts/seed_data/
├── manifest.yaml
├── menus.registry.yaml
├── release-plan.yaml
├── base/
│   ├── depts.yaml
│   ├── posts.yaml
│   ├── roles.yaml
│   ├── dict_types.yaml
│   ├── dict_data.yaml
│   └── configs.yaml
└── overlays/
    ├── dev.yaml
    └── prod.yaml
```
