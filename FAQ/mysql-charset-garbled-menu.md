# Q: 数据源菜单中文显示乱码?

## 问题描述
- 侧边栏「数据源中心」及其子菜单（数据源管理、数据源查询/新增/修改/删除）显示为 `æ•°æ®æºä¸­å¿ƒ` 等乱码
- 其他中文菜单（系统管理、系统监控等）显示正常
- 仅影响通过 seed 脚本后期追加的菜单记录（menu_id 5, 120, 1067–1070）

## 复现步骤
1. 执行 `python scripts/seed_data.py --env dev` 插入数据源相关菜单
2. 登录前端，展开侧边栏底部菜单
3. 观察到「数据源中心」显示为乱码字符

## 原因
- MySQL 连接字符串未指定 `charset=utf8mb4`（`config/database.py` 和 `config/get_scheduler.py`）
- asyncmy / pymysql 驱动在未显式指定 charset 时，可能使用 latin1 作为默认连接字符集
- UTF-8 编码的中文字节被当作 latin1 写入 utf8mb4 表，产生双重编码（mojibake）
- 验证方法：`SELECT HEX(menu_name) FROM sys_menu WHERE menu_id = 5;` 若结果以 `C3` 开头而非 `E6` 开头，即为双重编码

## 处理方案

### 1) 立即止血：直接修复数据库中的乱码数据

```sql
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源中心', remark = '数据源中心目录' WHERE menu_id = 5;
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源管理', remark = '数据源管理菜单' WHERE menu_id = 120;
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源查询' WHERE menu_id = 1067;
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源新增' WHERE menu_id = 1068;
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源修改' WHERE menu_id = 1069;
UPDATE `ruoyi-fastapi`.sys_menu SET menu_name = '数据源删除' WHERE menu_id = 1070;
```

### 2) 根治修复：在连接字符串中添加 charset 参数

`config/database.py`：

```python
ASYNC_SQLALCHEMY_DATABASE_URL = (
    f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    f'?charset=utf8mb4'
)
```

`config/get_scheduler.py`：

```python
SQLALCHEMY_DATABASE_URL = (
    f'mysql+pymysql://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    f'?charset=utf8mb4'
)
```

> 注：`alembic/env.py` 中已正确配置了 `?charset=utf8mb4`，无需修改。

### 3) 预防措施
- 所有 MySQL 连接字符串统一使用 `?charset=utf8mb4` 后缀
- seed 脚本执行后，可用以下命令快速验证：`mysql -u root -p --default-character-set=utf8mb4 -e "SELECT menu_id, menu_name FROM sys_menu WHERE menu_id IN (5, 120);"`

## 适用范围与版本
- MySQL 8.x + asyncmy / pymysql 驱动
- 问题与 MySQL 服务端字符集无关（数据库和表均为 utf8mb4），仅与客户端连接字符集有关
