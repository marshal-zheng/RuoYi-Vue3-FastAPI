from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO
from module_admin.entity.vo.device_vo import DeviceQueryModel


class DeviceDao:
    """
    设备数据访问对象
    """

    @classmethod
    async def get_device_list(cls, db: AsyncSession, query: DeviceQueryModel):
        """
        获取设备列表（分页）
        """
        # 构建查询条件
        conditions = []
        if query.device_name:
            conditions.append(DeviceDO.device_name.like(f'%{query.device_name}%'))
        if query.bus_type:
            conditions.append(DeviceDO.bus_type.like(f'%{query.bus_type}%'))
        if query.begin_time:
            conditions.append(DeviceDO.update_time >= query.begin_time)
        if query.end_time:
            conditions.append(DeviceDO.update_time <= query.end_time)

        # 查询总数
        count_stmt = select(func.count()).select_from(DeviceDO)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 查询数据（预加载接口信息）
        stmt = select(DeviceDO).options(selectinload(DeviceDO.interfaces))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(DeviceDO.update_time.desc())
        stmt = stmt.offset((query.page_num - 1) * query.page_size).limit(query.page_size)

        result = await db.execute(stmt)
        devices = result.scalars().all()

        return devices, total

    @classmethod
    async def get_device_by_id(cls, db: AsyncSession, device_id: int) -> Optional[DeviceDO]:
        """
        根据ID获取设备详情（包含接口）
        """
        stmt = select(DeviceDO).options(selectinload(DeviceDO.interfaces)).where(DeviceDO.device_id == device_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def add_device(cls, db: AsyncSession, device: DeviceDO) -> DeviceDO:
        """
        新增设备
        """
        db.add(device)
        await db.flush()
        await db.refresh(device, ['interfaces'])
        return device

    @classmethod
    async def update_device(cls, db: AsyncSession, device: DeviceDO) -> DeviceDO:
        """
        更新设备
        """
        await db.merge(device)
        await db.flush()
        return device

    @classmethod
    async def delete_device(cls, db: AsyncSession, device_ids: List[int]) -> int:
        """
        删除设备（级联删除接口）
        """
        stmt = delete(DeviceDO).where(DeviceDO.device_id.in_(device_ids))
        result = await db.execute(stmt)
        return result.rowcount

    @classmethod
    async def delete_device_interfaces(cls, db: AsyncSession, device_id: int):
        """
        删除设备的所有接口
        """
        stmt = delete(DeviceInterfaceDO).where(DeviceInterfaceDO.device_id == device_id)
        await db.execute(stmt)

    @classmethod
    async def add_device_interface(cls, db: AsyncSession, interface: DeviceInterfaceDO) -> DeviceInterfaceDO:
        """
        新增设备接口
        """
        db.add(interface)
        await db.flush()
        await db.refresh(interface)
        return interface

    @classmethod
    async def get_device_interfaces(cls, db: AsyncSession, device_id: int) -> List[DeviceInterfaceDO]:
        """
        获取设备的所有接口
        """
        stmt = select(DeviceInterfaceDO).where(DeviceInterfaceDO.device_id == device_id)
        result = await db.execute(stmt)
        return result.scalars().all()
