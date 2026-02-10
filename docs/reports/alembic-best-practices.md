# Alembic 数据库迁移最佳实践

## 1. 概述

本项目使用 Alembic 进行数据库版本控制和迁移管理。

## 2. 基本命令

### 2.1 创建迁移

```bash
# 自动生成迁移脚本（检测模型变化）
alembic revision --autogenerate -m "描述信息"

# 手动创建空迁移脚本
alembic revision -m "描述信息"
```

### 2.2 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 升级一个版本
alembic upgrade +1

# 降级一个版本
alembic downgrade -1

# 降级到指定版本
alembic downgrade <revision_id>

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 预览 SQL（不执行）
alembic upgrade head --sql
```

## 3. 迁移脚本命名规范

本项目使用时间戳格式命名：`YYYYMMDD_HHMMSS_描述`

示例：
- `20250123_143000_create_device_table.py`
- `20250123_150000_add_device_category_field.py`
- `20250124_100000_create_user_indexes.py`

## 4. 迁移脚本编写规范

### 4.1 基本结构

```python
"""简短的描述信息

详细说明（可选）：
- 修改内容1
- 修改内容2

Revision ID: 20250123_143000
Revises: 20250123_140000
Create Date: 2025-01-23 14:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20250123_143000'
down_revision = '20250123_140000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 schema"""
    # 在这里添加升级逻辑
    pass


def downgrade() -> None:
    """回滚数据库 schema"""
    # 在这里添加回滚逻辑
    pass
```

### 4.2 创建表

```python
def upgrade() -> None:
    op.create_table(
        'sys_device',
        sa.Column('device_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='设备ID'),
        sa.Column('device_name', sa.String(100), nullable=False, comment='设备名称'),
        sa.Column('device_type', sa.String(50), nullable=True, comment='设备类型'),
        sa.Column('create_time', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('device_id'),
        sa.Index('idx_device_name', 'device_name'),
        sa.Index('idx_create_time', 'create_time'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='设备表'
    )


def downgrade() -> None:
    op.drop_table('sys_device')
```

### 4.3 添加字段

```python
def upgrade() -> None:
    op.add_column(
        'sys_device',
        sa.Column('manufacturer', sa.String(100), nullable=True, comment='制造商')
    )
    # 添加索引（如果需要）
    op.create_index('idx_manufacturer', 'sys_device', ['manufacturer'])


def downgrade() -> None:
    op.drop_index('idx_manufacturer', table_name='sys_device')
    op.drop_column('sys_device', 'manufacturer')
```

### 4.4 修改字段

```python
def upgrade() -> None:
    # MySQL 示例
    op.alter_column(
        'sys_device',
        'device_name',
        existing_type=sa.String(50),
        type_=sa.String(100),
        existing_nullable=False,
        comment='设备名称（扩展长度）'
    )


def downgrade() -> None:
    op.alter_column(
        'sys_device',
        'device_name',
        existing_type=sa.String(100),
        type_=sa.String(50),
        existing_nullable=False,
        comment='设备名称'
    )
```

### 4.5 添加外键

```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_device_category',
        'sys_device',
        'sys_device_category',
        ['device_category_id'],
        ['category_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_device_category', 'sys_device', type_='foreignkey')
```

### 4.6 数据迁移

```python
from sqlalchemy import table, column

def upgrade() -> None:
    # 创建临时表对象
    device_table = table(
        'sys_device',
        column('device_id', sa.BigInteger),
        column('status', sa.String(1))
    )
    
    # 批量更新数据
    op.execute(
        device_table.update()
        .where(device_table.c.status == None)
        .values(status='0')
    )


def downgrade() -> None:
    pass  # 数据迁移通常不回滚
```

## 5. 迁移最佳实践

### 5.1 原则

1. **每个迁移只做一件事**：便于理解和回滚
2. **可逆性**：确保 downgrade() 能完全回滚 upgrade()
3. **幂等性**：多次执行同一迁移应该是安全的
4. **测试**：在开发环境测试迁移后再应用到生产

### 5.2 迁移前检查清单

- [ ] 确保模型定义正确
- [ ] 检查迁移脚本的 upgrade() 和 downgrade()
- [ ] 在开发环境测试升级
- [ ] 测试降级（回滚）
- [ ] 检查索引和外键约束
- [ ] 备份生产数据库

### 5.3 大数据量迁移

对于包含大量数据的表，使用批量操作：

```python
from alembic import context

def upgrade() -> None:
    connection = context.get_bind()
    
    # 分批处理
    batch_size = 1000
    offset = 0
    
    while True:
        result = connection.execute(
            sa.text(f"""
                SELECT device_id FROM sys_device 
                WHERE status IS NULL 
                LIMIT {batch_size} OFFSET {offset}
            """)
        )
        
        ids = [row[0] for row in result]
        if not ids:
            break
        
        connection.execute(
            sa.text("""
                UPDATE sys_device 
                SET status = '0' 
                WHERE device_id IN :ids
            """),
            {'ids': tuple(ids)}
        )
        
        offset += batch_size
```

### 5.4 避免的问题

1. **不要直接修改已应用的迁移**：应创建新迁移
2. **不要在迁移中导入业务模型**：使用 table() 和 column()
3. **注意字段默认值**：特别是 DateTime 和 Boolean
4. **索引命名**：使用明确的命名避免冲突

## 6. 团队协作

### 6.1 合并冲突

当多人同时创建迁移时：

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 查看迁移链
alembic history

# 3. 如有冲突，手动调整 down_revision
# 编辑迁移文件，确保链式正确

# 4. 测试迁移
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### 6.2 版本控制

- 所有迁移脚本都应提交到 Git
- 不要删除或修改已合并的迁移
- 迁移文件应按时间顺序排列

## 7. 生产环境部署

### 7.1 部署流程

```bash
# 1. 备份数据库
mysqldump -u user -p database > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 查看待执行的迁移
alembic history | head -n 20

# 3. 预览 SQL（可选）
alembic upgrade head --sql > migration.sql
# 检查 migration.sql 文件

# 4. 执行迁移
alembic upgrade head

# 5. 验证
alembic current
```

### 7.2 回滚计划

每次迁移前准备回滚脚本：

```bash
# 生成回滚 SQL
alembic downgrade -1 --sql > rollback.sql
```

## 8. 故障排查

### 8.1 常见问题

**问题：迁移执行失败**

```bash
# 查看当前版本
alembic current

# 查看历史
alembic history --verbose

# 手动标记版本（谨慎使用）
alembic stamp head
```

**问题：自动检测未发现变化**

- 确保模型已导入到 `alembic/env.py`
- 检查 `Base.metadata` 是否包含所有表
- 使用 `--autogenerate` 参数

**问题：MySQL 字符集问题**

在迁移中明确指定：

```python
op.create_table(
    'sys_device',
    # ...
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci'
)
```

## 9. 示例脚本

查看 `docs/alembic-examples.md` 获取更多示例。

## 10. 参考资料

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- 项目内部文档：`dev-docs/database-migration.md`
