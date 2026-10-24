"""
QueryBuilder 查询构建器
提供流式 API 构建复杂查询
"""
from typing import Generic, TypeVar, List, Optional, Type, Any
from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload


T = TypeVar('T')


class QueryBuilder(Generic[T]):
    """
    流式查询构建器
    
    提供链式 API 构建查询，支持：
    - 条件过滤
    - 排序
    - 分页
    - 关系预加载
    - 聚合函数
    """
    
    def __init__(self, db: AsyncSession, model_class: Type[T]):
        """
        初始化查询构建器
        
        Args:
            db: 数据库会话
            model_class: 模型类
        """
        self.db = db
        self.model_class = model_class
        self._stmt = select(model_class)
        self._filters = []
        self._orders = []
        self._limit_value = None
        self._offset_value = None
        self._relations = []
        self._join_relations = []
        self._group_by_fields = []
        self._include_deleted = False
    
    def where(self, *conditions) -> 'QueryBuilder[T]':
        """
        添加 WHERE 条件
        
        Args:
            *conditions: 条件表达式
        
        Returns:
            self（支持链式调用）
        """
        self._filters.extend(conditions)
        return self
    
    def filter(self, **kwargs) -> 'QueryBuilder[T]':
        """
        通过字典添加过滤条件
        
        Args:
            **kwargs: 字段名=值 的过滤条件
        
        Returns:
            self（支持链式调用）
        """
        for key, value in kwargs.items():
            field = getattr(self.model_class, key)
            self._filters.append(field == value)
        return self
    
    def filter_like(self, field_name: str, pattern: str) -> 'QueryBuilder[T]':
        """
        模糊查询
        
        Args:
            field_name: 字段名
            pattern: 匹配模式
        
        Returns:
            self（支持链式调用）
        """
        field = getattr(self.model_class, field_name)
        self._filters.append(field.like(f'%{pattern}%'))
        return self
    
    def filter_in(self, field_name: str, values: List[Any]) -> 'QueryBuilder[T]':
        """
        IN 查询
        
        Args:
            field_name: 字段名
            values: 值列表
        
        Returns:
            self（支持链式调用）
        """
        if values:
            field = getattr(self.model_class, field_name)
            self._filters.append(field.in_(values))
        return self
    
    def filter_between(self, field_name: str, start, end) -> 'QueryBuilder[T]':
        """
        范围查询
        
        Args:
            field_name: 字段名
            start: 起始值
            end: 结束值
        
        Returns:
            self（支持链式调用）
        """
        field = getattr(self.model_class, field_name)
        self._filters.append(field.between(start, end))
        return self
    
    def filter_null(self, field_name: str, is_null: bool = True) -> 'QueryBuilder[T]':
        """
        NULL 查询
        
        Args:
            field_name: 字段名
            is_null: True=IS NULL, False=IS NOT NULL
        
        Returns:
            self（支持链式调用）
        """
        field = getattr(self.model_class, field_name)
        if is_null:
            self._filters.append(field.is_(None))
        else:
            self._filters.append(field.isnot(None))
        return self
    
    def order_by(self, *fields) -> 'QueryBuilder[T]':
        """
        添加排序
        
        Args:
            *fields: 排序字段（可以是 field.desc() 或 field.asc()）
        
        Returns:
            self（支持链式调用）
        """
        self._orders.extend(fields)
        return self
    
    def order_by_desc(self, field_name: str) -> 'QueryBuilder[T]':
        """
        降序排序
        
        Args:
            field_name: 字段名
        
        Returns:
            self（支持链式调用）
        """
        field = getattr(self.model_class, field_name)
        self._orders.append(field.desc())
        return self
    
    def order_by_asc(self, field_name: str) -> 'QueryBuilder[T]':
        """
        升序排序
        
        Args:
            field_name: 字段名
        
        Returns:
            self（支持链式调用）
        """
        field = getattr(self.model_class, field_name)
        self._orders.append(field.asc())
        return self
    
    def limit(self, value: int) -> 'QueryBuilder[T]':
        """
        限制数量
        
        Args:
            value: 限制数量
        
        Returns:
            self（支持链式调用）
        """
        self._limit_value = value
        return self
    
    def offset(self, value: int) -> 'QueryBuilder[T]':
        """
        偏移量
        
        Args:
            value: 偏移量
        
        Returns:
            self（支持链式调用）
        """
        self._offset_value = value
        return self
    
    def paginate(self, page: int, page_size: int) -> 'QueryBuilder[T]':
        """
        分页
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
        
        Returns:
            self（支持链式调用）
        """
        self._offset_value = (page - 1) * page_size
        self._limit_value = page_size
        return self

    def include_deleted(self, include: bool = True) -> 'QueryBuilder[T]':
        """
        是否包含已删除记录（绕过软删除过滤）

        Args:
            include: True=包含已删除记录

        Returns:
            self（支持链式调用）
        """
        self._include_deleted = include
        return self
    
    def with_relations(self, *relation_names: str, strategy: str = 'selectinload') -> 'QueryBuilder[T]':
        """
        预加载关系
        
        Args:
            *relation_names: 关系名称列表
            strategy: 加载策略 ('selectinload' 或 'joinedload')
        
        Returns:
            self（支持链式调用）
        """
        for relation_name in relation_names:
            if strategy == 'selectinload':
                self._relations.append(relation_name)
            elif strategy == 'joinedload':
                self._join_relations.append(relation_name)
        return self
    
    def group_by(self, *fields) -> 'QueryBuilder[T]':
        """
        分组
        
        Args:
            *fields: 分组字段
        
        Returns:
            self（支持链式调用）
        """
        self._group_by_fields.extend(fields)
        return self
    
    def _build_statement(self):
        """构建 SQL 语句"""
        stmt = self._stmt
        
        # 应用过滤条件
        if self._filters:
            stmt = stmt.where(and_(*self._filters))
        
        # 预加载关系（selectinload）
        for relation_name in self._relations:
            relation = getattr(self.model_class, relation_name)
            stmt = stmt.options(selectinload(relation))
        
        # 预加载关系（joinedload）
        for relation_name in self._join_relations:
            relation = getattr(self.model_class, relation_name)
            stmt = stmt.options(joinedload(relation))
        
        # 分组
        if self._group_by_fields:
            stmt = stmt.group_by(*self._group_by_fields)
        
        # 排序
        if self._orders:
            stmt = stmt.order_by(*self._orders)
        
        # 分页
        if self._offset_value is not None:
            stmt = stmt.offset(self._offset_value)
        if self._limit_value is not None:
            stmt = stmt.limit(self._limit_value)
        return self._apply_execution_options(stmt)

    def _apply_execution_options(self, stmt):
        """应用执行选项"""
        if self._include_deleted:
            stmt = stmt.execution_options(include_deleted=True)
        return stmt
    
    async def get_one(self) -> Optional[T]:
        """
        获取单条记录
        
        Returns:
            记录对象或 None
        """
        stmt = self._build_statement()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_first(self) -> Optional[T]:
        """
        获取第一条记录
        
        Returns:
            记录对象或 None
        """
        stmt = self._build_statement().limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_many(self) -> List[T]:
        """
        获取多条记录
        
        Returns:
            记录列表
        """
        stmt = self._build_statement()
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_all(self) -> List[T]:
        """
        获取所有记录（别名）
        
        Returns:
            记录列表
        """
        return await self.get_many()
    
    async def count(self) -> int:
        """
        统计记录数
        
        Returns:
            记录总数
        """
        stmt = select(func.count()).select_from(self.model_class)
        if self._filters:
            stmt = stmt.where(and_(*self._filters))
        stmt = self._apply_execution_options(stmt)
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def exists(self) -> bool:
        """
        判断是否存在记录
        
        Returns:
            是否存在
        """
        count = await self.count()
        return count > 0
    
    async def paginate_result(self) -> tuple[List[T], int]:
        """
        分页查询（返回结果和总数）
        
        Returns:
            (记录列表, 总记录数)
        """
        items = await self.get_many()
        total = await self.count()
        return items, total
    
    async def delete(self) -> int:
        """
        删除记录
        
        Returns:
            删除的记录数
        """
        stmt = delete(self.model_class)
        if self._filters:
            stmt = stmt.where(and_(*self._filters))
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def update(self, **values) -> int:
        """
        更新记录
        
        Args:
            **values: 要更新的字段和值
        
        Returns:
            更新的记录数
        """
        stmt = update(self.model_class)
        if self._filters:
            stmt = stmt.where(and_(*self._filters))
        stmt = stmt.values(**values)
        result = await self.db.execute(stmt)
        return result.rowcount


