"""
批量操作工具
提供高效的批量数据库操作
"""
from typing import List, Dict, Any, Type, TypeVar
from sqlalchemy import insert, update, delete, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert as mysql_insert
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BulkOperations:
    """
    批量操作工具类
    
    提供高效的批量插入、更新、删除操作
    """
    
    def __init__(self, db: AsyncSession, batch_size: int = 1000):
        """
        初始化批量操作工具
        
        Args:
            db: 数据库会话
            batch_size: 批次大小（默认 1000）
        """
        self.db = db
        self.batch_size = batch_size
    
    async def bulk_insert(
        self,
        model_class: Type[T],
        data_list: List[Dict[str, Any]],
        return_defaults: bool = False
    ) -> int:
        """
        批量插入
        
        Args:
            model_class: 模型类
            data_list: 数据字典列表
            return_defaults: 是否返回默认值（如自增ID）
        
        Returns:
            插入的记录数
        """
        if not data_list:
            return 0
        
        total_inserted = 0
        
        # 分批插入
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            stmt = insert(model_class).values(batch)
            if return_defaults:
                stmt = stmt.returning(model_class)
            
            await self.db.execute(stmt)
            total_inserted += len(batch)
            
            logger.debug(f"批量插入: {len(batch)} 条记录")
        
        await self.db.flush()
        logger.info(f"批量插入完成: 共 {total_inserted} 条记录")
        
        return total_inserted
    
    async def bulk_insert_or_update(
        self,
        model_class: Type[T],
        data_list: List[Dict[str, Any]],
        index_elements: List[str],
        update_fields: List[str] = None
    ) -> int:
        """
        批量插入或更新（ON DUPLICATE KEY UPDATE）
        
        MySQL 特有功能
        
        Args:
            model_class: 模型类
            data_list: 数据字典列表
            index_elements: 唯一索引字段列表
            update_fields: 要更新的字段（None 表示更新所有字段）
        
        Returns:
            影响的记录数
        """
        if not data_list:
            return 0
        
        total_affected = 0
        
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            # MySQL INSERT ... ON DUPLICATE KEY UPDATE
            stmt = mysql_insert(model_class).values(batch)
            
            # 构建更新字典
            if update_fields:
                update_dict = {field: stmt.inserted[field] for field in update_fields}
            else:
                # 更新所有字段（除了主键）
                update_dict = {
                    c.name: stmt.inserted[c.name]
                    for c in model_class.__table__.columns
                    if c.name not in index_elements
                }
            
            stmt = stmt.on_duplicate_key_update(**update_dict)
            
            result = await self.db.execute(stmt)
            total_affected += result.rowcount
            
            logger.debug(f"批量插入或更新: {len(batch)} 条记录")
        
        await self.db.flush()
        logger.info(f"批量插入或更新完成: 共影响 {total_affected} 条记录")
        
        return total_affected
    
    async def bulk_update(
        self,
        model_class: Type[T],
        updates: List[Dict[str, Any]],
        key_field: str = 'id'
    ) -> int:
        """
        批量更新
        
        Args:
            model_class: 模型类
            updates: 更新数据列表，每项必须包含 key_field
            key_field: 主键字段名
        
        Returns:
            更新的记录数
        """
        if not updates:
            return 0
        
        total_updated = 0
        
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            
            if any(key_field not in item for item in batch):
                raise ValueError(f"Missing key field: {key_field}")

            update_keys = [k for k in batch[0].keys() if k != key_field]
            if not update_keys:
                continue

            if any(any(k not in item for k in update_keys) for item in batch):
                raise ValueError("All update items must share the same fields")

            values_map = {k: bindparam(k) for k in update_keys}
            stmt = (
                update(model_class)
                .where(getattr(model_class, key_field) == bindparam(key_field))
                .values(**values_map)
            )
            result = await self.db.execute(stmt, batch)
            total_updated += result.rowcount
            
            logger.debug(f"批量更新: {len(batch)} 条记录")
        
        await self.db.flush()
        logger.info(f"批量更新完成: 共 {total_updated} 条记录")
        
        return total_updated
    
    async def bulk_delete(
        self,
        model_class: Type[T],
        ids: List[Any],
        id_field: str = 'id'
    ) -> int:
        """
        批量删除
        
        Args:
            model_class: 模型类
            ids: ID 列表
            id_field: ID 字段名
        
        Returns:
            删除的记录数
        """
        if not ids:
            return 0
        
        total_deleted = 0
        
        for i in range(0, len(ids), self.batch_size):
            batch_ids = ids[i:i + self.batch_size]
            
            stmt = delete(model_class).where(
                getattr(model_class, id_field).in_(batch_ids)
            )
            result = await self.db.execute(stmt)
            total_deleted += result.rowcount
            
            logger.debug(f"批量删除: {len(batch_ids)} 条记录")
        
        await self.db.flush()
        logger.info(f"批量删除完成: 共 {total_deleted} 条记录")
        
        return total_deleted
    
    async def bulk_soft_delete(
        self,
        model_class: Type[T],
        ids: List[Any],
        id_field: str = 'id'
    ) -> int:
        """
        批量软删除
        
        Args:
            model_class: 模型类
            ids: ID 列表
            id_field: ID 字段名
        
        Returns:
            软删除的记录数
        """
        if not ids:
            return 0
        
        from datetime import datetime
        from module_admin.entity.do.enums import DelFlagEnum
        
        total_deleted = 0
        
        update_values = {}
        if hasattr(model_class, 'is_deleted'):
            update_values['is_deleted'] = True
            if hasattr(model_class, 'deleted_at'):
                update_values['deleted_at'] = datetime.now()
        if hasattr(model_class, 'del_flag'):
            update_values['del_flag'] = DelFlagEnum.DELETED.value
            if hasattr(model_class, 'update_time'):
                update_values['update_time'] = datetime.now()

        if not update_values:
            logger.warning(f"{model_class.__name__} does not support soft delete fields")
            return 0

        for i in range(0, len(ids), self.batch_size):
            batch_ids = ids[i:i + self.batch_size]
            
            stmt = update(model_class).where(
                getattr(model_class, id_field).in_(batch_ids)
            ).values(**update_values)
            result = await self.db.execute(stmt)
            total_deleted += result.rowcount
            
            logger.debug(f"批量软删除: {len(batch_ids)} 条记录")
        
        await self.db.flush()
        logger.info(f"批量软删除完成: 共 {total_deleted} 条记录")
        
        return total_deleted


