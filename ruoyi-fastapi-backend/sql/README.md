# 数据库管理

本项目使用 **Alembic** 管理数据库结构，**YAML + Python** 管理种子数据。

## Schema 管理

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 种子数据

```bash
# 开发环境
python scripts/seed_data.py --env dev

# 生产环境
python scripts/seed_data.py --env prod

# 重置
python scripts/seed_data.py --env dev --reset
```

## 数据文件结构

```
scripts/seed_data/
├── manifest.yaml          # 加载顺序
├── base/                   # 基础数据（所有环境）
│   ├── depts.yaml
│   ├── posts.yaml
│   ├── roles.yaml
│   ├── menus.yaml
│   ├── dict_types.yaml
│   ├── dict_data.yaml
│   └── configs.yaml
└── overlays/               # 环境特定数据
    ├── dev.yaml
    └── prod.yaml
```
