from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List
from fastapi import HTTPException
from module_admin.dao.device_dao import DeviceDao
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO
from module_admin.entity.vo.device_vo import DeviceQueryModel, DeviceModel, DeviceInterfaceModel
from utils.response_util import ResponseUtil


class DeviceService:
    """
    设备服务类
    """

    @classmethod
    async def get_device_list(cls, db: AsyncSession, query: DeviceQueryModel, current_user: str):
        """
        获取设备列表
        """
        devices, total = await DeviceDao.get_device_list(db, query)
        
        # 转换为列表VO（格式化总线接口显示）
        device_list = []
        for device in devices:
            # 统计总线接口类型
            interface_types = {}
            for interface in device.interfaces:
                interface_type = interface.interface_type
                interface_types[interface_type] = interface_types.get(interface_type, 0) + 1
            
            # 格式化显示：RS422(2), CAN(1)
            bus_interfaces = ', '.join([f"{k}({v})" for k, v in interface_types.items()])
            
            device_list.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'category_name': device.category_name,
                'bus_interfaces': bus_interfaces or '-',
                'create_by': device.create_by,
                'update_time': device.update_time
            })
        
        return ResponseUtil.success(data={
            'rows': device_list,
            'total': total
        })

    @classmethod
    async def get_device_detail(cls, db: AsyncSession, device_id: int):
        """
        获取设备详情（包含接口配置）
        """
        device = await DeviceDao.get_device_by_id(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 转换为VO模型
        device_vo = DeviceModel.model_validate(device)
        return ResponseUtil.success(data=device_vo.model_dump())

    @classmethod
    async def add_device(cls, db: AsyncSession, device_data: DeviceModel, current_user: str):
        """
        新增设备（包含接口）
        """
        # 创建设备DO对象
        device_do = DeviceDO(
            device_name=device_data.device_name,
            device_category_id=device_data.device_category_id,
            category_name=device_data.category_name,
            device_type=device_data.device_type,
            manufacturer=device_data.manufacturer,
            model=device_data.model,
            version=device_data.version,
            bus_type=device_data.bus_type,
            remark=device_data.remark,
            create_by=current_user,
            create_time=datetime.now()
        )
        
        # 添加接口
        for interface_data in device_data.interfaces:
            interface_do = DeviceInterfaceDO(
                interface_name=interface_data.interface_name,
                interface_type=interface_data.interface_type,
                position=interface_data.position,
                description=interface_data.description,
                params=interface_data.params,
                message_config=interface_data.message_config,
                create_time=datetime.now()
            )
            device_do.interfaces.append(interface_do)
        
        # 保存到数据库
        result = await DeviceDao.add_device(db, device_do)
        await db.commit()
        
        return ResponseUtil.success(data={'device_id': result.device_id}, msg="新增成功")

    @classmethod
    async def update_device(cls, db: AsyncSession, device_data: DeviceModel, current_user: str):
        """
        更新设备（包含接口）
        """
        # 检查设备是否存在
        existing = await DeviceDao.get_device_by_id(db, device_data.device_id)
        if not existing:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 更新设备基本信息
        existing.device_name = device_data.device_name
        existing.device_category_id = device_data.device_category_id
        existing.category_name = device_data.category_name
        existing.device_type = device_data.device_type
        existing.manufacturer = device_data.manufacturer
        existing.model = device_data.model
        existing.version = device_data.version
        existing.bus_type = device_data.bus_type
        existing.remark = device_data.remark
        existing.update_by = current_user
        existing.update_time = datetime.now()
        
        # 删除旧的接口
        await DeviceDao.delete_device_interfaces(db, device_data.device_id)
        
        # 添加新的接口
        for interface_data in device_data.interfaces:
            interface_do = DeviceInterfaceDO(
                device_id=device_data.device_id,
                interface_name=interface_data.interface_name,
                interface_type=interface_data.interface_type,
                position=interface_data.position,
                description=interface_data.description,
                params=interface_data.params,
                message_config=interface_data.message_config,
                create_time=datetime.now() if not interface_data.interface_id else None,
                update_time=datetime.now()
            )
            await DeviceDao.add_device_interface(db, interface_do)
        
        # 保存到数据库
        await DeviceDao.update_device(db, existing)
        await db.commit()
        
        return ResponseUtil.success(msg="修改成功")

    @classmethod
    async def delete_device(cls, db: AsyncSession, device_ids: str):
        """
        删除设备（级联删除接口）
        """
        # 解析ID列表
        id_list = [int(id_str) for id_str in device_ids.split(',')]
        
        # 删除设备
        deleted_count = await DeviceDao.delete_device(db, id_list)
        await db.commit()
        
        return ResponseUtil.success(msg=f"删除成功，共删除{deleted_count}条记录")
