## SQL 使用指南（扁平化结构）

> 所有脚本统一放在 `sql/` 根目录，按功能模块拆成最少的文件，避免再出现临时目录与分散的补丁。

### 文件清单

| 文件 | 说明 |
| --- | --- |
| `ruoyi-fastapi.sql` | MySQL 整库初始化（包含系统基础表/菜单） |
| `ruoyi-fastapi-pg.sql` | PostgreSQL 整库初始化 |
| `project.sql` | 工程/项目模块：表结构、演示数据、菜单/权限补丁 |
| `device.sql` | 设备模块：分类/设备表、接口表、菜单/权限补丁 |
| `protocol.sql` | 协议模块：协议表、字典数据、菜单/权限补丁 |

### 推荐使用方式

1. **首次建库**：导入 `ruoyi-fastapi.sql`（或 `ruoyi-fastapi-pg.sql`）。  
2. **按需启用模块**：执行需要的模块脚本，例如：
   ```bash
   mysql -u root -p ruoyi-fastapi < ruoyi-fastapi-backend/sql/project.sql
   mysql -u root -p ruoyi-fastapi < ruoyi-fastapi-backend/sql/device.sql
   mysql -u root -p ruoyi-fastapi < ruoyi-fastapi-backend/sql/protocol.sql
   ```
   所有脚本都具备幂等性，可重复执行，自动补齐菜单、字典和管理员权限。
3. **日常启动**：`setup.sh` / `start.sh` 会跳过 `ruoyi-fastapi*.sql`，仅执行模块脚本，保证旧环境持续同步。

### 脚本约定

- **表结构**：统一使用 `CREATE TABLE IF NOT EXISTS`，避免误删线上数据；如需 DDL 变更请写成 `ALTER TABLE`。
- **基础数据/字典**：采用固定主键 + `WHERE NOT EXISTS` 或 `ON DUPLICATE KEY UPDATE`，确保可重复执行。
- **菜单/权限**：固定 ID，执行前清理历史随机 ID，再插入新数据；必要时包裹事务。
- **扩展模块**：新增功能时直接补充一个 `<module>.sql`，文件内部按“表结构 -> 数据 -> 菜单/角色”顺序组织即可。

保持根目录只有少量核心 SQL，即可快速定位、审查和回滚任何模块的数据库改动。
