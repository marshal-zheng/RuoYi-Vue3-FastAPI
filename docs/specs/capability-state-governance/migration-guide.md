# 模块声明硬切换迁移说明

本方案已经完成硬切换。正式受管链路只认下面两类输入：

- `ruoyi-fastapi-backend/capabilities/modules/*.module.yaml`
- `ruoyi-fastapi-backend/scripts/seed_data/release-plan.yaml`

下面这些 legacy 文件不再参与正式编译、`dev-sync`、`finalize`、`deploy`、`verify`：

- `ruoyi-fastapi-backend/scripts/seed_data/menus.registry.yaml`
- `ruoyi-fastapi-backend/scripts/seed_data/base/dict_types.yaml`
- `ruoyi-fastapi-backend/scripts/seed_data/base/dict_data.yaml`
- `ruoyi-fastapi-backend/scripts/seed_data/base/configs.yaml`

它们只能保持空壳，或者作为一次性迁移脚本的输入。只要残留非空内容，`python scripts/menu.py check` 和 `python scripts/db.py verify --ci` 都会直接失败。

## 一次性迁移

如果仓库里还有旧中心化声明，先导出到一个模块 manifest：

```bash
cd ruoyi-fastapi-backend

python scripts/manual/migrate_legacy_managed_data.py \
  --module platform \
  --gate-config-key capability.platform.enabled \
  --gate-default-enabled
```

行为说明：

- 会把 `menus.registry.yaml`、`dict_types.yaml`、`dict_data.yaml`、`configs.yaml` 导出到 `capabilities/modules/<module>.module.yaml`
- 迁移出的菜单会生成稳定 `menu_key`，默认格式是 `<module>.menu.<menu_id>`
- 如果目标模块已存在，或者与现有模块发生 ownership 冲突，脚本直接失败
- 迁移脚本不会继续保留双轨语义；导出完成后应把 legacy 文件清空为占位壳

## 日常开发

迁移完成后，日常菜单脚手架只用 `menu.py`：

```bash
cd ruoyi-fastapi-backend

python scripts/menu.py add \
  --module platform \
  --parent-key platform.menu.1 \
  --menu-name 示例页面 \
  --path demo \
  --component system/demo/index \
  --grant-role common

python scripts/menu.py remove \
  --module platform \
  --menu-key platform.menu.100 \
  --cascade

python scripts/menu.py check
```

约束：

- `--module` 是唯一 ownership 入口
- `menu_id` 由脚手架自动维护，不再作为 CLI 输入
- `release-plan.yaml` 只维护模块 `true/false`，不再编辑对象级 `menu_ids / role_grants / dict_types / config_keys`

## 验证顺序

建议每次迁移或模块声明调整后都跑下面两步：

```bash
cd ruoyi-fastapi-backend

python scripts/menu.py check
python scripts/db.py verify --ci
```

如果是在开发态同步数据库，再执行：

```bash
cd ruoyi-fastapi-backend

DB_WORKFLOW_MODE=development python scripts/db.py dev-sync
```
