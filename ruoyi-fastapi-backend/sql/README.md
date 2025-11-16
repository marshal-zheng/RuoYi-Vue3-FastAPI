## SQL 使用指南（单目录约定）

> 目的：在同一 `sql/` 目录下，通过命名约定区分**全量建库**、**初始化数据**与**增量补丁**，让工程管理、协议管理保持一致体验。

### 文件类型

- `ruoyi-fastapi*.sql`：整库初始化脚本（MySQL/PG）。
- `sys_*.sql`：模块建表 / 基础数据，如 `sys_project.sql`、`sys_protocol.sql`、`sys_project_version.sql`。
- `*_dict_data.sql`：幂等的字典或演示数据脚本，例如 `protocol_dict_data.sql`。
- `update_*.sql`：运行中环境的增量补丁（菜单、结构升级等）。命名可追加日期：`update_project_menu_20241116.sql`。

### 推荐执行顺序

1. `ruoyi-fastapi.sql` 或 `ruoyi-fastapi-pg.sql`
2. 需要的 `sys_*.sql` 扩展模块（按实际功能挑选）
3. 字典/演示数据脚本（`*_dict_data.sql`）
4. 增量补丁（全部 `update_*.sql`，按文件中说明执行）

### 编写与维护规范

- 菜单、按钮、字典等固定数据统一采用固定 ID，并通过 `INSERT ... ON DUPLICATE KEY UPDATE` / `WHERE NOT EXISTS` 保证可重复执行。
- DDL 改造脚本先判断列/索引是否存在，必要时提供备份与回滚提示。
- 每个 `update_*.sql` 在文件头说明：背景、适用场景、回滚方式，脚本内部用事务包裹关键更新。
- 新功能上线时，同时提供 `sys_*.sql`（新环境）与对应 `update_*.sql`（老环境），保证部署与升级一致。

### 目录清单（示例）

- `sys_project.sql` / `sys_protocol.sql`：工程管理、协议管理基础表
- `protocol_menu.sql`：协议菜单全量初始化
- `update_project_menu.sql` / `update_protocol_menu.sql`：工程与协议菜单的固定 ID 补丁
- `update_protocol_version.sql`：协议版本字段升级
- `protocol_dict_data.sql`：协议相关字典

> 若需要新增脚本，请遵循以上命名+注释规范，避免再额外分目录，便于后续排查与部署。
