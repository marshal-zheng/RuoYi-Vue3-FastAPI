from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_admin.dao.project_dao import ProjectDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.project_vo import ProjectModel, ProjectPageQueryModel, DeleteProjectModel
from utils.common_util import CamelCaseUtil
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
            
            await ProjectDao.add_project_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
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
        from datetime import datetime
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
        if page_object.project_ids:
            try:
                await ProjectDao.delete_project_dao(query_db, page_object)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入工程id为空')

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