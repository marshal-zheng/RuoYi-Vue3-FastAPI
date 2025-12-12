# 拓扑图加载报错：Out of sort memory

## 问题现象

进入工程拓扑图编辑页面时，部分项目可以正常加载，部分项目报错：

```
(asyncmy.errors.OperationalError) (1038, 'Out of sort memory, consider increasing server sort buffer size')
[SQL: SELECT sys_project_topology.topology_id, sys_project_topology.project_id, sys_project_topology.version_id, 
sys_project_topology.topology_data, sys_project_topology.create_by, sys_project_topology.create_time, 
sys_project_topology.update_by, sys_project_topology.update_time 
FROM sys_project_topology 
WHERE sys_project_topology.project_id = %s AND sys_project_topology.version_id = %s 
ORDER BY sys_project_topology.update_time DESC]
```

---

## 问题原因

### 1. 根本原因：MySQL filesort 内存溢出

MySQL 执行 `ORDER BY` 时，如果无法使用索引进行排序，就会使用 **filesort**（文件排序）。filesort 会将数据加载到内存中的 `sort_buffer` 进行排序。

当排序的数据量超过 `sort_buffer_size`（默认约 256KB ~ 2MB）时，MySQL 会报错：

```
ERROR 1038: Out of sort memory
```

### 2. 直接原因：大 JSON 字段 + 缺少联合索引

`sys_project_topology` 表的 `topology_data` 字段是 **JSON 类型**，存储完整的拓扑图数据，单条记录可能达到 **几百 KB 甚至几 MB**。

原查询逻辑：

```python
query = select(SysProjectTopology).where(
    SysProjectTopology.project_id == project_id,
    SysProjectTopology.version_id == version_id
).order_by(desc(SysProjectTopology.update_time))  # 无 LIMIT
```

执行流程：
1. MySQL 根据 `project_id` 索引找到所有匹配记录
2. 将 **整行数据（包括大 JSON）** 加载到内存
3. 在内存中按 `update_time` 排序
4. 返回第一条（`scalars().first()`）

**问题在于**：
- 表上只有 `idx_project_topology_project_id` 单列索引
- 排序字段 `update_time` 没有包含在索引中
- MySQL 必须先读取所有匹配行的完整数据，再排序
- 大 JSON 字段导致内存占用飙升

### 3. 为什么有的项目正常、有的报错？

| 情况 | 是否报错 | 原因 |
|------|----------|------|
| 新项目，拓扑数据小 | ✅ 正常 | JSON 小，排序内存够用 |
| 老项目，拓扑数据大 | ❌ 报错 | JSON 大，超出 sort_buffer |
| 同一版本存在多条历史记录 | ❌ 报错 | 需要排序的行数多 |
| 数据库 sort_buffer 配置大 | ✅ 正常 | 内存足够 |

**核心变量**：
- `topology_data` 字段大小
- 同一 `project_id + version_id` 下的记录数量
- MySQL `sort_buffer_size` 配置

---

## 解决方案

### 方案 A：后端代码优化（已实施）

#### 1. 使用两步查询（子查询模式）

> ⚠️ **注意**：仅加 `LIMIT 1` 不够！MySQL 在无覆盖索引时，仍需将整行（包括大 JSON）加载到内存排序后再取第一条。

**正确做法**：先只查小字段 `topology_id`，排序完成后再按主键查完整行。

```python
# 修改前（仍会报错）
query = select(SysProjectTopology).where(...)
query = query.order_by(desc(SysProjectTopology.update_time)).limit(1)

# 修改后（两步查询，彻底解决）
# 第一步：只查 topology_id（4字节），排序不涉及大 JSON
id_query = select(SysProjectTopology.topology_id).where(
    SysProjectTopology.project_id == project_id,
    SysProjectTopology.version_id == version_id
).order_by(desc(SysProjectTopology.update_time)).limit(1)

topology_id = (await db.execute(id_query)).scalar()

# 第二步：根据主键直接获取完整行，无需排序
if topology_id:
    result = await db.execute(
        select(SysProjectTopology).where(SysProjectTopology.topology_id == topology_id)
    )
    return result.scalars().first()
```

