"""
代码生成器 Repository 层
提供代码生成业务表和字段的数据访问操作
"""
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlglot.expressions import Expression

from config.env import DataBaseConfig
from module_generator.entity.do.gen_do import GenTableDO, GenTableColumnDO
from module_generator.entity.vo.gen_vo import (
    GenTableBaseModel,
    GenTableColumnBaseModel,
)
from utils.page_util import PageUtil


class GenTableRepository:
    """
    代码生成业务表 Repository
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_id(self, table_id: int) -> Optional[GenTableDO]:
        """
        根据业务表ID获取业务表信息（包含字段列表）
        
        :param table_id: 业务表ID
        :return: 业务表对象
        """
        result = await self.db.execute(
            select(GenTableDO)
            .options(selectinload(GenTableDO.columns))
            .where(GenTableDO.table_id == table_id)
        )
        return result.scalars().first()
    
    async def find_by_name(self, table_name: str) -> Optional[GenTableDO]:
        """
        根据业务表名称获取业务表信息（包含字段列表）
        
        :param table_name: 业务表名称
        :return: 业务表对象
        """
        result = await self.db.execute(
            select(GenTableDO)
            .options(selectinload(GenTableDO.columns))
            .where(GenTableDO.table_name == table_name)
        )
        return result.scalars().first()
    
    async def find_all(self) -> List[GenTableDO]:
        """
        获取所有业务表信息
        
        :return: 业务表列表
        """
        result = await self.db.execute(
            select(GenTableDO).options(selectinload(GenTableDO.columns))
        )
        return list(result.scalars().all())
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        table_name: Optional[str] = None,
        table_comment: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_page: bool = True
    ):
        """
        分页查询业务表列表
        
        :param page: 页码
        :param page_size: 每页数量
        :param table_name: 表名称（模糊匹配）
        :param table_comment: 表描述（模糊匹配）
        :param begin_time: 开始时间
        :param end_time: 结束时间
        :param is_page: 是否分页
        :return: 分页结果
        """
        conditions = []
        
        if table_name:
            conditions.append(
                func.lower(GenTableDO.table_name).like(f'%{table_name.lower()}%')
            )
        
        if table_comment:
            conditions.append(
                func.lower(GenTableDO.table_comment).like(f'%{table_comment.lower()}%')
            )
        
        if begin_time and end_time:
            conditions.append(
                GenTableDO.create_time.between(
                    datetime.combine(
                        datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)
                    ),
                    datetime.combine(
                        datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59)
                    )
                )
            )
        
        query = (
            select(GenTableDO)
            .options(selectinload(GenTableDO.columns))
            .where(*conditions if conditions else [True])
            .distinct()
        )
        
        # Imports/deletions must be reflected immediately in the metadata list.
        return await PageUtil.paginate(self.db, query, page, page_size, is_page)
    
    async def get_db_table_list(
        self,
        page: int,
        page_size: int,
        table_name: Optional[str] = None,
        table_comment: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_page: bool = True
    ):
        """
        获取数据库中未导入的表列表
        
        :param page: 页码
        :param page_size: 每页数量
        :param table_name: 表名称
        :param table_comment: 表描述
        :param begin_time: 开始时间
        :param end_time: 结束时间
        :param is_page: 是否分页
        :return: 数据库表列表
        """
        if DataBaseConfig.db_type == 'postgresql':
            query_sql = """
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time
            from 
                list_table
            where 
                table_name not like 'apscheduler_%' 
                and table_name not like 'gen_%'
                and table_name not in (select table_name from gen_table)
            """
        else:
            query_sql = """
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time
            from 
                information_schema.tables
            where 
                table_schema = (select database())
                and table_name not like 'apscheduler\\_%' 
                and table_name not like 'gen\\_%'
                and table_name not in (select table_name from gen_table)
            """
        
        bind_params = {}
        
        if table_name:
            query_sql += " and lower(table_name) like lower(concat('%', :table_name, '%'))"
            bind_params['table_name'] = table_name
        
        if table_comment:
            query_sql += " and lower(table_comment) like lower(concat('%', :table_comment, '%'))"
            bind_params['table_comment'] = table_comment
        
        if begin_time:
            if DataBaseConfig.db_type == 'postgresql':
                query_sql += " and create_time::date >= to_date(:begin_time, 'yyyy-MM-dd')"
            else:
                query_sql += " and date_format(create_time, '%Y%m%d') >= date_format(:begin_time, '%Y%m%d')"
            bind_params['begin_time'] = begin_time
        
        if end_time:
            if DataBaseConfig.db_type == 'postgresql':
                query_sql += " and create_time::date <= to_date(:end_time, 'yyyy-MM-dd')"
            else:
                query_sql += " and date_format(create_time, '%Y%m%d') <= date_format(:end_time, '%Y%m%d')"
            bind_params['end_time'] = end_time
        
        query_sql += " order by create_time desc"
        
        query = select(text(query_sql).bindparams(**bind_params))
        
        return await PageUtil.paginate(self.db, query, page, page_size, is_page)
    
    async def get_db_tables_by_names(self, table_names: List[str]) -> List[Any]:
        """
        根据表名列表获取数据库表信息
        
        :param table_names: 表名列表
        :return: 数据库表信息列表
        """
        if DataBaseConfig.db_type == 'postgresql':
            query_sql = """
            select
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time 
            from 
                list_table
            where 
                table_name not like 'qrtz_%' 
                and table_name not like 'gen_%' 
                and table_name = any(:table_names)
            """
        else:
            query_sql = """
            select
                table_name as table_name, 
                table_comment as table_comment, 
                create_time as create_time, 
                update_time as update_time 
            from 
                information_schema.tables
            where 
                table_name not like 'qrtz\\_%' 
                and table_name not like 'gen\\_%' 
                and table_schema = (select database())
                and table_name in :table_names
            """
        
        query = text(query_sql).bindparams(table_names=tuple(table_names))
        result = await self.db.execute(query)
        return result.fetchall()
    
    async def execute_sql_statements(self, sql_statements: List[Expression]) -> None:
        """
        执行 SQL 语句列表（用于创建表）
        
        :param sql_statements: SQL 语句 AST 列表
        """
        for sql_statement in sql_statements:
            sql = sql_statement.sql(dialect=DataBaseConfig.sqlglot_parse_dialect)
            await self.db.execute(text(sql))
    
    async def add(self, gen_table_data: Dict[str, Any]) -> GenTableDO:
        """
        新增业务表
        
        :param gen_table_data: 业务表数据字典
        :return: 新增的业务表对象
        """
        db_gen_table = GenTableDO(
            **GenTableBaseModel(**gen_table_data).model_dump()
        )
        self.db.add(db_gen_table)
        await self.db.flush()
        return db_gen_table
    
    async def update(self, gen_table_data: Dict[str, Any]) -> None:
        """
        更新业务表
        
        :param gen_table_data: 业务表数据字典（必须包含 table_id）
        """
        await self.db.execute(
            update(GenTableDO),
            [GenTableBaseModel(**gen_table_data).model_dump()]
        )
    
    async def delete_by_id(self, table_id: int) -> None:
        """
        根据ID删除业务表
        
        :param table_id: 业务表ID
        """
        await self.db.execute(
            delete(GenTableDO).where(GenTableDO.table_id == table_id)
        )
    
    async def delete_by_ids(self, table_ids: List[int]) -> None:
        """
        批量删除业务表
        
        :param table_ids: 业务表ID列表
        """
        await self.db.execute(
            delete(GenTableDO).where(GenTableDO.table_id.in_(table_ids))
        )


class GenTableColumnRepository:
    """
    代码生成业务表字段 Repository
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_table_id(self, table_id: int) -> List[GenTableColumnDO]:
        """
        根据业务表ID获取字段列表
        
        :param table_id: 业务表ID
        :return: 字段列表
        """
        result = await self.db.execute(
            select(GenTableColumnDO)
            .where(GenTableColumnDO.table_id == table_id)
            .order_by(GenTableColumnDO.sort)
        )
        return list(result.scalars().all())
    
    async def get_db_columns_by_table_name(self, table_name: str) -> List[Any]:
        """
        从数据库获取表的字段信息
        
        :param table_name: 表名称
        :return: 字段信息列表
        """
        if DataBaseConfig.db_type == 'postgresql':
            query_sql = """
            select
                column_name, is_required, is_pk, sort, column_comment, is_increment, column_type
            from
                list_column
            where
                table_name = :table_name
            """
        else:
            query_sql = """
            select 
                column_name as column_name,
                case 
                    when is_nullable = 'no' and column_key != 'PRI' then '1' 
                    else '0' 
                end as is_required,
                case 
                    when column_key = 'PRI' then '1' 
                    else '0' 
                end as is_pk,
                ordinal_position as sort,
                column_comment as column_comment,
                case 
                    when extra = 'auto_increment' then '1' 
                    else '0' 
                end as is_increment,
                column_type as column_type
            from 
                information_schema.columns
            where 
                table_schema = (select database()) 
                and table_name = :table_name
            order by 
                ordinal_position
            """
        
        query = text(query_sql).bindparams(table_name=table_name)
        result = await self.db.execute(query)
        return result.fetchall()
    
    async def add(self, column_data: Dict[str, Any]) -> GenTableColumnDO:
        """
        新增业务表字段
        
        :param column_data: 字段数据字典
        :return: 新增的字段对象
        """
        db_column = GenTableColumnDO(
            **GenTableColumnBaseModel(**column_data).model_dump()
        )
        self.db.add(db_column)
        await self.db.flush()
        return db_column
    
    async def update(self, column_data: Dict[str, Any]) -> None:
        """
        更新业务表字段
        
        :param column_data: 字段数据字典（必须包含 column_id）
        """
        await self.db.execute(
            update(GenTableColumnDO),
            [GenTableColumnBaseModel(**column_data).model_dump()]
        )
    
    async def delete_by_table_id(self, table_id: int) -> None:
        """
        根据业务表ID删除所有字段
        
        :param table_id: 业务表ID
        """
        await self.db.execute(
            delete(GenTableColumnDO).where(GenTableColumnDO.table_id == table_id)
        )
    
    async def delete_by_column_id(self, column_id: int) -> None:
        """
        根据字段ID删除字段
        
        :param column_id: 字段ID
        """
        await self.db.execute(
            delete(GenTableColumnDO).where(GenTableColumnDO.column_id == column_id)
        )
    
    async def delete_by_column_ids(self, column_ids: List[int]) -> None:
        """
        批量删除字段
        
        :param column_ids: 字段ID列表
        """
        await self.db.execute(
            delete(GenTableColumnDO).where(GenTableColumnDO.column_id.in_(column_ids))
        )
