import json
import re
from io import BytesIO
from datetime import datetime
from typing import Dict, List
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from module_admin.dao.device_dao import DeviceDao
from module_admin.dao.device_category_dao import DeviceCategoryDao
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO
from module_admin.entity.vo.device_vo import (
    DeviceQueryModel,
    DeviceModel,
    DeviceListModel,
    DeviceInterfaceModel,
    CloneDeviceModel,
    DeviceExportDataModel,
    ExportDeviceModel,
    ExportDeviceInterfaceModel,
)
from utils.response_util import ResponseUtil
from exceptions.exception import ServiceException


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
            
            category_name = device.category_name or (
                device.category.name if getattr(device, 'category', None) else None
            )

            interface_vo_list = [
                DeviceInterfaceModel.model_validate(interface)
                for interface in device.interfaces
            ]

            device_vo = DeviceListModel(
                device_id=device.device_id,
                device_name=device.device_name,
                category_name=category_name or '-',
                bus_interfaces=bus_interfaces or '-',
                create_by=device.create_by,
                update_time=device.update_time,
                interfaces=interface_vo_list,
            )

            # 仅返回驼峰格式字段，避免混用命名风格
            device_list.append(device_vo.model_dump(by_alias=True))
        
        return ResponseUtil.success(
            rows=device_list,
            dict_content={'total': total}
        )

    @classmethod
    async def get_device_detail(cls, db: AsyncSession, device_id: int):
        """
        获取设备详情（包含接口配置）
        """
        device = await DeviceDao.get_device_by_id(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 单独查询接口信息，避免异步懒加载导致 MissingGreenlet
        interfaces = await DeviceDao.get_device_interfaces(db, device_id)
        interface_list = []
        for interface in interfaces:
            interface_item = {
                'interface_id': interface.interface_id,
                'device_id': interface.device_id,
                'interface_name': interface.interface_name,
                'interface_type': interface.interface_type,
                'position': interface.position,
                'description': interface.description,
                'params': interface.params,
                'message_config': interface.message_config,
                'create_time': interface.create_time,
                'update_time': interface.update_time,
            }
            interface_list.append(interface_item)

        device_data = {
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_category_id': device.device_category_id,
            'category_name': device.category_name,
            'device_type': device.device_type,
            'manufacturer': device.manufacturer,
            'model': device.model,
            'version': device.version,
            'bus_type': device.bus_type,
            'remark': device.remark,
            'create_by': device.create_by,
            'create_time': device.create_time,
            'update_by': device.update_by,
            'update_time': device.update_time,
            'interfaces': interface_list,
        }

        device_vo = DeviceModel.model_validate(device_data)
        return ResponseUtil.success(data=device_vo.model_dump(by_alias=True))

    @classmethod
    async def add_device(cls, db: AsyncSession, device_data: DeviceModel, current_user: str):
        """
        新增设备（包含接口）
        """
        # 创建设备DO对象
        resolved_category_id, resolved_category_name = await cls._resolve_category_info(
            db,
            device_data.device_category_id,
            device_data.category_name,
        )

        device_do = DeviceDO(
            device_name=device_data.device_name,
            device_category_id=resolved_category_id,
            category_name=resolved_category_name,
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
        resolved_category_id, resolved_category_name = await cls._resolve_category_info(
            db,
            device_data.device_category_id,
            device_data.category_name,
        )

        existing.device_name = device_data.device_name
        existing.device_category_id = resolved_category_id
        existing.category_name = resolved_category_name
        existing.device_type = device_data.device_type
        existing.manufacturer = device_data.manufacturer
        existing.model = device_data.model
        existing.version = device_data.version
        existing.bus_type = device_data.bus_type
        existing.remark = device_data.remark
        existing.update_by = current_user
        existing.update_time = datetime.now()
        
        # 使用会话关系清空并重建接口，避免旧数据重新合并
        existing.interfaces.clear()
        await db.flush()

        # 添加新的接口（全部走 relationship，保持事务一致性）
        for interface_data in device_data.interfaces:
            interface_do = DeviceInterfaceDO(
                interface_name=interface_data.interface_name,
                interface_type=interface_data.interface_type,
                position=interface_data.position,
                description=interface_data.description,
                params=interface_data.params,
                message_config=interface_data.message_config,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            existing.interfaces.append(interface_do)
        
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
        id_list = [int(id_str.strip()) for id_str in device_ids.split(',') if id_str.strip()]
        if not id_list:
            raise HTTPException(status_code=400, detail="未提供有效的设备ID")

        try:
            # 先删除接口信息以避免外键约束
            await DeviceDao.delete_interfaces_by_device_ids(db, id_list)

            # 删除设备
            deleted_count = await DeviceDao.delete_device(db, id_list)
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"设备删除失败: {exc.orig}")

        return ResponseUtil.success(msg=f"删除成功，共删除{deleted_count}条记录")

    @classmethod
    async def check_device_name_unique(cls, db: AsyncSession, device_name: str, device_id: int = None):
        """
        检查设备名称是否唯一
        """
        existing = await DeviceDao.get_device_by_name(db, device_name)
        
        if not existing:
            return ResponseUtil.success(data=True)
        
        if device_id and existing.device_id == device_id:
            return ResponseUtil.success(data=True)
        
        return ResponseUtil.success(data=False)

    @classmethod
    async def clone_device(cls, db: AsyncSession, clone_data: CloneDeviceModel, current_user: str):
        """
        克隆设备（包含接口）
        """
        # 获取源设备信息
        source_device = await DeviceDao.get_device_by_id(db, clone_data.source_device_id)
        if not source_device:
            raise ServiceException(message='源设备不存在')
        
        # 检查新设备名称是否唯一
        existing = await DeviceDao.get_device_by_name(db, clone_data.device_name)
        if existing:
            raise ServiceException(message=f'设备名称 "{clone_data.device_name}" 已存在')
        
        # 创建新设备
        resolved_category_id, resolved_category_name = await cls._resolve_category_info(
            db,
            source_device.device_category_id,
            source_device.category_name,
        )
        
        new_device = DeviceDO(
            device_name=clone_data.device_name,
            device_category_id=resolved_category_id,
            category_name=resolved_category_name,
            device_type=source_device.device_type,
            manufacturer=source_device.manufacturer,
            model=source_device.model,
            version=source_device.version,
            bus_type=source_device.bus_type,
            remark=source_device.remark,
            create_by=current_user,
            create_time=datetime.now(),
            update_by=current_user,
            update_time=datetime.now()
        )
        
        # 克隆接口
        for source_interface in source_device.interfaces:
            interface_do = DeviceInterfaceDO(
                interface_name=source_interface.interface_name,
                interface_type=source_interface.interface_type,
                position=source_interface.position,
                description=source_interface.description,
                params=source_interface.params,
                message_config=source_interface.message_config,
                create_time=datetime.now()
            )
            new_device.interfaces.append(interface_do)
        
        # 保存到数据库
        result = await DeviceDao.add_device(db, new_device)
        await db.commit()
        
        return ResponseUtil.success(data={'device_id': result.device_id}, msg="克隆成功")

    @classmethod
    async def export_devices_zip_services(cls, db: AsyncSession, device_ids: List[int]):
        """
        批量导出设备数据（zip包）
        """
        if not device_ids:
            raise ServiceException(message='请选择需要导出的设备')

        buffer = BytesIO()
        exported = 0

        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_file:
            for device_id in device_ids:
                device = await DeviceDao.get_device_by_id(db, device_id)
                if not device:
                    continue

                export_data = cls._build_export_data(device)
                data_dict = export_data.model_dump(mode='json', by_alias=True)
                json_bytes = json.dumps(data_dict, ensure_ascii=False, default=str).encode('utf-8')

                safe_name = cls._safe_filename(device.device_name)
                filename = f'{safe_name}_{device_id}.json'
                zip_file.writestr(filename, json_bytes)
                exported += 1

        if exported == 0:
            raise ServiceException(message='未找到可导出的设备')

        buffer.seek(0)
        zip_name = f'device_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
        return buffer, zip_name

    @classmethod
    async def import_devices_from_zip_services(cls, db: AsyncSession, file_bytes: bytes, operator: str):
        """
        批量导入设备（zip或单个json）
        """
        if not file_bytes:
            raise ServiceException(message='上传文件为空')

        file_buffer = BytesIO(file_bytes)
        success_count = 0
        failed_count = 0
        results: List[Dict[str, str]] = []

        if is_zipfile(file_buffer):
            file_buffer.seek(0)
            with ZipFile(file_buffer, 'r') as zip_file:
                json_files = [
                    name for name in zip_file.namelist()
                    if not name.endswith('/') and name.lower().endswith('.json')
                ]
                if not json_files:
                    raise ServiceException(message='zip包中未找到json设备文件')

                for name in json_files:
                    content = zip_file.read(name).decode('utf-8')
                    try:
                        import_result = await cls._import_single_device(db, content, operator)
                        success_count += 1
                        results.append({
                            'fileName': name,
                            'status': 'success',
                            **import_result,
                        })
                    except Exception as exc:
                        failed_count += 1
                        await db.rollback()
                        results.append({
                            'fileName': name,
                            'status': 'failed',
                            'message': str(exc),
                        })
        else:
            try:
                content = file_buffer.getvalue().decode('utf-8')
                import_result = await cls._import_single_device(db, content, operator)
                success_count = 1
                results.append({
                    'fileName': 'device.json',
                    'status': 'success',
                    **import_result,
                })
            except Exception as exc:
                await db.rollback()
                raise ServiceException(message=str(exc))

        return {
            'successCount': success_count,
            'failedCount': failed_count,
            'details': results,
        }

    @classmethod
    async def _import_single_device(cls, db: AsyncSession, json_text: str, operator: str):
        """
        导入单个设备
        """
        raw_data = json.loads(json_text)
        export_data = DeviceExportDataModel(**raw_data)
        source = export_data.device

        resolved_category_id, resolved_category_name = await cls._resolve_category_info(
            db,
            getattr(source, 'device_category_id', None),
            source.category_name,
        )
        device_name = await cls._ensure_unique_device_name(db, source.device_name)

        new_device = DeviceDO(
            device_name=device_name,
            device_category_id=resolved_category_id,
            category_name=resolved_category_name,
            device_type=source.device_type,
            manufacturer=source.manufacturer,
            model=source.model,
            version=source.version,
            bus_type=source.bus_type,
            remark=source.remark,
            create_by=operator,
            create_time=datetime.now(),
            update_by=operator,
            update_time=datetime.now()
        )

        for interface in source.interfaces:
            interface_do = DeviceInterfaceDO(
                interface_name=interface.interface_name,
                interface_type=interface.interface_type,
                position=interface.position or 'right',
                description=interface.description,
                params=interface.params,
                message_config=interface.message_config,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            new_device.interfaces.append(interface_do)

        result = await DeviceDao.add_device(db, new_device)
        await db.commit()

        return {
            'deviceId': result.device_id,
            'deviceName': new_device.device_name,
        }

    @staticmethod
    def _build_export_data(device: DeviceDO) -> DeviceExportDataModel:
        """
        构造导出数据
        """
        interfaces = [
            ExportDeviceInterfaceModel(
                interface_name=intf.interface_name,
                interface_type=intf.interface_type,
                position=intf.position,
                description=intf.description,
                params=intf.params,
                message_config=intf.message_config,
            )
            for intf in (device.interfaces or [])
        ]
        export_device = ExportDeviceModel(
            device_id=device.device_id,
            device_name=device.device_name,
            category_name=device.category_name,
            device_type=device.device_type,
            manufacturer=device.manufacturer,
            model=device.model,
            version=device.version,
            bus_type=device.bus_type,
            remark=device.remark,
            interfaces=interfaces,
        )
        return DeviceExportDataModel(
            device=export_device
        )

    @staticmethod
    async def _ensure_unique_device_name(db: AsyncSession, device_name: str) -> str:
        """
        确保设备名称唯一
        """
        base_name = device_name or '设备'
        candidate = base_name
        suffix = 1
        existing = await DeviceDao.get_device_by_name(db, candidate)
        while existing:
            candidate = f'{base_name}_{suffix}'
            suffix += 1
            existing = await DeviceDao.get_device_by_name(db, candidate)
        return candidate

    @staticmethod
    def _safe_filename(name: str) -> str:
        """
        生成安全的文件名
        """
        safe = re.sub(r'[\\/:*?"<>|\\s]+', '_', name.strip()) if name else 'device'
        return safe or 'device'

    @staticmethod
    async def _resolve_category_info(db: AsyncSession, category_id, category_name):
        """
        根据已知的分类ID或名称补齐另一端信息，确保数据一致。
        """
        resolved_id = category_id
        resolved_name = category_name

        if category_id and not category_name:
            category = await DeviceCategoryDao.get_device_category_by_id(db, category_id)
            if category:
                resolved_name = category.name
        elif category_name and not category_id:
            category = await DeviceCategoryDao.get_device_category_by_name(db, category_name)
            if category:
                resolved_id = category.device_category_id
                resolved_name = category.name

        return resolved_id, resolved_name
