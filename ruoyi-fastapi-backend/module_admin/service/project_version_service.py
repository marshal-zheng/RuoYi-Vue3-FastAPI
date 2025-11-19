from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_admin.dao.project_version_dao import ProjectVersionDao
from module_admin.dao.project_topology_dao import ProjectTopologyDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from module_admin.entity.vo.project_version_vo import (
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    DeleteProjectVersionModel,
    CloneProjectVersionModel,
    LockProjectVersionModel
)
from utils.common_util import CamelCaseUtil
from utils.page_util import PageResponseModel


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
        version_list_result = await ProjectVersionDao.get_project_version_list(query_db, query_object, is_page)
        if is_page:
            return PageResponseModel(
                **{
                    **version_list_result.model_dump(),
                    'rows': CamelCaseUtil.transform_result(version_list_result.rows)
                }
            )
        else:
            return CamelCaseUtil.transform_result(version_list_result)

    @classmethod
    async def add_project_version_services(cls, query_db: AsyncSession, page_object: ProjectVersionModel):
        """
        新增版本信息service

        :param query_db: orm对象
        :param page_object: 新增版本对象
        :return: 新增版本校验结果
        """
        try:
            # 检查版本号是否唯一
            is_unique = await ProjectVersionDao.check_version_number_unique(
                query_db, page_object.project_id, page_object.version_number
            )
            if not is_unique:
                raise ServiceException(message=f'版本号 {page_object.version_number} 已存在')
            
            await ProjectVersionDao.add_project_version_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_project_version_services(cls, query_db: AsyncSession, page_object: ProjectVersionModel):
        """
        编辑版本信息service

        :param query_db: orm对象
        :param page_object: 编辑版本对象
        :return: 编辑版本校验结果
        """
        try:
            # 检查版本是否存在
            version = await ProjectVersionDao.get_project_version_detail_by_id(query_db, page_object.version_id)
            if not version:
                raise ServiceException(message='版本不存在')
            
            # 检查版本是否已固化
            if version.is_locked == '1':
                raise ServiceException(message='固化版本不允许编辑')
            
            # 检查版本号是否唯一
            if page_object.version_number and page_object.version_number != version.version_number:
                is_unique = await ProjectVersionDao.check_version_number_unique(
                    query_db, version.project_id, page_object.version_number, page_object.version_id
                )
                if not is_unique:
                    raise ServiceException(message=f'版本号 {page_object.version_number} 已存在')
            
            await ProjectVersionDao.edit_project_version_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_project_version_services(cls, query_db: AsyncSession, page_object: DeleteProjectVersionModel):
        """
        删除版本信息service

        :param query_db: orm对象
        :param page_object: 删除版本对象
        :return: 删除版本校验结果
        """
        if not page_object.version_ids:
            raise ServiceException(message='传入版本ID为空')
        
        try:
            version_id_list = [int(version_id) for version_id in page_object.version_ids.split(',') if version_id]
            if not version_id_list:
                raise ServiceException(message='未解析到有效版本ID')

            versions = []
            project_delete_map = {}

            for version_id in version_id_list:
                version = await ProjectVersionDao.get_project_version_detail_by_id(query_db, version_id)
                if not version:
                    raise ServiceException(message=f'版本ID {version_id} 不存在或已删除')
                if version.is_locked == '1':
                    raise ServiceException(message=f'版本 {version.version_name} 已固化，不允许删除')
                versions.append(version)
                project_delete_map[version.project_id] = project_delete_map.get(version.project_id, 0) + 1

            project_counts = await ProjectVersionDao.get_project_version_counts(
                query_db, list(project_delete_map.keys())
            )

            for project_id, delete_count in project_delete_map.items():
                total_count = project_counts.get(project_id, 0)
                if total_count - delete_count < 1:
                    raise ServiceException(message=f'项目ID {project_id} 至少需要保留一个版本，无法全部删除')

            await ProjectVersionDao.delete_project_version_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def project_version_detail_services(cls, query_db: AsyncSession, version_id: int):
        """
        获取版本详细信息service

        :param query_db: orm对象
        :param version_id: 版本ID
        :return: 版本ID对应的信息
        """
        version = await ProjectVersionDao.get_project_version_detail_by_id(query_db, version_id)
        if version:
            result = CamelCaseUtil.transform_result(version)
        else:
            result = CamelCaseUtil.transform_result({})

        return result

    @classmethod
    async def clone_project_version_services(cls, query_db: AsyncSession, clone_object: CloneProjectVersionModel):
        """
        克隆版本信息service

        :param query_db: orm对象
        :param clone_object: 克隆版本对象
        :return: 克隆版本校验结果
        """
        try:
            # 获取源版本信息
            source_version = await ProjectVersionDao.get_project_version_detail_by_id(
                query_db, clone_object.source_version_id
            )
            if not source_version:
                raise ServiceException(message='源版本不存在')
            
            # 检查新版本号是否唯一
            is_unique = await ProjectVersionDao.check_version_number_unique(
                query_db, source_version.project_id, clone_object.version_number
            )
            if not is_unique:
                raise ServiceException(message=f'版本号 {clone_object.version_number} 已存在')
            
            # 创建新版本
            new_version = ProjectVersionModel(
                project_id=source_version.project_id,
                version_number=clone_object.version_number,
                version_name=clone_object.version_name,
                description=clone_object.description or source_version.description,
                status='1',
                is_locked='0',
                create_by=clone_object.create_by,
                create_time=clone_object.create_time
            )
            new_version_do = await ProjectVersionDao.add_project_version_dao(query_db, new_version)

            # 克隆拓扑数据（如果源版本存在拓扑）
            source_topology = await ProjectTopologyDao.get_topology_by_project_and_version(
                query_db, source_version.project_id, source_version.version_id
            )
            if source_topology:
                topology_model = ProjectTopologyModel(
                    project_id=source_version.project_id,
                    version_id=new_version_do.version_id,
                    topology_data=source_topology.topology_data,
                    create_by=clone_object.create_by,
                    create_time=clone_object.create_time,
                    update_by=clone_object.create_by,
                    update_time=clone_object.create_time
                )
                await ProjectTopologyDao.save_project_topology_dao(query_db, topology_model)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='克隆成功')
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def lock_project_version_services(cls, query_db: AsyncSession, lock_object: LockProjectVersionModel):
        """
        固化/解除固化版本信息service

        :param query_db: orm对象
        :param lock_object: 固化对象
        :return: 固化校验结果
        """
        try:
            # 检查版本是否存在
            version = await ProjectVersionDao.get_project_version_detail_by_id(query_db, lock_object.version_id)
            if not version:
                raise ServiceException(message='版本不存在')
            
            await ProjectVersionDao.lock_project_version_dao(query_db, lock_object)
            await query_db.commit()
            
            message = '固化成功' if lock_object.is_locked == '1' else '解除固化成功'
            return CrudResponseModel(is_success=True, message=message)
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def unlock_project_versions_by_project_services(
        cls, query_db: AsyncSession, project_id: int, operator: str | None = None
    ):
        """
        批量解除指定项目下的固化版本
        """
        if not project_id:
            raise ServiceException(message='工程ID不能为空')

        try:
            locked_map = await ProjectVersionDao.get_locked_versions_by_project(query_db, [project_id])
            locked_versions = locked_map.get(project_id, [])
            if not locked_versions:
                raise ServiceException(message='当前工程不存在需要解除固化的版本')

            await ProjectVersionDao.unlock_project_versions_by_project(query_db, project_id, operator)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='批量解除固化成功')
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise e
