# 后端脚本目录

本目录包含后端相关的工具脚本。

## 脚本列表

| 脚本 | 说明 |
|------|------|
| `analyze_indexes.py` | 数据库索引分析工具 |
| `data_migrate.py` | 数据迁移脚本 |
| `db_migrate.sh` | 数据库迁移执行脚本 |
| `run_tests.sh` | 运行测试脚本 |
| `seed_data.py` | 种子数据初始化 |
| `test_migrations.py` | 迁移测试脚本 |
| `wait_for_db.py` | 等待数据库就绪 |
| `check_no_new_horizontal_layer_files.py` | 横向分层目录新增文件防回退检查 |

## 索引分析工具

`analyze_indexes.py` 用于分析数据库索引使用情况，识别未使用和重复索引。

### 功能

- 分析索引使用情况（扫描次数、读取行数）
- 识别未使用的索引
- 识别重复索引
- 发现缺失索引（基于顺序扫描统计）
- 生成优化建议
- 支持 MySQL 和 PostgreSQL

### 使用方法

```bash
cd ruoyi-fastapi-backend

# 控制台输出（默认）
python scripts/analyze_indexes.py

# Markdown 格式输出
python scripts/analyze_indexes.py --format markdown

# JSON 格式输出
python scripts/analyze_indexes.py --format json

# 导出报告到文件
python scripts/analyze_indexes.py --output report.json

# 组合使用
python scripts/analyze_indexes.py --format markdown --output index_report.md
```

### 输出示例

```
============================================================
索引分析报告
生成时间: 2026-01-27 10:30:00
============================================================

📊 索引统计摘要
----------------------------------------
  总索引数: 45
  活跃索引: 38
  低使用率索引: 5
  未使用索引: 2
  总索引大小: 12.5 MB
  未使用索引大小: 1.2 MB

⚠️  未使用的索引 (2 个)
----------------------------------------
  - sys_user.idx_user_email
    大小: 0.8 MB, 扫描次数: 0

💡 优化建议
----------------------------------------
  🔴 [HIGH] 发现 2 个未使用的索引，建议删除以节省存储空间和提升写入性能
```

### 注意事项

1. **需要足够的运行数据**：索引使用统计需要系统运行一段时间后才能准确反映使用情况
2. **MySQL 需要启用 performance_schema**：MySQL 的索引统计依赖 `sys.schema_index_statistics`
3. **PostgreSQL 自动收集统计**：PostgreSQL 的 `pg_stat_user_indexes` 会自动收集索引使用数据

## 数据库迁移

### 执行迁移

```bash
cd ruoyi-fastapi-backend

# 生成迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 迁移测试

```bash
python scripts/test_migrations.py
```

## 种子数据

### 初始化种子数据

```bash
cd ruoyi-fastapi-backend

# 默认环境
python scripts/seed_data.py

# 指定环境
python scripts/seed_data.py --env dev
python scripts/seed_data.py --env prod
```

### 种子数据结构

```
seed_data/
├── manifest.yaml          # 数据加载清单
├── menus.registry.yaml    # 菜单+授权唯一声明源
├── base/                  # 基础数据
│   ├── configs.yaml       # 系统配置
│   ├── depts.yaml         # 部门数据
│   ├── dict_types.yaml    # 字典类型
│   ├── dict_data.yaml     # 字典数据
│   ├── posts.yaml         # 岗位数据
│   └── roles.yaml         # 角色数据
└── overlays/              # 环境覆盖
    ├── dev.yaml           # 开发环境（不再承载 role_menus）
    └── prod.yaml          # 生产环境
```

### 菜单声明工具链

```bash
# 新增/删除菜单脚手架
python scripts/menu_registry_tool.py add --parent-id 0 --menu-name 示例 --path demo --component demo/index
python scripts/menu_registry_tool.py remove --menu-id 9999 --cascade

# 本地与 CI 校验
python scripts/check_menu_registry.py --strict
```
