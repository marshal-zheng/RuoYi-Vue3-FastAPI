"""
Specification 规范模式
提供灵活的查询条件组合能力
"""
from abc import ABC, abstractmethod
from typing import Any, List
from sqlalchemy import and_, or_, not_


class Specification(ABC):
    """
    规范接口
    
    定义查询规范的基本行为
    支持规范的组合（与、或、非）
    """
    
    @abstractmethod
    def apply(self, query):
        """
        应用规范到查询
        
        Args:
            query: SQLAlchemy 查询对象
        
        Returns:
            应用了规范的查询对象
        """
        pass

    def to_condition(self):
        """返回条件表达式（用于组合规范）"""
        return None
    
    def __and__(self, other: 'Specification') -> 'Specification':
        """与操作"""
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification') -> 'Specification':
        """或操作"""
        return OrSpecification(self, other)
    
    def __invert__(self) -> 'Specification':
        """非操作"""
        return NotSpecification(self)


class AndSpecification(Specification):
    """与规范 - 组合多个规范（AND）"""
    
    def __init__(self, *specs: Specification):
        self.specs = specs
    
    def apply(self, query):
        condition = self.to_condition()
        if condition is None:
            return query
        return query.where(condition)

    def to_condition(self):
        conditions = []
        for spec in self.specs:
            if not spec:
                continue
            condition = spec.to_condition()
            if condition is None:
                raise ValueError("All specifications in AND must provide conditions")
            conditions.append(condition)

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return and_(*conditions)


class OrSpecification(Specification):
    """或规范 - 组合多个规范（OR）"""
    
    def __init__(self, *specs: Specification):
        self.specs = specs
    
    def apply(self, query):
        condition = self.to_condition()
        if condition is None:
            return query
        return query.where(condition)

    def to_condition(self):
        conditions = []
        for spec in self.specs:
            if not spec:
                continue
            condition = spec.to_condition()
            if condition is None:
                raise ValueError("All specifications in OR must provide conditions")
            conditions.append(condition)

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return or_(*conditions)


class NotSpecification(Specification):
    """非规范 - 取反规范"""
    
    def __init__(self, spec: Specification):
        self.spec = spec
    
    def apply(self, query):
        condition = self.to_condition()
        if condition is None:
            return query
        return query.where(condition)

    def to_condition(self):
        condition = self.spec.to_condition()
        if condition is None:
            raise ValueError("NOT specification requires a condition")
        return not_(condition)


class BaseSpecification(Specification):
    """
    基础规范类
    
    提供通用的规范实现
    """
    
    def __init__(self, condition=None):
        self.condition = condition
    
    def apply(self, query):
        if self.condition is not None:
            return query.where(self.condition)
        return query
    
    def to_condition(self):
        """转换为条件表达式"""
        return self.condition


class EqualsSpecification(BaseSpecification):
    """等于规范"""
    
    def __init__(self, field, value):
        super().__init__(field == value)


class NotEqualsSpecification(BaseSpecification):
    """不等于规范"""
    
    def __init__(self, field, value):
        super().__init__(field != value)


class LikeSpecification(BaseSpecification):
    """模糊匹配规范"""
    
    def __init__(self, field, pattern: str):
        super().__init__(field.like(f'%{pattern}%'))


class InSpecification(BaseSpecification):
    """IN 规范"""
    
    def __init__(self, field, values: List[Any]):
        super().__init__(field.in_(values))


class NotInSpecification(BaseSpecification):
    """NOT IN 规范"""
    
    def __init__(self, field, values: List[Any]):
        super().__init__(field.notin_(values))


class BetweenSpecification(BaseSpecification):
    """范围规范"""
    
    def __init__(self, field, start, end):
        super().__init__(field.between(start, end))


class GreaterThanSpecification(BaseSpecification):
    """大于规范"""
    
    def __init__(self, field, value):
        super().__init__(field > value)


class GreaterThanOrEqualSpecification(BaseSpecification):
    """大于等于规范"""
    
    def __init__(self, field, value):
        super().__init__(field >= value)


class LessThanSpecification(BaseSpecification):
    """小于规范"""
    
    def __init__(self, field, value):
        super().__init__(field < value)


class LessThanOrEqualSpecification(BaseSpecification):
    """小于等于规范"""
    
    def __init__(self, field, value):
        super().__init__(field <= value)


