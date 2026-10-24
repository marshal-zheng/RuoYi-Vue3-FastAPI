"""
通用 Repository
"""
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CommonRepository:
    """通用仓储，承载系统级只读查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sys_tables(self) -> List[Dict[str, str]]:
        """获取 sys_ 前缀表名与注释。"""
        query = text(
            """
            SELECT
                TABLE_NAME AS table_name,
                TABLE_COMMENT AS table_comment
            FROM
                information_schema.TABLES
            WHERE
                TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME LIKE 'sys_%'
            ORDER BY
                TABLE_NAME
            """
        )
        result = await self.db.execute(query)
        rows = result.mappings().all()

        table_list: List[Dict[str, str]] = []
        for row in rows:
            table_name = str(row.get('table_name') or '')
            table_comment = str(row.get('table_comment') or table_name)
            table_list.append(
                {
                    'label': f'{table_comment} ({table_name})' if table_comment else table_name,
                    'value': table_name,
                }
            )
        return table_list
