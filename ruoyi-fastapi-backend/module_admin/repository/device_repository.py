"""
设备 Repository
展示如何使用 Repository 模式替代传统 DAO
"""
from typing import List, Optional
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from module_admin.repository.base_repository import BaseRepository
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO


class DeviceRepository(BaseRepository[DeviceDO]):
    """
    设备 Repository
    
    继承 BaseRepository，获得基础 CRUD 能力
    添加设备特定的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, DeviceDO)
    
    async def get_by_id_with_interfaces(self, device_id: int) -> Optional[DeviceDO]:
        """
        根据ID获取设备详情（包含接口和分类）
        
        Args:
            device_id: 设备ID
        
        Returns:
            设备对象或 None
        """
        stmt = select(DeviceDO).options(
            selectinload(DeviceDO.interfaces),
            selectinload(DeviceDO.category),
        ).where(DeviceDO.device_id == device_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_name(self, device_name: str) -> Optional[DeviceDO]:
        """
        根据设备名称查找设备
        
        Args:
            device_name: 设备名称
        
        Returns:
            设备对象或 None
        """
        stmt = select(DeviceDO).where(DeviceDO.device_name == device_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_name_and_type(
        self, 
        device_name: str, 
        device_type: Optional[str] = None
    ) -> Optional[DeviceDO]:
        """
        根据设备名称和类型查找设备
        
        Args:
            device_name: 设备名称
            device_type: 设备类型（可选）
        
        Returns:
            设备对象或 None
        """
        stmt = select(DeviceDO).options(
            selectinload(DeviceDO.interfaces)
        ).where(DeviceDO.device_name == device_name)
        
        if device_type:
            stmt = stmt.where(DeviceDO.device_type == device_type)
        
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_ids(self, device_ids: List[int]) -> List[DeviceDO]:
        """
        根据ID列表批量获取设备
        
        Args:
            device_ids: 设备ID列表
        
        Returns:
            设备列表
        """
        if not device_ids:
            return []
        
        stmt = select(DeviceDO).options(
            selectinload(DeviceDO.interfaces),
            selectinload(DeviceDO.category),
        ).where(DeviceDO.device_id.in_(device_ids))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def search_devices(
        self,
        device_name: Optional[str] = None,
        bus_type: Optional[str] = None,
        device_type: Optional[str] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[DeviceDO], int]:
        """
        搜索设备（分页）
        
        Args:
            device_name: 设备名称（模糊查询）
            bus_type: 总线类型（模糊查询）
            device_type: 设备类型
            category_id: 分类ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            (设备列表, 总数)
        """
        # 构建查询条件
        conditions = []
        if device_name:
            conditions.append(DeviceDO.device_name.like(f'%{device_name}%'))
        if bus_type:
            conditions.append(DeviceDO.bus_type.like(f'%{bus_type}%'))
        if device_type:
            conditions.append(DeviceDO.device_type == device_type)
        if category_id:
            conditions.append(DeviceDO.device_category_id == category_id)
        
        # 查询总数
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(DeviceDO)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # 查询数据
        stmt = select(DeviceDO).options(
            selectinload(DeviceDO.interfaces),
            selectinload(DeviceDO.category),
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(DeviceDO.update_time.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        devices = result.scalars().all()
        
        return devices, total
    
    async def delete_by_device_ids(self, device_ids: List[int]) -> int:
        """
        根据设备ID列表删除设备（级联删除接口）
        
        Args:
            device_ids: 设备ID列表
        
        Returns:
            删除的记录数
        """
        if not device_ids:
            return 0
        
        stmt = delete(DeviceDO).where(DeviceDO.device_id.in_(device_ids))
        result = await self.db.execute(stmt)
        return result.rowcount


class DeviceInterfaceRepository(BaseRepository[DeviceInterfaceDO]):
    """
    设备接口 Repository
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, DeviceInterfaceDO)
    
    async def find_by_device_id(self, device_id: int) -> List[DeviceInterfaceDO]:
        """
        获取设备的所有接口
        
        Args:
            device_id: 设备ID
        
        Returns:
            接口列表
        """
        stmt = select(DeviceInterfaceDO).where(
            DeviceInterfaceDO.device_id == device_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_device_id(self, device_id: int) -> int:
        """
        删除设备的所有接口
        
        Args:
            device_id: 设备ID
        
        Returns:
            删除的记录数
        """
        stmt = delete(DeviceInterfaceDO).where(
            DeviceInterfaceDO.device_id == device_id
        )
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_device_ids(self, device_ids: List[int]) -> int:
        """
        根据设备ID列表删除其所有接口
        
        Args:
            device_ids: 设备ID列表
        
        Returns:
            删除的记录数
        """
        if not device_ids:
            return 0
        
        stmt = delete(DeviceInterfaceDO).where(
            DeviceInterfaceDO.device_id.in_(device_ids)
        )
        result = await self.db.execute(stmt)
        return result.rowcount


# 使用示例
"""
from utils.transaction_manager import transactional

# 1. 基础使用
device_repo = DeviceRepository(db)

# 获取设备（包含接口）
device = await device_repo.get_by_id_with_interfaces(device_id=1)

# 根据名称查找
device = await device_repo.find_by_name("传感器01")

# 搜索设备（分页）
devices, total = await device_repo.search_devices(
    device_name="传感器",
    page=1,
    page_size=10
)

# 2. 结合事务管理器使用
@transactional()
async def create_device_with_interfaces(
    db: AsyncSession, 
    device_data: dict, 
    interfaces_data: List[dict]
):
    # 创建 Repository
    device_repo = DeviceRepository(db)
    interface_repo = DeviceInterfaceRepository(db)
    
    # 添加设备
    device = DeviceDO(**device_data)
    device = await device_repo.add(device)
    
    # 添加接口
    for intf_data in interfaces_data:
        intf_data['device_id'] = device.device_id
        interface = DeviceInterfaceDO(**intf_data)
        await interface_repo.add(interface)
    
    return device

# 3. 在 Service 中使用
class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.device_repo = DeviceRepository(db)
        self.interface_repo = DeviceInterfaceRepository(db)
    
    async def get_device_detail(self, device_id: int):
        return await self.device_repo.get_by_id_with_interfaces(device_id)
    
    async def search_devices(self, query_params):
        return await self.device_repo.search_devices(**query_params)
"""
