import math
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import func, select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression
from typing import Optional, List
from utils.common_util import CamelCaseUtil


class PageResponseModel(BaseModel):
    """
    列表分页查询返回模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    rows: List = []
    page_num: Optional[int] = None
    page_size: Optional[int] = None
    total: int
    has_next: Optional[bool] = None


class PageUtil:
    """
    分页工具类
    """

    @classmethod
    def get_page_obj(cls, data_list: List, page_num: int, page_size: int):
        """
        输入数据列表data_list和分页信息，返回分页数据列表结果

        :param data_list: 原始数据列表
        :param page_num: 当前页码
        :param page_size: 当前页面数据量
        :return: 分页数据对象
        """
        # 计算起始索引和结束索引
        start = (page_num - 1) * page_size
        end = page_num * page_size

        # 根据计算得到的起始索引和结束索引对数据列表进行切片
        paginated_data = data_list[start:end]
        has_next = True if math.ceil(len(data_list) / page_size) > page_num else False

        result = PageResponseModel(rows=paginated_data, page_num=page_num, page_size=page_size, total=len(data_list), has_next=has_next)

        return result

    @classmethod
    async def paginate(cls, db: AsyncSession, query: Select, page_num: int, page_size: int, is_page: bool = False):
        """
        输入查询语句和分页信息，返回分页数据列表结果

        :param db: orm对象
        :param query: sqlalchemy查询语句
        :param page_num: 当前页码
        :param page_size: 当前页面数据量
        :param is_page: 是否开启分页
        :return: 分页数据对象
        """
        query = cls._prepend_update_time_order(query)
        if is_page:
            total = (await db.execute(select(func.count('*')).select_from(query.subquery()))).scalar()
            query_result = await db.execute(query.offset((page_num - 1) * page_size).limit(page_size))
            paginated_data = []
            for row in query_result:
                if row and len(row) == 1:
                    paginated_data.append(row[0])
                else:
                    paginated_data.append(row)
            has_next = math.ceil(total / page_size) > page_num
            result = PageResponseModel(rows=CamelCaseUtil.transform_result(paginated_data), page_num=page_num, page_size=page_size, total=total, has_next=has_next)
        else:
            query_result = await db.execute(query)
            no_paginated_data = []
            for row in query_result:
                if row and len(row) == 1:
                    no_paginated_data.append(row[0])
                else:
                    no_paginated_data.append(row)
            result = CamelCaseUtil.transform_result(no_paginated_data)

        return result

    @classmethod
    def _prepend_update_time_order(cls, query: Select) -> Select:
        """
        如果查询涉及包含update_time字段的模型，则优先按update_time倒序排序，保证最新记录优先。
        已经按update_time排序的查询不会重复处理。
        """
        if query.get_execution_options().get('skip_update_time_order'):
            return query

        update_time_column = cls._get_update_time_column(query)
        if update_time_column is None:
            return query

        def _is_update_time_clause(clause):
            target = clause.element if isinstance(clause, UnaryExpression) else clause
            try:
                return target.compare(update_time_column)
            except Exception:
                return False

        existing_order = cls._get_order_by_clauses(query)
        if existing_order and _is_update_time_clause(existing_order[0]):
            return query

        filtered_order = [clause for clause in existing_order if not _is_update_time_clause(clause)]
        query = query.order_by(None)
        return query.order_by(update_time_column.desc(), *filtered_order)

    @classmethod
    def _get_update_time_column(cls, query: Select):
        """
        从查询的列描述中提取第一个包含update_time字段的模型列。
        """
        for desc in getattr(query, 'column_descriptions', []):
            entity = desc.get('entity')
            if entity is not None and hasattr(entity, 'update_time'):
                return getattr(entity, 'update_time')

        for desc in getattr(query, 'column_descriptions', []):
            expr = desc.get('expr')
            if getattr(expr, 'name', None) == 'update_time':
                return expr

        return None

    @classmethod
    def _get_order_by_clauses(cls, query: Select) -> list:
        """
        兼容不同SQLAlchemy版本的order_by读取方式，返回当前查询的排序列表。
        """
        # SQLAlchemy 1.4/2.0内部属性名差异，这里做容错处理
        order_by_clauses = getattr(query, '_order_by_clauses', None)
        if order_by_clauses is None:
            order_by_clauses = getattr(query, '_order_by_clause', None)
        if order_by_clauses is None:
            return []

        # _order_by_clause可能是None、tuple或者ImmutableSequence
        if isinstance(order_by_clauses, (list, tuple)):
            return list(order_by_clauses)
        try:
            return list(order_by_clauses)
        except Exception:
            return []


def get_page_obj(data_list: List, page_num: int, page_size: int):
    """
    输入数据列表data_list和分页信息，返回分页数据列表结果

    :param data_list: 原始数据列表
    :param page_num: 当前页码
    :param page_size: 当前页面数据量
    :return: 分页数据对象
    """
    # 计算起始索引和结束索引
    start = (page_num - 1) * page_size
    end = page_num * page_size

    # 根据计算得到的起始索引和结束索引对数据列表进行切片
    paginated_data = data_list[start:end]
    has_next = True if math.ceil(len(data_list) / page_size) > page_num else False

    result = PageResponseModel(rows=paginated_data, page_num=page_num, page_size=page_size, total=len(data_list), has_next=has_next)

    return result
