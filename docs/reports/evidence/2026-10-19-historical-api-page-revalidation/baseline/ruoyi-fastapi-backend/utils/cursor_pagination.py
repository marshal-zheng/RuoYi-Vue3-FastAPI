"""
P1-019: 游标分页工具

游标分页（Cursor-based Pagination）比传统的 OFFSET 分页更高效：

OFFSET 分页的问题：
- SELECT * FROM logs OFFSET 10000 LIMIT 20
- 数据库需要扫描并跳过前 10000 条记录
- 页数越大，性能越差

游标分页的优势：
- SELECT * FROM logs WHERE id < 12345 ORDER BY id DESC LIMIT 20
- 直接定位到游标位置，使用索引快速查找
- 性能恒定，不随页数增长而下降

适用场景：
- 大数据量分页（如日志、消息、订单）
- 无限滚动加载
- 实时数据流

不适用场景：
- 需要跳转到特定页码
- 需要精确的总页数

使用示例：

```python
from utils.cursor_pagination import CursorPaginator

# 创建分页器
paginator = CursorPaginator(
    model=OperLogDO,
    cursor_field='oper_id',
    order_desc=True
)

# 分页查询
result = await paginator.paginate(
    db=session,
    page_size=20,
    cursor=12345,  # 上一页最后一条的 ID
    filters=[
        OperLogDO.status == 0,
        OperLogDO.oper_time > some_date
    ]
)

# 结果
{
    'rows': [...],
    'next_cursor': 12325,
    'has_more': True,
    'page_size': 20
}
```
"""

from typing import TypeVar, Generic, Optional, List, Any, Dict
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from utils.common_util import CamelCaseUtil


T = TypeVar('T')


class CursorPageResponse(BaseModel):
    """游标分页响应模型"""
    
    model_config = ConfigDict(alias_generator=to_camel)
    
    rows: List[Any] = []
    next_cursor: Optional[Any] = None
    prev_cursor: Optional[Any] = None
    has_more: bool = False
    has_prev: bool = False
    page_size: int = 20


class CursorPaginator(Generic[T]):
    """
    通用游标分页器
    
    支持任意模型的游标分页，使用主键或指定字段作为游标
    """
    
    def __init__(
        self,
        model: T,
        cursor_field: str = 'id',
        order_desc: bool = True
    ):
        """
        初始化游标分页器
        
        Args:
            model: SQLAlchemy 模型类
            cursor_field: 用作游标的字段名（应该是唯一且有序的，如主键）
            order_desc: 是否降序排列（True: 最新的在前，False: 最旧的在前）
        """
        self.model = model
        self.cursor_field = cursor_field
        self.order_desc = order_desc
    
    async def paginate(
        self,
        db: AsyncSession,
        page_size: int = 20,
        cursor: Optional[Any] = None,
        filters: Optional[List[BinaryExpression]] = None,
        transform: bool = True
    ) -> CursorPageResponse:
        """
        执行游标分页查询
        
        Args:
            db: 数据库会话
            page_size: 每页数量
            cursor: 游标值（上一页最后一条记录的游标字段值）
            filters: 额外的过滤条件列表
            transform: 是否转换为驼峰命名
        
        Returns:
            游标分页响应
        """
        cursor_column = getattr(self.model, self.cursor_field)
        
        # 构建条件
        conditions = filters.copy() if filters else []
        
        # 添加游标条件
        if cursor is not None:
            if self.order_desc:
                conditions.append(cursor_column < cursor)
            else:
                conditions.append(cursor_column > cursor)
        
        # 构建查询
        order_func = desc if self.order_desc else asc
        
        query = select(self.model)
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(order_func(cursor_column)).limit(page_size + 1)
        
        # 执行查询
        result = await db.execute(query)
        rows = result.scalars().all()
        
        # 判断是否有下一页
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]
        
        # 计算游标
        if rows:
            next_cursor = getattr(rows[-1], self.cursor_field)
        else:
            next_cursor = None
        
        # 转换结果
        if transform:
            transformed_rows = CamelCaseUtil.transform_result(rows)
        else:
            transformed_rows = rows
        
        return CursorPageResponse(
            rows=transformed_rows,
            next_cursor=next_cursor,
            has_more=has_more,
            has_prev=cursor is not None,
            page_size=page_size
        )
    
    async def paginate_bidirectional(
        self,
        db: AsyncSession,
        page_size: int = 20,
        cursor: Optional[Any] = None,
        direction: str = 'next',
        filters: Optional[List[BinaryExpression]] = None,
        transform: bool = True
    ) -> CursorPageResponse:
        """
        双向游标分页（支持向前和向后翻页）
        
        Args:
            db: 数据库会话
            page_size: 每页数量
            cursor: 游标值
            direction: 翻页方向 ('next' 或 'prev')
            filters: 额外的过滤条件
            transform: 是否转换为驼峰命名
        
        Returns:
            游标分页响应
        """
        cursor_column = getattr(self.model, self.cursor_field)
        
        # 构建条件
        conditions = filters.copy() if filters else []
        
        # 根据方向确定查询顺序和游标条件
        if direction == 'next':
            is_forward = True
        else:
            is_forward = False
        
        # 添加游标条件
        if cursor is not None:
            if self.order_desc:
                if is_forward:
                    conditions.append(cursor_column < cursor)
                else:
                    conditions.append(cursor_column > cursor)
            else:
                if is_forward:
                    conditions.append(cursor_column > cursor)
                else:
                    conditions.append(cursor_column < cursor)
        
        # 确定排序方向
        if self.order_desc:
            order_func = desc if is_forward else asc
        else:
            order_func = asc if is_forward else desc
        
        # 构建查询
        query = select(self.model)
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(order_func(cursor_column)).limit(page_size + 1)
        
        # 执行查询
        result = await db.execute(query)
        rows = result.scalars().all()
        
        # 判断是否有更多
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]
        
        # 如果是向前翻页，需要反转结果
        if not is_forward:
            rows = list(reversed(rows))
        
        # 计算游标
        if rows:
            next_cursor = getattr(rows[-1], self.cursor_field)
            prev_cursor = getattr(rows[0], self.cursor_field)
        else:
            next_cursor = None
            prev_cursor = None
        
        # 转换结果
        if transform:
            transformed_rows = CamelCaseUtil.transform_result(rows)
        else:
            transformed_rows = rows
        
        return CursorPageResponse(
            rows=transformed_rows,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_more=has_more if is_forward else cursor is not None,
            has_prev=cursor is not None if is_forward else has_more,
            page_size=page_size
        )


# 辅助函数
def encode_cursor(value: Any) -> str:
    """
    编码游标值为字符串（用于 API 响应）
    
    Args:
        value: 游标值
    
    Returns:
        编码后的字符串
    """
    import base64
    import json
    
    if value is None:
        return None
    
    # 简单的 base64 编码
    data = json.dumps({'v': value})
    return base64.urlsafe_b64encode(data.encode()).decode()


def decode_cursor(cursor_str: str) -> Any:
    """
    解码游标字符串
    
    Args:
        cursor_str: 编码的游标字符串
    
    Returns:
        解码后的游标值
    """
    import base64
    import json
    
    if not cursor_str:
        return None
    
    data = base64.urlsafe_b64decode(cursor_str.encode()).decode()
    return json.loads(data)['v']