class BulkLoader:
    """
    批量数据加载器
    
    用于高效加载大量数据
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化批量加载器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._buffer = {}
    
    def add(self, model_class: Type[T], data: Dict[str, Any]):
        """
        添加数据到缓冲区
        
        Args:
            model_class: 模型类
            data: 数据字典
        """
        model_name = model_class.__name__
        if model_name not in self._buffer:
            self._buffer[model_name] = {
                'model_class': model_class,
                'data': []
            }
        self._buffer[model_name]['data'].append(data)
    
    async def flush(self, batch_size: int = 1000):
        """
        刷新缓冲区，执行批量插入
        
        Args:
            batch_size: 批次大小
        """
        bulk_ops = BulkOperations(self.db, batch_size)
        
        for model_name, buffer_data in self._buffer.items():
            model_class = buffer_data['model_class']
            data_list = buffer_data['data']
            
            if data_list:
                await bulk_ops.bulk_insert(model_class, data_list)
                logger.info(f"已刷新 {model_name}: {len(data_list)} 条记录")
        
        # 清空缓冲区
        self._buffer.clear()
    
    def clear(self):
        """清空缓冲区"""
        self._buffer.clear()


# 使用示例
"""
from utils.bulk_operations import BulkOperations, BulkLoader
from module_admin.entity.do.device_do import DeviceDO

# 1. 批量插入
bulk_ops = BulkOperations(db, batch_size=1000)

devices_data = [
    {'device_name': f'设备{i}', 'device_type': '传感器'}
    for i in range(10000)
]

count = await bulk_ops.bulk_insert(DeviceDO, devices_data)
print(f"插入了 {count} 条记录")

# 2. 批量插入或更新（MySQL）
devices_data = [
    {'device_id': 1, 'device_name': '设备01-更新', 'device_type': '传感器'},
    {'device_id': 2, 'device_name': '设备02-更新', 'device_type': '传感器'},
]

count = await bulk_ops.bulk_insert_or_update(
    DeviceDO,
    devices_data,
    index_elements=['device_id'],
    update_fields=['device_name', 'device_type']
)

# 3. 批量更新
updates = [
    {'device_id': 1, 'device_name': '新名称1'},
    {'device_id': 2, 'device_name': '新名称2'},
]

count = await bulk_ops.bulk_update(
    DeviceDO,
    updates,
    key_field='device_id'
)

# 4. 批量删除
ids = [1, 2, 3, 4, 5]
count = await bulk_ops.bulk_delete(DeviceDO, ids, id_field='device_id')

# 5. 批量软删除
count = await bulk_ops.bulk_soft_delete(DeviceDO, ids, id_field='device_id')

# 6. 使用批量加载器
loader = BulkLoader(db)

# 添加数据到缓冲区
for i in range(10000):
    loader.add(DeviceDO, {
        'device_name': f'设备{i}',
        'device_type': '传感器'
    })

# 刷新缓冲区（批量插入）
await loader.flush(batch_size=1000)

# 7. 在 Repository 中使用
class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bulk_ops = BulkOperations(db)
    
    async def create_many(self, devices_data: List[Dict]):
        return await self.bulk_ops.bulk_insert(DeviceDO, devices_data)
    
    async def update_many(self, updates: List[Dict]):
        return await self.bulk_ops.bulk_update(DeviceDO, updates, 'device_id')
    
    async def delete_many(self, device_ids: List[int]):
        return await self.bulk_ops.bulk_delete(DeviceDO, device_ids, 'device_id')

# 8. 性能对比示例
import time

# 传统方式（逐条插入）
start = time.time()
for i in range(10000):
    device = DeviceDO(device_name=f'设备{i}')
    db.add(device)
    await db.flush()
print(f"逐条插入耗时: {time.time() - start:.2f}秒")

# 批量插入
start = time.time()
devices_data = [
    {'device_name': f'设备{i}'}
    for i in range(10000)
]
await bulk_ops.bulk_insert(DeviceDO, devices_data)
print(f"批量插入耗时: {time.time() - start:.2f}秒")
"""
