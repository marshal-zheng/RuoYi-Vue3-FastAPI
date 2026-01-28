"""
Repository 模式实现
提供统一的数据访问抽象层，隔离业务逻辑和数据库操作
"""
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Type, Any, Dict, Sequence
from sqlalchemy import select, delete, func, and_, or_, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from utils.count_cache import get_count_cache
from module_admin.entity.do.enums import DelFlagEnum

logger = logging.getLogger(__name__)


T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Repository 接口
    
    定义数据访问层的标准操作
    所有 Repository 必须实现此接口
    """
    
    @abstractmethod
    async def get_by_id(
        self,
        id: Any,
        relations: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> Optional[T]:
        """根据ID获取单条记录"""
        pass
    
    @abstractmethod
    async def find_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        relations: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[T]:
        """查找所有记录（支持过滤、排序、分页）"""
        pass
    
    @abstractmethod
    async def find_one(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> Optional[T]:
        """查找单条记录（支持过滤）"""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """添加记录"""
        pass
    
    @abstractmethod
    async def add_all(self, entities: List[T]) -> List[T]:
        """批量添加记录"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete_by_id(self, id: Any) -> bool:
        """根据ID删除记录"""
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: List[Any]) -> int:
        """批量删除记录"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False) -> int:
        """统计记录数（支持过滤）"""
        pass
    
    @abstractmethod
    async def exists(self, filters: Optional[Dict[str, Any]] = None) -> bool:
        """判断记录是否存在（支持过滤）"""
        pass


class BaseRepository(IRepository[T]):
    """
    基础 Repository 实现
    
    提供通用的 CRUD 操作实现
    子类可以继承并扩展特定的查询方法
    
    特性：
    - 写操作（add/delete）后自动失效对应表的 COUNT 缓存
    - 支持软删除
    - 支持分页查询
    """
    
    def __init__(self, db: AsyncSession, model_class: Type[T]):
        """
        初始化 Repository
        
        Args:
            db: 数据库会话
            model_class: 模型类
        """
        self.db = db
        self.model_class = model_class
        self._table_name = getattr(model_class, '__tablename__', None)
    
    async def _invalidate_count_cache(self):
        """
        失效当前表的 COUNT 缓存
        
        在写操作后调用，确保下次分页查询能获取最新的总数
        """
        if not self._table_name:
            return
        
        count_cache = get_count_cache()
        if count_cache.enabled:
            await count_cache.invalidate_table(self._table_name)
            logger.debug(f"已失效表 '{self._table_name}' 的 COUNT 缓存")

    def _get_pk_columns(self) -> Sequence:
        """获取模型主键列"""
        mapper = inspect(self.model_class)
        return mapper.primary_key

    def _get_single_pk_column(self):
        """获取单一主键列（如复合主键则抛出异常）"""
        pk_columns = self._get_pk_columns()
        if len(pk_columns) != 1:
            raise ValueError("Composite primary key requires dict or tuple")
        return pk_columns[0]

    def _build_pk_condition(self, id_value: Any):
        """构建主键查询条件（支持单主键或复合主键）"""
        pk_columns = self._get_pk_columns()
        if len(pk_columns) == 1:
            return pk_columns[0] == id_value

        if isinstance(id_value, dict):
            missing = [col.key for col in pk_columns if col.key not in id_value]
            if missing:
                raise ValueError(f"Missing primary key fields: {','.join(missing)}")
            return and_(*[col == id_value[col.key] for col in pk_columns])

        if isinstance(id_value, (list, tuple)) and len(id_value) == len(pk_columns):
            return and_(*[col == val for col, val in zip(pk_columns, id_value)])

        raise ValueError("Composite primary key requires dict or tuple")
    
    async def get_by_id(
        self,
        id: Any,
        relations: List[str] = None,
        include_deleted: bool = False
    ) -> Optional[T]:
        """
        根据ID获取单条记录
        
        Args:
            id: 主键ID
            relations: 需要预加载的关系列表
            include_deleted: 是否包含已删除记录
        
        Returns:
            查询结果或 None
        """
        stmt = select(self.model_class).where(self._build_pk_condition(id))
        if include_deleted:
            stmt = stmt.execution_options(include_deleted=True)
        
        if relations:
            for relation in relations:
                stmt = stmt.options(selectinload(getattr(self.model_class, relation)))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_all(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        relations: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[T]:
        """
        查找所有记录
        
        Args:
            filters: 过滤条件字典
            order_by: 排序字段列表
            limit: 限制数量
            offset: 偏移量
            relations: 需要预加载的关系列表
            include_deleted: 是否包含已删除记录
        
        Returns:
            记录列表
        """
        stmt = select(self.model_class)
        
        # 应用过滤条件
        if filters:
            conditions = [getattr(self.model_class, k) == v for k, v in filters.items()]
            stmt = stmt.where(and_(*conditions))
        
        # 软删除过滤
        if not include_deleted and hasattr(self.model_class, 'is_deleted'):
            stmt = stmt.where(
                or_(
                    self.model_class.is_deleted == False,
                    self.model_class.is_deleted.is_(None)
                )
            )
        if include_deleted:
            stmt = stmt.execution_options(include_deleted=True)
        
        # 预加载关系
        if relations:
            for relation in relations:
                stmt = stmt.options(selectinload(getattr(self.model_class, relation)))
        
        # 排序
        if order_by:
            stmt = stmt.order_by(*order_by)
        
        # 分页
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_one(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> Optional[T]:
        """
        查找单条记录
        
        Args:
            **filters: 过滤条件
            include_deleted: 是否包含已删除记录
        
        Returns:
            查询结果或 None
        """
        results = await self.find_all(
            filters=filters,
            limit=1,
            include_deleted=include_deleted
        )
        return results[0] if results else None
    
    async def add(self, entity: T) -> T:
        """
        添加记录
        
        Args:
            entity: 实体对象
        
        Returns:
            添加后的实体（包含生成的ID）
        
        Note:
            添加后会自动失效对应表的 COUNT 缓存
        """
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        await self._invalidate_count_cache()
        return entity
    
    async def add_all(self, entities: List[T]) -> List[T]:
        """
        批量添加记录
        
        Args:
            entities: 实体列表
        
        Returns:
            添加后的实体列表
        
        Note:
            添加后会自动失效对应表的 COUNT 缓存
        """
        self.db.add_all(entities)
        await self.db.flush()
        for entity in entities:
            await self.db.refresh(entity)
        await self._invalidate_count_cache()
        return entities
    
    async def update(self, entity: T) -> T:
        """
        更新记录
        
        Args:
            entity: 实体对象
        
        Returns:
            更新后的实体
        """
        await self.db.merge(entity)
        await self.db.flush()
        return entity
    
    async def delete_by_id(self, id: Any) -> bool:
        """
        根据ID删除记录（物理删除）
        
        Args:
            id: 主键ID
        
        Returns:
            是否删除成功
        
        Note:
            删除后会自动失效对应表的 COUNT 缓存
        """
        stmt = delete(self.model_class).where(self._build_pk_condition(id))
        result = await self.db.execute(stmt)
        if result.rowcount > 0:
            await self._invalidate_count_cache()
            return True
        return False
    
    async def delete_by_ids(self, ids: List[Any]) -> int:
        """
        批量删除记录（物理删除）
        
        Args:
            ids: 主键ID列表
        
        Returns:
            删除的记录数
        
        Note:
            删除后会自动失效对应表的 COUNT 缓存
        """
        if not ids:
            return 0
        pk_column = self._get_single_pk_column()
        stmt = delete(self.model_class).where(pk_column.in_(ids))
        result = await self.db.execute(stmt)
        if result.rowcount > 0:
            await self._invalidate_count_cache()
        return result.rowcount
    
    async def soft_delete_by_id(self, id: Any) -> bool:
        """
        软删除记录
        
        Args:
            id: 主键ID
        
        Returns:
            是否删除成功
        
        Note:
            软删除后会自动失效对应表的 COUNT 缓存
        """
        entity = await self.get_by_id(id)
        if not entity:
            return False
        if hasattr(entity, 'soft_delete'):
            entity.soft_delete()
        elif hasattr(entity, 'del_flag'):
            setattr(entity, 'del_flag', DelFlagEnum.DELETED.value)
            if hasattr(entity, 'update_time'):
                setattr(entity, 'update_time', datetime.now())
        else:
            return False
        await self.update(entity)
        await self._invalidate_count_cache()
        return True
    
    async def soft_delete_by_ids(self, ids: List[Any]) -> int:
        """
        批量软删除
        
        Args:
            ids: 主键ID列表
        
        Returns:
            删除的记录数
        
        Note:
            软删除后会自动失效对应表的 COUNT 缓存
        """
        count = 0
        for entity_id in ids:
            entity = await self.get_by_id(entity_id)
            if not entity:
                continue
            if hasattr(entity, 'soft_delete'):
                entity.soft_delete()
            elif hasattr(entity, 'del_flag'):
                setattr(entity, 'del_flag', DelFlagEnum.DELETED.value)
                if hasattr(entity, 'update_time'):
                    setattr(entity, 'update_time', datetime.now())
            else:
                continue
            await self.update(entity)
            count += 1
        if count > 0:
            await self._invalidate_count_cache()
        return count
    
    async def count(self, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False) -> int:
        """
        统计记录数
        
        Args:
            filters: 过滤条件字典
            include_deleted: 是否包含已删除记录
        
        Returns:
            记录总数
        """
        stmt = select(func.count()).select_from(self.model_class)
        
        # 应用过滤条件
        if filters:
            conditions = [getattr(self.model_class, k) == v for k, v in filters.items()]
            stmt = stmt.where(and_(*conditions))
        
        # 软删除过滤
        if not include_deleted and hasattr(self.model_class, 'is_deleted'):
            stmt = stmt.where(
                or_(
                    self.model_class.is_deleted == False,
                    self.model_class.is_deleted.is_(None)
                )
            )
        if include_deleted:
            stmt = stmt.execution_options(include_deleted=True)
        
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def exists(self, filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        判断记录是否存在
        
        Args:
            **filters: 过滤条件
        
        Returns:
            是否存在
        """
        count = await self.count(filters=filters)
        return count > 0
    
    async def paginate(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List] = None,
        relations: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> tuple[List[T], int]:
        """
        分页查询
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            filters: 过滤条件
            order_by: 排序字段
            relations: 需要预加载的关系
            include_deleted: 是否包含已删除记录
        
        Returns:
            (记录列表, 总记录数)
        """
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询数据
        items = await self.find_all(
            filters=filters,
            order_by=order_by,
            limit=page_size,
            offset=offset,
            relations=relations,
            include_deleted=include_deleted
        )
        
        # 查询总数
        total = await self.count(filters=filters, include_deleted=include_deleted)
        
        return items, total
