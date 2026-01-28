from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ValidationException, ResourceNotFoundException, ResourceConflictException
from config.error_codes import ErrorCode
from module_admin.entity.do.project_version_do import SysProjectVersion
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_version_vo import (
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    DeleteProjectVersionModel,
    CloneProjectVersionModel,
    LockProjectVersionModel
)
from module_admin.repository import ProjectVersionRepository, ProjectTopologyRepository
from utils.common_util import CamelCaseUtil
from utils.page_util import PageResponseModel
from utils.transaction_manager import transactional


class ProjectVersionService:
    """
    项目版本管理模块服务层
    """

    @classmethod
    async def get_project_version_list_services(
        cls, query_db: AsyncSession, query_object: ProjectVersionPageQueryModel, is_page: bool = False
    ):
        """
        获取版本列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 版本列表信息对象
        """
        version_repo = ProjectVersionRepository(query_db)
        if is_page:
            version_list_result = await version_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                project_id=query_object.project_id,
                version_name=query_object.version_name,
                version_number=query_object.version_number,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time
            )
            return PageResponseModel(
                **{
                    **version_list_result.model_dump(),
                    'rows': CamelCaseUtil.transform_result(version_list_result.rows)
                }
            )
        else:
            version_list_result = await version_repo.find_by_project(query_object.project_id)
            return CamelCaseUtil.transform_result(version_list_result)

    @classmethod
    @transactional()
    async def add_project_version_services(cls, query_db: AsyncSession, page_object: ProjectVersionModel):
        """
        新增版本信息service

        :param query_db: orm对象
        :param page_object: 新增版本对象
        :return: 新增版本校验结果
        """
        version_repo = ProjectVersionRepository(query_db)
        # 检查版本号是否唯一
        is_unique = await version_repo.check_version_number_unique(
            page_object.project_id, page_object.version_number
        )
        if not is_unique:
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                message=f'版本号 {page_object.version_number} 已存在'
            )
        
        db_version = SysProjectVersion(**page_object.model_dump())
        await version_repo.add(db_version)
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_project_version_services(cls, query_db: AsyncSession, page_object: ProjectVersionModel):
        """
        编辑版本信息service

        :param query_db: orm对象
        :param page_object: 编辑版本对象
        :return: 编辑版本校验结果
        """
        version_repo = ProjectVersionRepository(query_db)
        # 检查版本是否存在
        version = await version_repo.find_by_id(page_object.version_id)
        if not version:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='版本不存在'
            )
        
        # 检查版本是否已固化
        if version.is_locked == '1':
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='固化版本不允许编辑'
            )
        
        # 检查版本号是否唯一
        if page_object.version_number and page_object.version_number != version.version_number:
            is_unique = await version_repo.check_version_number_unique(
                version.project_id, page_object.version_number, page_object.version_id
            )
            if not is_unique:
                raise ServiceException(message=f'版本号 {page_object.version_number} 已存在')
        
        # 更新版本信息
        update_data = page_object.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(version, key) and value is not None:
                setattr(version, key, value)
        await query_db.flush()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def delete_project_version_services(cls, query_db: AsyncSession, page_object: DeleteProjectVersionModel):
        """
        删除版本信息service

        :param query_db: orm对象
        :param page_object: 删除版本对象
        :return: 删除版本校验结果
        """
        if not page_object.version_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='version_ids',
                message='传入版本ID为空'
            )
        
        version_id_list = [int(version_id) for version_id in page_object.version_ids.split(',') if version_id]
        if not version_id_list:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='version_ids',
                message='未解析到有效版本ID'
            )

        version_repo = ProjectVersionRepository(query_db)
        versions = []
        project_delete_map = {}

        for version_id in version_id_list:
            version = await version_repo.find_by_id(version_id)
            if not version:
                raise ServiceException(message=f'版本ID {version_id} 不存在或已删除')
            if version.is_locked == '1':
                raise ServiceException(message=f'版本 {version.version_name} 已固化，不允许删除')
            versions.append(version)
            project_delete_map[version.project_id] = project_delete_map.get(version.project_id, 0) + 1

        project_counts = await version_repo.count_by_projects(list(project_delete_map.keys()))

        for project_id, delete_count in project_delete_map.items():
            total_count = project_counts.get(project_id, 0)
            if total_count - delete_count < 1:
                raise ServiceException(message=f'项目ID {project_id} 至少需要保留一个版本，无法全部删除')

        await version_repo.soft_delete_batch(version_id_list, page_object.update_by or '')
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def project_version_detail_services(cls, query_db: AsyncSession, version_id: int):
        """
        获取版本详细信息service

        :param query_db: orm对象
        :param version_id: 版本ID
        :return: 版本ID对应的信息
        """
        version_repo = ProjectVersionRepository(query_db)
        version = await version_repo.find_by_id(version_id)
        if version:
            result = CamelCaseUtil.transform_result(version)
        else:
            result = CamelCaseUtil.transform_result({})

        return result

    @classmethod
    @transactional()
    async def clone_project_version_services(cls, query_db: AsyncSession, clone_object: CloneProjectVersionModel):
        """
        克隆版本信息service

        :param query_db: orm对象
        :param clone_object: 克隆版本对象
        :return: 克隆版本校验结果
        """
        version_repo = ProjectVersionRepository(query_db)
        topology_repo = ProjectTopologyRepository(query_db)
        
        # 获取源版本信息
        source_version = await version_repo.find_by_id(clone_object.source_version_id)
        if not source_version:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='源版本不存在'
            )
        
        # 检查新版本号是否唯一
        is_unique = await version_repo.check_version_number_unique(
            source_version.project_id, clone_object.version_number
        )
        if not is_unique:
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                message=f'版本号 {clone_object.version_number} 已存在'
            )
        
        # 创建新版本
        new_version = SysProjectVersion(
            project_id=source_version.project_id,
            version_number=clone_object.version_number,
            version_name=clone_object.version_name,
            description=clone_object.description or source_version.description,
            status='1',
            is_locked='0',
            create_by=clone_object.create_by,
            create_time=clone_object.create_time
        )
        new_version_do = await version_repo.add(new_version)

        # 克隆拓扑数据（如果源版本存在拓扑）
        source_topology = await topology_repo.find_by_project_and_version(
            source_version.project_id, source_version.version_id
        )
        if source_topology:
            await topology_repo.save_topology(
                project_id=source_version.project_id,
                version_id=new_version_do.version_id,
                topology_data=source_topology.topology_data,
                create_by=clone_object.create_by,
                update_by=clone_object.create_by
            )

        return CrudResponseModel(is_success=True, message='克隆成功')

    @classmethod
    @transactional()
    async def lock_project_version_services(cls, query_db: AsyncSession, lock_object: LockProjectVersionModel):
        """
        固化/解除固化版本信息service

        :param query_db: orm对象
        :param lock_object: 固化对象
        :return: 固化校验结果
        """
        version_repo = ProjectVersionRepository(query_db)
        # 检查版本是否存在
        version = await version_repo.find_by_id(lock_object.version_id)
        if not version:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='版本不存在'
            )
        
        await version_repo.lock_version(
            version_id=lock_object.version_id,
            is_locked=lock_object.is_locked,
            update_by=lock_object.update_by or '',
            locked_by=lock_object.locked_by if lock_object.is_locked == '1' else None,
            locked_time=datetime.now() if lock_object.is_locked == '1' else None
        )
        
        message = '固化成功' if lock_object.is_locked == '1' else '解除固化成功'
        return CrudResponseModel(is_success=True, message=message)

    @classmethod
    @transactional()
    async def unlock_project_versions_by_project_services(
        cls, query_db: AsyncSession, project_id: int, operator: str | None = None
    ):
        """
        批量解除指定项目下的固化版本
        """
        if not project_id:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='project_id',
                message='工程ID不能为空'
            )

        version_repo = ProjectVersionRepository(query_db)
        locked_map = await version_repo.find_locked_by_projects([project_id])
        locked_versions = locked_map.get(project_id, [])
        if not locked_versions:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='当前工程不存在需要解除固化的版本'
            )

        await version_repo.unlock_by_project(project_id, operator)
        return CrudResponseModel(is_success=True, message='批量解除固化成功')
