import base64
import json
import re
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Set
from zipfile import is_zipfile

from sqlalchemy.ext.asyncio import AsyncSession

from config.error_codes import ErrorCode
from exceptions.exception import ResourceNotFoundException, ServiceException, ValidationException
from module_admin.entity.do.device_do import DeviceDO, DeviceInterfaceDO
from module_admin.entity.do.enums import EnableStatusEnum, LockStatusEnum
from module_admin.entity.do.project_do import ProjectDO
from module_admin.entity.do.project_version_do import ProjectVersionDO
from module_admin.entity.vo.common_vo import CrudResponseModel
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
from ports import (
    IDeviceInterfaceRepository,
    IDeviceRepository,
    IProjectRepository,
    IProjectTopologyRepository,
    IProjectVersionRepository,
)
from utils.common_util import CamelCaseUtil
from utils.io_toolkit import JsonExporter, ZipEntry, ZipExporter, ZipImporter
from utils.log_util import logger
from utils.transaction_manager import transactional


class ProjectService:
    """
    工程管理模块服务层
    """

    def __init__(
        self,
        project_repo: IProjectRepository,
        version_repo: IProjectVersionRepository,
        topology_repo: IProjectTopologyRepository,
        device_repo: IDeviceRepository,
        interface_repo: IDeviceInterfaceRepository,
        query_db: AsyncSession,
    ):
        self.project_repo = project_repo
        self.version_repo = version_repo
        self.topology_repo = topology_repo
        self.device_repo = device_repo
        self.interface_repo = interface_repo
        self.query_db = query_db

    async def get_project_list(self, query_object: ProjectPageQueryModel, is_page: bool = False):
        return await self.get_project_list_services(query_object, is_page=is_page)

    async def add_project(self, page_object: ProjectModel, operator: Optional[str] = None):
        return await self.add_project_services(page_object, operator=operator)

    async def edit_project(self, page_object: ProjectModel, operator: Optional[str] = None):
        return await self.edit_project_services(page_object, operator=operator)

    async def delete_project(self, page_object: DeleteProjectModel, operator: Optional[str] = None):
        return await self.delete_project_services(page_object, operator=operator)

    async def get_project_detail(self, project_id: int):
        return await self.project_detail_services(project_id)

    async def export_project_zip(self, project_id: int):
        return await self.export_project_zip_services(project_id)

    async def export_projects_zip(self, project_ids: List[int]):
        return await self.export_projects_zip_services(project_ids)

    async def import_project(self, import_data: ProjectImportDataModel, operator: str):
        return await self.import_project_services(import_data, operator)

    async def import_projects_from_zip(self, file_bytes: bytes, operator: str):
        return await self.import_projects_from_zip_services(file_bytes, operator)

    async def get_project_list_services(self, query_object: ProjectPageQueryModel, is_page: bool = False):
        """
        获取工程列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 工程列表信息对象
        """
        if is_page:
            return await self.project_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )

        project_list_result = await self.project_repo.find_all_active()
        return CamelCaseUtil.transform_result(project_list_result)

    @transactional()
    async def add_project_services(
        self,
        page_object: ProjectModel,
        operator: Optional[str] = None,
    ):
        """
        新增工程信息service

        :param page_object: 新增工程对象
        :return: 新增工程校验结果
        """
        # 自动生成工程编码
        if not page_object.project_code:
            page_object.project_code = await self._generate_project_code()

        now = datetime.now()
        effective_operator = operator or page_object.create_by or page_object.update_by or 'system'
        if not page_object.create_by:
            page_object.create_by = effective_operator
        if not page_object.update_by:
            page_object.update_by = effective_operator
        if not page_object.create_time:
            page_object.create_time = now
        if not page_object.update_time:
            page_object.update_time = now

        db_project = ProjectDO(**page_object.model_dump())
        new_project = await self.project_repo.add(db_project)

        # 创建默认初始版本
        default_version = ProjectVersionDO(
            project_id=new_project.project_id,
            version_number='v1.0.0',
            version_name='初始版本',
            description='项目初始版本',
            status=EnableStatusEnum.ENABLED.value,
            is_locked=LockStatusEnum.UNLOCKED.value,
            create_by=page_object.create_by,
            create_time=now,
            update_by=page_object.update_by,
            update_time=now,
        )
        new_version = await self.version_repo.add(default_version)

        return CrudResponseModel(
            is_success=True,
            message='新增成功',
            result={'projectId': new_project.project_id, 'versionId': new_version.version_id},
        )

    async def _generate_project_code(self) -> str:
        """
        生成工程编码：格式为 PRJ + 年月日 + 4位序号，例如：PRJ202511130001

        :return: 工程编码
        """
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'PRJ{today}'
        max_code = await self.project_repo.get_max_project_code_by_prefix(prefix)

        if max_code:
            # 提取序号并加1
            seq = int(max_code[-4:]) + 1
        else:
            seq = 1

        return f'{prefix}{seq:04d}'

    @transactional()
    async def edit_project_services(
        self,
        page_object: ProjectModel,
        operator: Optional[str] = None,
    ):
        """
        编辑工程信息service

        :param page_object: 编辑工程对象
        :return: 编辑工程校验结果
        """
        project = await self.project_repo.find_by_id(page_object.project_id)
        if project:
            if operator and not page_object.update_by:
                page_object.update_by = operator
            if not page_object.update_time:
                page_object.update_time = datetime.now()
            update_data = page_object.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(project, key) and value is not None:
                    setattr(project, key, value)
            await self.project_repo.update(project)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_project_services(
        self,
        page_object: DeleteProjectModel,
        operator: Optional[str] = None,
    ):
        """
        删除工程信息service

        :param page_object: 删除工程对象
        :return: 删除工程校验结果
        """
        if not page_object.project_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='project_ids', user_message='传入工程id为空'
            )

        if operator and not page_object.update_by:
            page_object.update_by = operator

        project_id_list = [int(project_id) for project_id in page_object.project_ids.split(',') if project_id]
        if not project_id_list:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='project_ids', user_message='未解析到有效工程id'
            )

        locked_map = await self.version_repo.find_locked_by_projects(project_id_list)
        if locked_map:
            blocked_messages = []
            for project_id, versions in locked_map.items():
                version_names = '、'.join([version.version_name for version in versions])
                blocked_messages.append(f'工程ID {project_id} 存在固化版本：{version_names}')
            raise ServiceException(user_message='；'.join(blocked_messages))

        await self.project_repo.soft_delete_batch(project_id_list, page_object.update_by or '')
        return CrudResponseModel(is_success=True, message='删除成功')

    async def project_detail_services(self, project_id: int):
        """
        获取工程详细信息service

        :param project_id: 工程id
        :return: 工程id对应的信息
        """
        project = await self.project_repo.find_by_id(project_id)
        if project:
            return CamelCaseUtil.transform_result(project)

        raise ResourceNotFoundException(
            user_message='工程不存在',
            error_code=ErrorCode.PROJECT_NOT_FOUND,
            developer_message=f'project_id={project_id} not found',
        )

    async def export_project_services(self, project_id: int):
        """
        导出工程数据service

        :param project_id: 工程id
        :return: 工程导出数据
        """
        # 1. 获取工程基本信息
        project = await self.project_repo.find_by_id(project_id)
        if not project:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='工程不存在')

        # 2. 获取所有版本
        versions = await self.version_repo.find_by_project(project_id)
        version_ids = [v.version_id for v in versions]

        # 3. 获取所有版本的拓扑数据
        topologies = await self.topology_repo.find_by_version_ids(project_id, version_ids)
        topo_map = {t.version_id: t.topology_data for t in topologies}

        # 4. 从拓扑数据中提取设备ID
        device_ids: Set[int] = set()
        for topo_data in topo_map.values():
            if topo_data:
                device_ids.update(self._extract_device_ids_from_topology(topo_data))

        # 5. 获取设备完整信息
        devices = await self.device_repo.find_by_ids(list(device_ids))

        # 6. 构建导出数据
        export_project = ExportProjectModel(
            project_name=project.project_name,
            project_code=project.project_code,
            project_desc=project.project_desc,
            create_by=project.create_by,
            create_time=project.create_time,
        )

        export_versions = []
        for version in versions:
            export_versions.append(
                ExportVersionModel(
                    version_number=version.version_number,
                    version_name=version.version_name,
                    description=version.description,
                    status=version.status,
                    is_locked=version.is_locked,
                    topology=topo_map.get(version.version_id),
                )
            )

        export_devices = []
        for device in devices:
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
            export_devices.append(
                ExportDeviceModel(
                    device_id=device.device_id,
                    device_name=device.device_name,
                    device_type=device.device_type,
                    category_name=device.category_name,
                    manufacturer=device.manufacturer,
                    model=device.model,
                    version=device.version,
                    bus_type=device.bus_type,
                    remark=device.remark,
                    interfaces=interfaces,
                )
            )

        return ProjectExportDataModel(
            export_version='1.0.0',
            export_time=datetime.now(),
            project=export_project,
            versions=export_versions,
            devices=export_devices,
        )

    async def export_project_zip_services(self, project_id: int):
        """
        导出单个工程为zip包
        """
        export_data = await self.export_project_services(project_id)
        data_dict = export_data.model_dump(mode='json', by_alias=True)

        project_name = export_data.project.project_name or f'project_{project_id}'
        safe_name = self._safe_filename(project_name)
        json_filename = f'{safe_name}_export_{project_id}.json'
        zip_name = f'{safe_name}_export_{project_id}.zip'

        json_exporter = JsonExporter()
        zip_exporter = ZipExporter()

        json_result = await json_exporter.export(data_dict, filename=json_filename)
        zip_entry = ZipEntry(filename=json_result.filename, content=json_result.content)
        zip_result = await zip_exporter.export([zip_entry], filename=zip_name)

        buffer = BytesIO(zip_result.content)
        buffer.seek(0)
        return buffer, zip_result.filename

    async def export_projects_zip_services(self, project_ids: List[int]):
        """
        批量导出工程数据并打包为zip

        :param project_ids: 工程id列表
        :return: (zip二进制流, 文件名)
        """
        if not project_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='project_ids', user_message='请选择需要导出的工程'
            )

        errors = []
        exported_count = 0

        json_exporter = JsonExporter()
        zip_exporter = ZipExporter()
        entries: List[ZipEntry] = []

        for project_id in project_ids:
            try:
                export_data = await self.export_project_services(project_id)
                data_dict = export_data.model_dump(mode='json', by_alias=True)
                project_name = export_data.project.project_name or f'project_{project_id}'
                safe_name = self._safe_filename(project_name)
                filename = f'{safe_name}_export_{project_id}.json'
                json_result = await json_exporter.export(data_dict, filename=filename)
                entries.append(ZipEntry(filename=json_result.filename, content=json_result.content))
                exported_count += 1
            except Exception as error:
                logger.error(f'导出工程 {project_id} 失败: {error}')
                errors.append(f'工程ID {project_id}: {str(error)}')

        if exported_count == 0:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, user_message='未能导出任何工程，请检查工程ID是否有效'
            )

        zip_name = f'project_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
        zip_result = await zip_exporter.export(entries, filename=zip_name)

        # 记录导出过程中失败的工程，作为响应头提示
        if errors:
            logger.warning(f'部分工程导出失败: {"；".join(errors)}')

        buffer = BytesIO(zip_result.content)
        buffer.seek(0)
        return buffer, zip_result.filename

    @staticmethod
    def _extract_device_ids_from_topology(topology_data: dict) -> Set[int]:
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

    @transactional()
    async def import_project_services(self, import_data: ProjectImportDataModel, operator: str):
        """
        导入工程数据service

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
        new_project.project_code = await self._generate_project_code()

        db_project = ProjectDO(**new_project.model_dump())
        db_project = await self.project_repo.add(db_project)
        new_project_id = db_project.project_id

        # 2. 处理设备：建立旧ID到新ID的映射
        device_id_mapping = {}  # old_device_id -> new_device_id
        for export_device in import_data.devices:
            old_device_id = export_device.device_id

            # 查找是否已存在相同名称和类型的设备
            existing_device = await self.device_repo.find_by_name_and_type(
                export_device.device_name,
                export_device.device_type,
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
                new_device = await self.device_repo.add(new_device)

                # 创建设备接口
                for interface in export_device.interfaces:
                    new_interface = DeviceInterfaceDO(
                        device_id=new_device.device_id,
                        interface_name=interface.interface_name,
                        interface_type=interface.interface_type,
                        position=interface.position,
                        description=interface.description,
                        params=interface.params,
                        message_config=interface.message_config,
                        create_time=datetime.now(),
                        update_time=datetime.now(),
                    )
                    await self.interface_repo.add(new_interface)

                device_id_mapping[old_device_id] = new_device.device_id

        # 3. 创建版本和拓扑
        first_version_id = None
        for export_version in import_data.versions:
            # 创建版本
            new_version = ProjectVersionDO(
                project_id=new_project_id,
                version_number=export_version.version_number,
                version_name=export_version.version_name,
                description=export_version.description,
                status=export_version.status,
                is_locked=LockStatusEnum.UNLOCKED.value,  # 导入时不保留固化状态
                create_by=operator,
                create_time=datetime.now(),
                update_by=operator,
                update_time=datetime.now(),
            )
            db_version = await self.version_repo.add(new_version)

            if first_version_id is None:
                first_version_id = db_version.version_id

            # 创建拓扑数据（更新设备ID引用）
            if export_version.topology:
                updated_topology = self._update_topology_device_ids(export_version.topology, device_id_mapping)
                await self.topology_repo.save_topology(
                    project_id=new_project_id,
                    version_id=db_version.version_id,
                    topology_data=updated_topology,
                    create_by=operator,
                    update_by=operator,
                )

        return CrudResponseModel(
            is_success=True,
            message='导入成功',
            result={
                'projectId': new_project_id,
                'versionId': first_version_id,
            },
        )

    @staticmethod
    def _update_topology_device_ids(topology_data: dict, device_id_mapping: dict) -> dict:
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

    async def import_projects_from_zip_services(self, file_bytes: bytes, operator: str):
        """
        批量导入工程（zip包）

        :param file_bytes: zip文件字节流
        :param operator: 操作人
        :return: 导入结果摘要
        """
        if not file_bytes:
            raise ValidationException(error_code=ErrorCode.INVALID_INPUT, user_message='上传文件为空')

        logger.info(f'导入文件大小: {len(file_bytes)} 字节')
        logger.info(f'文件头部(hex): {file_bytes[:20].hex() if len(file_bytes) >= 20 else file_bytes.hex()}')

        def _as_zip_buffer(raw_bytes: bytes) -> Optional[BytesIO]:
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

        results = []
        success_count = 0
        failed_count = 0

        try:
            if file_buffer:
                zip_importer = ZipImporter(
                    file_filter=lambda name: name.lower().endswith('.json'),
                )
                zip_result = await zip_importer.import_data(file_bytes)
                entries = zip_result.data or {}
                if not entries:
                    raise ServiceException(message='zip包中未找到json工程文件')

                for name, content in entries.items():
                    try:
                        file_content = content.decode('utf-8')
                        import_result = await self._import_single_project_from_json(file_content, operator, name)
                        success_count += 1
                        results.append(import_result)
                    except Exception as error:
                        failed_count += 1
                        await self.query_db.rollback()
                        results.append(
                            {
                                'fileName': name,
                                'status': 'failed',
                                'message': str(error),
                            }
                        )
            else:
                # 尝试将文件作为单个json工程导入，兼容未压缩的导出文件
                try:
                    file_content = file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    raise ServiceException(message='上传文件格式错误，请选择有效的zip导出包')

                try:
                    import_result = await self._import_single_project_from_json(
                        file_content,
                        operator,
                        'project.json',
                    )
                    success_count = 1
                    results.append(import_result)
                except Exception as error:
                    await self.query_db.rollback()
                    raise ServiceException(message=str(error))
        except ServiceException:
            raise
        except Exception as error:
            raise ServiceException(message=str(error))

        return {
            'successCount': success_count,
            'failedCount': failed_count,
            'details': results,
        }

    async def _import_single_project_from_json(self, json_text: str, operator: str, filename: str) -> dict:
        """
        从单个json文本导入工程（用于zip内文件或直接上传json）
        """
        raw_data = json.loads(json_text)
        if isinstance(raw_data, dict) and 'code' in raw_data and 'msg' in raw_data and 'project' not in raw_data:
            # 后端错误信息被误当成导出包上传
            err_code = raw_data.get('code')
            err_msg = raw_data.get('msg') or '文件内容无效'
            raise ServiceException(message=f'导入文件不是有效的工程导出包：后端返回 code={err_code}, msg={err_msg}')

        project_name_from_json = raw_data.get('project', {}).get('projectName')
        if not project_name_from_json:
            raise ServiceException(message='缺少工程名称（project.projectName）')

        import_data = ProjectImportDataModel(**raw_data)
        import_result = await self.import_project_services(import_data, operator)
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
        safe = re.sub(r'[\\/:*?"<>|\s]+', '_', name.strip()) if name else 'project'
        return safe or 'project'