class IsNullSpecification(BaseSpecification):
    """为空规范"""
    
    def __init__(self, field):
        super().__init__(field.is_(None))


class IsNotNullSpecification(BaseSpecification):
    """不为空规范"""
    
    def __init__(self, field):
        super().__init__(field.isnot(None))


class OrderBySpecification(Specification):
    """排序规范"""
    
    def __init__(self, *order_fields):
        self.order_fields = order_fields
    
    def apply(self, query):
        return query.order_by(*self.order_fields)


class LimitSpecification(Specification):
    """限制数量规范"""
    
    def __init__(self, limit: int):
        self.limit = limit
    
    def apply(self, query):
        return query.limit(self.limit)


class OffsetSpecification(Specification):
    """偏移规范"""
    
    def __init__(self, offset: int):
        self.offset = offset
    
    def apply(self, query):
        return query.offset(self.offset)


# 工厂函数 - 提供更简洁的 API
def equals(field, value) -> Specification:
    """等于"""
    return EqualsSpecification(field, value)


def not_equals(field, value) -> Specification:
    """不等于"""
    return NotEqualsSpecification(field, value)


def like(field, pattern: str) -> Specification:
    """模糊匹配"""
    return LikeSpecification(field, pattern)


def in_(field, values: List[Any]) -> Specification:
    """IN"""
    return InSpecification(field, values)


def not_in(field, values: List[Any]) -> Specification:
    """NOT IN"""
    return NotInSpecification(field, values)


def between(field, start, end) -> Specification:
    """范围"""
    return BetweenSpecification(field, start, end)


def gt(field, value) -> Specification:
    """大于"""
    return GreaterThanSpecification(field, value)


def gte(field, value) -> Specification:
    """大于等于"""
    return GreaterThanOrEqualSpecification(field, value)


def lt(field, value) -> Specification:
    """小于"""
    return LessThanSpecification(field, value)


def lte(field, value) -> Specification:
    """小于等于"""
    return LessThanOrEqualSpecification(field, value)


def is_null(field) -> Specification:
    """为空"""
    return IsNullSpecification(field)


def is_not_null(field) -> Specification:
    """不为空"""
    return IsNotNullSpecification(field)


def order_by(*fields) -> Specification:
    """排序"""
    return OrderBySpecification(*fields)


def limit(count: int) -> Specification:
    """限制数量"""
    return LimitSpecification(count)


def offset(count: int) -> Specification:
    """偏移"""
    return OffsetSpecification(count)


# 使用示例
"""
from module_admin.entity.do.device_do import DeviceDO
from module_admin.repository.specification import *

# 1. 简单规范
spec = equals(DeviceDO.device_name, "传感器01")

# 2. 模糊查询
spec = like(DeviceDO.device_name, "传感器")

# 3. 组合规范（AND）
spec = (
    like(DeviceDO.device_name, "传感器") & 
    equals(DeviceDO.device_type, "温度传感器")
)

# 4. 组合规范（OR）
spec = (
    equals(DeviceDO.device_type, "温度传感器") | 
    equals(DeviceDO.device_type, "湿度传感器")
)

# 5. 复杂组合
spec = (
    like(DeviceDO.device_name, "传感器") &
    (equals(DeviceDO.device_type, "温度传感器") | 
     equals(DeviceDO.device_type, "湿度传感器")) &
    gte(DeviceDO.create_time, datetime(2024, 1, 1))
)

# 6. 在 Repository 中使用
from sqlalchemy import select

async def find_by_spec(db: AsyncSession, spec: Specification):
    stmt = select(DeviceDO)
    stmt = spec.apply(stmt)
    result = await db.execute(stmt)
    return result.scalars().all()

# 7. 扩展 Repository 支持规范模式
class DeviceRepository(BaseRepository[DeviceDO]):
    async def find_by_specification(self, spec: Specification) -> List[DeviceDO]:
        stmt = select(self.model_class)
        stmt = spec.apply(stmt)
        result = await self.db.execute(stmt)
        return result.scalars().all()

# 使用
device_repo = DeviceRepository(db)
spec = like(DeviceDO.device_name, "传感器") & equals(DeviceDO.bus_type, "CAN")
devices = await device_repo.find_by_specification(spec)
"""