# 使用示例
"""
from module_admin.entity.do.device_do import DeviceDO
from module_admin.repository.query_builder import QueryBuilder

# 1. 基础查询
query = QueryBuilder(db, DeviceDO)
devices = await query.filter(device_type="传感器").get_many()

# 2. 复杂查询（链式调用）
devices = await (
    QueryBuilder(db, DeviceDO)
    .filter_like("device_name", "传感器")
    .filter(bus_type="CAN")
    .order_by_desc("create_time")
    .limit(10)
    .get_many()
)

# 3. 分页查询
devices, total = await (
    QueryBuilder(db, DeviceDO)
    .filter_like("device_name", "传感器")
    .paginate(page=1, page_size=10)
    .order_by_desc("create_time")
    .paginate_result()
)

# 4. 预加载关系
device = await (
    QueryBuilder(db, DeviceDO)
    .filter(device_id=1)
    .with_relations("interfaces", "category")
    .get_one()
)

# 5. 统计
count = await (
    QueryBuilder(db, DeviceDO)
    .filter(device_type="传感器")
    .count()
)

# 6. 判断存在
exists = await (
    QueryBuilder(db, DeviceDO)
    .filter(device_name="传感器01")
    .exists()
)

# 7. 批量更新
updated = await (
    QueryBuilder(db, DeviceDO)
    .filter(device_type="旧类型")
    .update(device_type="新类型")
)

# 8. 批量删除
deleted = await (
    QueryBuilder(db, DeviceDO)
    .filter_in("device_id", [1, 2, 3])
    .delete()
)

# 9. 在 Repository 中集成
class DeviceRepository(BaseRepository[DeviceDO]):
    def query(self) -> QueryBuilder[DeviceDO]:
        '''创建查询构建器'''
        return QueryBuilder(self.db, self.model_class)
    
    async def find_active_devices(self):
        return await (
            self.query()
            .filter(status="0")
            .order_by_desc("create_time")
            .get_many()
        )

# 使用
repo = DeviceRepository(db)
devices = await repo.find_active_devices()
"""