**原理**：
- 第一步排序只涉及 `topology_id`（4字节）+ `update_time`（8字节），内存占用极小
- 第二步按主键直接定位，不需要排序

#### 2. 保存时清理重复记录

在 `save_project_topology_dao` 中，保存后自动清理同一 `project_id + version_id` 下的历史重复记录，确保每个版本只保留最新一条拓扑数据。

```python
# 清理重复记录
cleanup_where = [
    SysProjectTopology.project_id == topology.project_id,
    SysProjectTopology.topology_id != existing.topology_id,
]
if topology.version_id is None:
    cleanup_where.append(SysProjectTopology.version_id.is_(None))
else:
    cleanup_where.append(SysProjectTopology.version_id == topology.version_id)
await db.execute(delete(SysProjectTopology).where(*cleanup_where))
```

### 方案 B：数据库索引优化（已实施）

添加联合索引，让 MySQL 可以使用索引完成排序，避免 filesort：

```sql
-- 新建表时自动包含
KEY `idx_project_topology_project_version_update_time` (`project_id`, `version_id`, `update_time`)

-- 已存在表追加索引（幂等）
ALTER TABLE `sys_project_topology` 
ADD INDEX `idx_project_topology_project_version_update_time` (`project_id`, `version_id`, `update_time`);
```

**索引生效原理**：
- 索引按 `(project_id, version_id, update_time)` 顺序存储
- 查询时 `WHERE project_id=? AND version_id=?` 精确匹配前两列
- `ORDER BY update_time DESC` 直接沿索引倒序读取
- **无需 filesort，无需加载大 JSON 到内存排序**

### 方案 C：DBA 层面（可选，不推荐）

增大 MySQL `sort_buffer_size`：

```sql
SET GLOBAL sort_buffer_size = 8388608;  -- 8MB
```

**不推荐原因**：
- 治标不治本，随着数据增长还会复发
- 每个连接都会分配这么多内存，可能导致内存压力

---

## 修复后是否还会出现？

**已彻底修复**，不会再出现：

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 大拓扑数据 | ❌ 报错 | ✅ 正常（LIMIT 1 + 索引避免全量排序） |
| 同版本多条记录 | ❌ 报错 | ✅ 正常（自动清理只保留一条） |
| 高并发写入 | ⚠️ 可能产生重复 | ✅ 正常（兜底清理） |

---

## 手动修复历史数据

如果数据库中已存在重复的拓扑记录，可执行以下 SQL 清理：

```sql
-- 查看哪些 project_id + version_id 存在重复
SELECT project_id, version_id, COUNT(*) as cnt
FROM sys_project_topology
GROUP BY project_id, version_id
HAVING cnt > 1;

-- 删除重复记录，只保留每组最新的一条
DELETE t1 FROM sys_project_topology t1
INNER JOIN sys_project_topology t2
WHERE t1.project_id = t2.project_id
  AND (t1.version_id = t2.version_id OR (t1.version_id IS NULL AND t2.version_id IS NULL))
  AND t1.update_time < t2.update_time;
```

---

## 相关文件

- 后端 DAO：`ruoyi-fastapi-backend/module_admin/dao/project_topology_dao.py`
- 数据库建表：`ruoyi-fastapi-backend/sql/project.sql`
- 前端入口：`ruoyi-fastapi-frontend/src/views/project/components/VersionList.vue`（点击"图编辑"触发）

---

## 总结

| 项目 | 说明 |
|------|------|
| **错误类型** | MySQL filesort 内存溢出 |
| **触发条件** | 大 JSON 字段 + 无覆盖索引 + 无 LIMIT |
| **根因** | 排序需要将完整行数据加载到内存 |
| **为什么不稳定** | 取决于数据大小和 sort_buffer 配置 |
| **解决方案** | LIMIT 1 + 联合索引 + 清理重复数据 |
| **是否彻底修复** | ✅ 是 |
