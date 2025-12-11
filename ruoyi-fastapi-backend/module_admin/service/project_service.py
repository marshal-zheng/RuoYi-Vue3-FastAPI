import base64
import json
import re
from datetime import datetime
from io import BytesIO
from typing import List, Set
from zipfile import ZIP_DEFLATED, ZipFile, is_zipfile

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.dao.device_dao import DeviceDao
from module_admin.dao.project_dao import ProjectDao
from module_admin.dao.project_topology_dao import ProjectTopologyDao
from module_admin.dao.project_version_dao import ProjectVersionDao
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from module_admin.entity.vo.project_version_vo import ProjectVersionModel
from module_admin.entity.vo.project_vo import (
    DeleteProjectModel,
    ExportDeviceInterfaceModel,
    ExportDeviceModel,
    ExportProjectModel,
    ExportVersionModel,
    ProjectExportDataModel,
    ProjectImportDataModel,
    ProjectModel,
    ProjectPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.page_util import PageResponseModel


class ProjectService:
    """
    工程管理模块服务层
    """

    @classmethod
    async def get_project_list_services(
        cls, query_db: AsyncSession, query_object: ProjectPageQueryModel, is_page: bool = False
    ):
        """
        获取工程列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 工程列表信息对象
        """
        project_list_result = await ProjectDao.get_project_list(query_db, query_object, is_page)
        if is_page:
            return PageResponseModel(
                **{
                    **project_list_result.model_dump(),
                    'rows': CamelCaseUtil.transform_result(project_list_result.rows)
                }
            )
        else:
            return CamelCaseUtil.transform_result(project_list_result)

    @classmethod
    async def add_project_services(cls, query_db: AsyncSession, page_object: ProjectModel):
        """
        新增工程信息service

        :param query_db: orm对象
        :param page_object: 新增工程对象
        :return: 新增工程校验结果
        """
        try:
            # 自动生成工程编码
            if not page_object.project_code:
                page_object.project_code = await cls._generate_project_code(query_db)

            new_project = await ProjectDao.add_project_dao(query_db, page_object)
            
            # 创建默认初始版本
            default_version = ProjectVersionModel(
                project_id=new_project.project_id,
                version_number='v1.0.0',
                version_name='初始版本',
                description='项目初始版本',
                status='1',
                is_locked='0',
                create_by=page_object.create_by,
                create_time=datetime.now(),
                update_by=page_object.update_by,
                update_time=datetime.now()
            )
            new_version = await ProjectVersionDao.add_project_version_dao(query_db, default_version)
            
            await query_db.commit()
            return CrudResponseModel(
                is_success=True,
                message='新增成功',
                result={
                    'projectId': new_project.project_id,
                    'versionId': new_version.version_id
                }
            )
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def _generate_project_code(cls, query_db: AsyncSession) -> str:
        """
        生成工程编码：格式为 PRJ + 年月日 + 4位序号，例如：PRJ202511130001
        
        :param query_db: orm对象
        :return: 工程编码
        """
        from sqlalchemy import select, func
        from module_admin.entity.do.project_do import SysProject
        
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'PRJ{today}'
        
        # 查询今天最大的编号
        result = await query_db.execute(
            select(func.max(SysProject.project_code))
            .where(SysProject.project_code.like(f'{prefix}%'))
        )
        max_code = result.scalar()
        
        if max_code:
            # 提取序号并加1
            seq = int(max_code[-4:]) + 1
        else:
            seq = 1
        
        return f'{prefix}{seq:04d}'

    @classmethod
    async def edit_project_services(cls, query_db: AsyncSession, page_object: ProjectModel):
        """
        编辑工程信息service

        :param query_db: orm对象
        :param page_object: 编辑工程对象
        :return: 编辑工程校验结果
        """
        try:
            await ProjectDao.edit_project_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_project_services(cls, query_db: AsyncSession, page_object: DeleteProjectModel):
        """
        删除工程信息service

        :param query_db: orm对象
        :param page_object: 删除工程对象
        :return: 删除工程校验结果
        """
        if not page_object.project_ids:
            raise ServiceException(message='传入工程id为空')

        project_id_list = [int(project_id) for project_id in page_object.project_ids.split(',') if project_id]
        if not project_id_list:
            raise ServiceException(message='未解析到有效工程id')

        try:
            locked_map = await ProjectVersionDao.get_locked_versions_by_project(query_db, project_id_list)
            if locked_map:
                blocked_messages = []
                for project_id, versions in locked_map.items():
                    version_names = '、'.join([version.version_name for version in versions])
                    blocked_messages.append(f'工程ID {project_id} 存在固化版本：{version_names}')
                raise ServiceException(message='；'.join(blocked_messages))

            await ProjectDao.delete_project_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def project_detail_services(cls, query_db: AsyncSession, project_id: int):
        """
        获取工程详细信息service

        :param query_db: orm对象
        :param project_id: 工程id
        :return: 工程id对应的信息
        """
        project = await ProjectDao.get_project_detail_by_id(query_db, project_id)
        if project:
            result = CamelCaseUtil.transform_result(project)
        else:
            result = CamelCaseUtil.transform_result({})

        return result

    @classmethod
    async def export_project_services(cls, query_db: AsyncSession, project_id: int):
        """
        导出工程数据service

        :param query_db: orm对象
        :param project_id: 工程id
        :return: 工程导出数据
        """
        # 1. 获取工程基本信息
        project = await ProjectDao.get_project_detail_by_id(query_db, project_id)
        if not project:
            raise ServiceException(message='工程不存在')

        # 2. 获取所有版本
        versions = await ProjectVersionDao.get_all_versions_by_project(query_db, project_id)
        version_ids = [v.version_id for v in versions]

        # 3. 获取所有版本的拓扑数据
        topologies = await ProjectTopologyDao.get_topologies_by_version_ids(
            query_db, project_id, version_ids
        )
        topo_map = {t.version_id: t.topology_data for t in topologies}

        # 4. 从拓扑数据中提取设备ID
        device_ids: Set[int] = set()
        for topo_data in topo_map.values():
            if topo_data:
                device_ids.update(cls._extract_device_ids_from_topology(topo_data))

        # 5. 获取设备完整信息
        devices = await DeviceDao.get_devices_by_ids(query_db, list(device_ids))

        # 6. 构建导出数据
        export_project = ExportProjectModel(
            project_name=project.project_name,
            project_code=project.project_code,
            project_desc=project.project_desc,
            create_by=project.create_by,
            create_time=project.create_time,
        )

        export_versions = []
        for v in versions:
            export_versions.append(ExportVersionModel(
                version_number=v.version_number,
                version_name=v.version_name,
                description=v.description,
                status=v.status,
                is_locked=v.is_locked,
                topology=topo_map.get(v.version_id),
            ))

        export_devices = []
        for d in devices:
            interfaces = [
                ExportDeviceInterfaceModel(
                    interface_name=intf.interface_name,
                    interface_type=intf.interface_type,
                    position=intf.position,
                    description=intf.description,
                    params=intf.params,
                    message_config=intf.message_config,
                )
                for intf in (d.interfaces or [])
            ]
            export_devices.append(ExportDeviceModel(
                device_id=d.device_id,
                device_name=d.device_name,
                device_type=d.device_type,
                category_name=d.category_name,
                manufacturer=d.manufacturer,
                model=d.model,
                version=d.version,
                bus_type=d.bus_type,
                remark=d.remark,
                interfaces=interfaces,
            ))

        export_data = ProjectExportDataModel(
            export_version='1.0.0',
            export_time=datetime.now(),
            project=export_project,
            versions=export_versions,
            devices=export_devices,
        )

        return export_data

    @classmethod
    async def export_project_zip_services(cls, query_db: AsyncSession, project_id: int):
        """
        导出单个工程为zip包
        """
        export_data = await cls.export_project_services(query_db, project_id)
        buffer = BytesIO()

        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_file:
            data_dict = export_data.model_dump(mode='json', by_alias=True)
            json_bytes = json.dumps(data_dict, ensure_ascii=False, default=str).encode('utf-8')

            project_name = export_data.project.project_name or f'project_{project_id}'
            safe_name = cls._safe_filename(project_name)
            filename = f'{safe_name}_export_{project_id}.json'
            zip_file.writestr(filename, json_bytes)

        buffer.seek(0)
        zip_name = f'{safe_name}_export_{project_id}.zip'
        return buffer, zip_name

    @classmethod
    async def export_projects_zip_services(cls, query_db: AsyncSession, project_ids: List[int]):
        """
        批量导出工程数据并打包为zip

        :param query_db: orm对象
        :param project_ids: 工程id列表
        :return: (zip二进制流, 文件名)
        """
        if not project_ids:
            raise ServiceException(message='请选择需要导出的工程')

        buffer = BytesIO()
        errors = []
        exported_count = 0

        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zip_file:
            for project_id in project_ids:
                try:
                    export_data = await cls.export_project_services(query_db, project_id)
                    data_dict = export_data.model_dump(mode='json', by_alias=True)
                    json_bytes = json.dumps(data_dict, ensure_ascii=False, default=str).encode('utf-8')

                    project_name = export_data.project.project_name or f'project_{project_id}'
                    safe_name = cls._safe_filename(project_name)
                    filename = f'{safe_name}_export_{project_id}.json'
                    zip_file.writestr(filename, json_bytes)
                    exported_count += 1
                except Exception as e:
                    logger.error(f'导出工程 {project_id} 失败: {e}')
                    errors.append(f'工程ID {project_id}: {str(e)}')

        if exported_count == 0:
            raise ServiceException(message='未能导出任何工程，请检查工程ID是否有效')

        buffer.seek(0)
        zip_name = f'project_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'

        # 记录导出过程中失败的工程，作为响应头提示
        if errors:
            logger.warning(f'部分工程导出失败: {"；".join(errors)}')

        return buffer, zip_name

    @classmethod
    def _extract_device_ids_from_topology(cls, topology_data: dict) -> Set[int]:
        """
        从拓扑数据中提取设备ID
        """
        device_ids: Set[int] = set()
        if not topology_data:
            return device_ids

        # 从 graph.cells 或 nodes 中提取
        graph = topology_data.get('graph', {})
        cells = graph.get('cells', [])
        nodes = topology_data.get('nodes', [])

        for cell in cells:
            data = cell.get('data', {})
            device_id = data.get('deviceId')
            if device_id:
                device_ids.add(int(device_id))

        for node in nodes:
            data = node.get('data', {})
            device_id = data.get('deviceId')
            if device_id:
                device_ids.add(int(device_id))

        return device_ids

    @classmethod
    async def import_project_services(
        cls, query_db: AsyncSession, import_data: ProjectImportDataModel, operator: str
    ):
        """
        导入工程数据service

        :param query_db: orm对象
        :param import_data: 导入数据
        :param operator: 操作人
        :return: 导入结果
        """
        # 获取原始项目名称，确保不为空
        original_name = import_data.project.project_name
        base_name = original_name.strip() if original_name else '未命名工程'
        if not base_name:
            base_name = '未命名工程'
        import_suffix = '-外部导入'
        project_name = base_name if base_name.endswith(import_suffix) else f'{base_name}{import_suffix}'

        # 1. 创建新工程
        new_project = ProjectModel(
            project_name=project_name,
            project_desc=import_data.project.project_desc,
            create_by=operator,
            create_time=datetime.now(),
            update_by=operator,
            update_time=datetime.now(),
        )

        # 自动生成工程编码
        new_project.project_code = await cls._generate_project_code(query_db)
        db_project = await ProjectDao.add_project_dao(query_db, new_project)
        new_project_id = db_project.project_id

        # 2. 处理设备：建立旧ID到新ID的映射
        device_id_mapping = {}  # old_device_id -> new_device_id
        for export_device in import_data.devices:
            old_device_id = export_device.device_id

            # 查找是否已存在相同名称和类型的设备
            existing_device = await DeviceDao.find_device_by_name_and_type(
                query_db, export_device.device_name, export_device.device_type
            )

            if existing_device:
                # 使用现有设备
                device_id_mapping[old_device_id] = existing_device.device_id
            else:
                # 创建新设备
                new_device = DeviceDO(
                    device_name=export_device.device_name,
                    device_type=export_device.device_type,
                    category_name=export_device.category_name,
                    manufacturer=export_device.manufacturer,
                    model=export_device.model,
                    version=export_device.version,
                    bus_type=export_device.bus_type,
                    remark=export_device.remark,
                    create_by=operator,
                    create_time=datetime.now(),
                    update_by=operator,
                    update_time=datetime.now(),
                )
                new_device = await DeviceDao.add_device(query_db, new_device)

                # 创建设备接口
                for intf in export_device.interfaces:
                    new_interface = DeviceInterfaceDO(
                        device_id=new_device.device_id,
                        interface_name=intf.interface_name,
                        interface_type=intf.interface_type,
                        position=intf.position,
                        description=intf.description,
                        params=intf.params,
                        message_config=intf.message_config,
                        create_time=datetime.now(),
                        update_time=datetime.now(),
                    )
                    await DeviceDao.add_device_interface(query_db, new_interface)

                device_id_mapping[old_device_id] = new_device.device_id

        # 3. 创建版本和拓扑
        first_version_id = None
        for export_version in import_data.versions:
            # 创建版本
            new_version = ProjectVersionModel(
                project_id=new_project_id,
                version_number=export_version.version_number,
                version_name=export_version.version_name,
                description=export_version.description,
                status=export_version.status,
                is_locked='0',  # 导入时不保留固化状态
                create_by=operator,
                create_time=datetime.now(),
                update_by=operator,
                update_time=datetime.now(),
            )
            db_version = await ProjectVersionDao.add_project_version_dao(query_db, new_version)
            
            if first_version_id is None:
                first_version_id = db_version.version_id

            # 创建拓扑数据（更新设备ID引用）
            if export_version.topology:
                updated_topology = cls._update_topology_device_ids(
                    export_version.topology, device_id_mapping
                )
                new_topology = ProjectTopologyModel(
                    project_id=new_project_id,
                    version_id=db_version.version_id,
                    topology_data=updated_topology,
                    create_by=operator,
                    create_time=datetime.now(),
                    update_by=operator,
                    update_time=datetime.now(),
                )
                await ProjectTopologyDao.save_project_topology_dao(query_db, new_topology)

        await query_db.commit()

        return CrudResponseModel(
            is_success=True,
            message='导入成功',
            result={
                'projectId': new_project_id,
                'versionId': first_version_id,
            }
        )

    @classmethod
    def _update_topology_device_ids(cls, topology_data: dict, device_id_mapping: dict) -> dict:
        """
        更新拓扑数据中的设备ID引用
        """
        import copy
        updated = copy.deepcopy(topology_data)

        # 更新 graph.cells 中的设备ID
        graph = updated.get('graph', {})
        cells = graph.get('cells', [])
        for cell in cells:
            data = cell.get('data', {})
            old_device_id = data.get('deviceId')
            if old_device_id and old_device_id in device_id_mapping:
                data['deviceId'] = device_id_mapping[old_device_id]

        # 更新 nodes 中的设备ID
        nodes = updated.get('nodes', [])
        for node in nodes:
            data = node.get('data', {})
            old_device_id = data.get('deviceId')
            if old_device_id and old_device_id in device_id_mapping:
                data['deviceId'] = device_id_mapping[old_device_id]

        return updated

    @classmethod
    async def import_projects_from_zip_services(
        cls, query_db: AsyncSession, file_bytes: bytes, operator: str
    ):
        """
        批量导入工程（zip包）

        :param query_db: orm对象
        :param file_bytes: zip文件字节流
        :param operator: 操作人
        :return: 导入结果摘要
        """
        if not file_bytes:
            raise ServiceException(message='上传文件为空')

        logger.info(f'导入文件大小: {len(file_bytes)} 字节')
        logger.info(f'文件头部(hex): {file_bytes[:20].hex() if len(file_bytes) >= 20 else file_bytes.hex()}')

        def _as_zip_buffer(raw_bytes: bytes) -> BytesIO | None:
            buf = BytesIO(raw_bytes)
            if is_zipfile(buf):
                buf.seek(0)
                return buf
            return None

        # 先尝试直接识别zip，其次尝试解码base64再识别zip
        file_buffer = _as_zip_buffer(file_bytes)
        if not file_buffer:
            try:
                decoded = base64.b64decode(file_bytes, validate=True)
                file_buffer = _as_zip_buffer(decoded)
                if file_buffer:
                    file_bytes = decoded
            except Exception:
                file_buffer = None

        # 以zip方式解析
        results = []
        success_count = 0
        failed_count = 0

        try:
            if file_buffer:
                with ZipFile(file_buffer, 'r') as zip_file:
                    json_files = [
                        name for name in zip_file.namelist()
                        if not name.endswith('/') and name.lower().endswith('.json')
                    ]

                    if not json_files:
                        raise ServiceException(message='zip包中未找到json工程文件')

                    for name in json_files:
                        try:
                            file_content = zip_file.read(name).decode('utf-8')
                            import_result = await cls._import_single_project_from_json(
                                query_db, file_content, operator, name
                            )
                            success_count += 1
                            results.append(import_result)
                        except Exception as e:
                            failed_count += 1
                            await query_db.rollback()
                            results.append({
                                'fileName': name,
                                'status': 'failed',
                                'message': str(e),
                            })
            else:
                # 尝试将文件作为单个json工程导入，兼容未压缩的导出文件
                try:
                    file_content = file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    raise ServiceException(message='上传文件格式错误，请选择有效的zip导出包')

                try:
                    import_result = await cls._import_single_project_from_json(
                        query_db, file_content, operator, 'project.json'
                    )
                    success_count = 1
                    results.append(import_result)
                except Exception as e:
                    await query_db.rollback()
                    raise ServiceException(message=str(e))
        except ServiceException:
            raise
        except Exception as e:
            raise ServiceException(message=str(e))

        return {
            'successCount': success_count,
            'failedCount': failed_count,
            'details': results,
        }

    @classmethod
    async def _import_single_project_from_json(
        cls, query_db: AsyncSession, json_text: str, operator: str, filename: str
    ) -> dict:
        """
        从单个json文本导入工程（用于zip内文件或直接上传json）
        """
        raw_data = json.loads(json_text)
        if isinstance(raw_data, dict) and 'code' in raw_data and 'msg' in raw_data and 'project' not in raw_data:
            # 后端错误信息被误当成导出包上传
            err_code = raw_data.get('code')
            err_msg = raw_data.get('msg') or '文件内容无效'
            raise ServiceException(
                message=f'导入文件不是有效的工程导出包：后端返回 code={err_code}, msg={err_msg}'
            )

        project_name_from_json = raw_data.get('project', {}).get('projectName')
        if not project_name_from_json:
            raise ServiceException(message='缺少工程名称（project.projectName）')

        import_data = ProjectImportDataModel(**raw_data)
        import_result = await cls.import_project_services(
            query_db, import_data, operator
        )
        return {
            'fileName': filename,
            'status': 'success',
            'projectId': import_result.result.get('projectId'),
            'versionId': import_result.result.get('versionId'),
        }

    @staticmethod
    def _safe_filename(name: str) -> str:
        """
        生成文件安全的工程名称
        """
        safe = re.sub(r'[\\\\/:*?\"<>|\\s]+', '_', name.strip()) if name else 'project'
        return safe or 'project'
