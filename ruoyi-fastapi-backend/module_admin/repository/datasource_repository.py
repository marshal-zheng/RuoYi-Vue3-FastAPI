from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.datasource_do import DataSourceDO
from module_admin.repository.base_repository import BaseRepository


class DataSourceRepository(BaseRepository[DataSourceDO]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DataSourceDO)

    async def find_by_name(self, name: str) -> Optional[DataSourceDO]:
        stmt = select(DataSourceDO).where(DataSourceDO.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[DataSourceDO], int]:
        conditions = [DataSourceDO.is_deleted == False]
        if name:
            conditions.append(DataSourceDO.name.like(f'%{name}%'))
        if type:
            conditions.append(DataSourceDO.type == type)
        if status:
            conditions.append(DataSourceDO.status == status)

        count_stmt = select(func.count()).select_from(DataSourceDO).where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(DataSourceDO)
            .where(and_(*conditions))
            .order_by(DataSourceDO.create_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total
