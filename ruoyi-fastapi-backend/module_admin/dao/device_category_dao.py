from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from module_admin.entity.do.device_category_do import DeviceCategoryDO
from module_admin.entity.vo.device_category_vo import DeviceCategoryQueryModel


class DeviceCategoryDao:
    """
    设备分类数据访问对象
    """

    @classmethod
    async def get_device_category_list(cls, db: AsyncSession, query: DeviceCategoryQueryModel):
        """
        获取设备分类列表（分页）
        """
        # 构建查询条件
        conditions = []
        if query.name:
            conditions.append(DeviceCategoryDO.name.like(f'%{query.name}%'))
        if query.status:
            conditions.append(DeviceCategoryDO.status == query.status)
        if query.begin_time:
            conditions.append(DeviceCategoryDO.create_time >= query.begin_time)
        if query.end_time:
            conditions.append(DeviceCategoryDO.create_time <= query.end_time)

        # 查询总数
        count_stmt = select(func.count()).select_from(DeviceCategoryDO)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 查询数据
        stmt = select(DeviceCategoryDO)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(DeviceCategoryDO.create_time.desc())
        stmt = stmt.offset((query.page_num - 1) * query.page_size).limit(query.page_size)

        result = await db.execute(stmt)
        categories = result.scalars().all()

        return categories, total

    @classmethod
    async def get_device_category_by_id(cls, db: AsyncSession, category_id: int) -> Optional[DeviceCategoryDO]:
        """
        根据ID获取设备分类
        """
        stmt = select(DeviceCategoryDO).where(DeviceCategoryDO.device_category_id == category_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_device_category_by_name(cls, db: AsyncSession, name: str) -> Optional[DeviceCategoryDO]:
        """
        根据名称获取设备分类
        """
        stmt = select(DeviceCategoryDO).where(DeviceCategoryDO.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def add_device_category(cls, db: AsyncSession, category: DeviceCategoryDO) -> DeviceCategoryDO:
        """
        新增设备分类
        """
        db.add(category)
        await db.flush()
        await db.refresh(category)
        return category

    @classmethod
    async def update_device_category(cls, db: AsyncSession, category: DeviceCategoryDO) -> DeviceCategoryDO:
        """
        更新设备分类
        """
        await db.merge(category)
        await db.flush()
        return category

    @classmethod
    async def delete_device_category(cls, db: AsyncSession, category_ids: List[int]) -> int:
        """
        删除设备分类
        """
        from sqlalchemy import delete
        stmt = delete(DeviceCategoryDO).where(DeviceCategoryDO.device_category_id.in_(category_ids))
        result = await db.execute(stmt)
        return result.rowcount

    @classmethod
    async def get_all_device_categories(cls, db: AsyncSession) -> List[DeviceCategoryDO]:
        """
        获取所有设备分类（用于下拉选择）
        """
        stmt = select(DeviceCategoryDO).where(DeviceCategoryDO.status == '0').order_by(DeviceCategoryDO.name)
        result = await db.execute(stmt)
        return result.scalars().all()
