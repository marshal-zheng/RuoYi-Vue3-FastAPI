# 登录错误修复说明

## 问题描述
登录时出现错误：
```
Unknown column 'create_time' in 'field list'
```

## 原因分析
数据库表 `sys_logininfor` 缺少 `create_time` 字段，但ORM模型 `SysLogininfor` 继承自 `LogBaseModel`，该基类包含 `create_time` 字段。

这是因为：
1. 旧的数据库表是从SQL文件创建的，没有 `create_time` 字段
2. 新的ORM模型使用了 `LogBaseModel`，自动包含了 `create_time` 字段

## 解决方案
已创建数据库迁移文件来添加缺失的字段：
- 文件：`alembic/versions/20260127_add_create_time_to_logininfor.py`
- 迁移ID：`20260127_add_create_time`

## 执行迁移
```bash
cd ruoyi-fastapi-backend
alembic upgrade head
```

## 迁移内容
1. 检查 `sys_logininfor` 表是否存在
2. 检查 `create_time` 列是否已存在
3. 如果不存在，添加 `create_time` 列
4. 将现有记录的 `create_time` 设置为 `login_time` 的值

## 验证
迁移成功后，登录功能应该正常工作。

## 注意事项
- 迁移是幂等的，可以安全地多次运行
- 如果列已存在，迁移会跳过
- 现有数据的 `create_time` 会被设置为 `login_time` 的值

## 相关文件
- ORM模型：`module_admin/entity/do/log_do.py`
- 基类定义：`module_admin/entity/do/base.py`
- 迁移文件：`alembic/versions/20260127_add_create_time_to_logininfor.py`
