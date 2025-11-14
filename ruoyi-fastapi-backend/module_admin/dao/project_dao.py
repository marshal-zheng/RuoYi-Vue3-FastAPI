from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.project_do import SysProject
from module_admin.entity.vo.project_vo import ProjectModel, ProjectPageQueryModel, DeleteProjectModel
from utils.page_util import PageUtil


class ProjectDao:
    """
    工程管理模块数据库操作层
    """

    @classmethod
    async def get_project_detail_by_id(cls, db: AsyncSession, project_id: int):
        """
        根据工程id获取工程详细信息

        :param db: orm对象
        :param project_id: 工程id
        :return: 工程信息对象
        """
        project_info = (
            await db.execute(
                select(SysProject).where(
                    SysProject.project_id == project_id,
                    SysProject.del_flag == '0'
                )
            )
        ).scalars().first()

        return project_info

    @classmethod
    async def get_project_list(cls, db: AsyncSession, query_object: ProjectPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取工程列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 工程列表信息对象
        """
        query = select(SysProject).where(
            SysProject.del_flag == '0'
        ).order_by(desc(SysProject.create_time))
        
        if query_object.begin_time and query_object.end_time:
            query = query.where(
                SysProject.create_time.between(query_object.begin_time, query_object.end_time)
            )
        
        if is_page:
            return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, True)
        else:
            project_list = (await db.execute(query)).scalars().all()
            return project_list

    @classmethod
    async def add_project_dao(cls, db: AsyncSession, project: ProjectModel):
        """
        新增工程数据库操作

        :param db: orm对象
        :param project: 工程对象
        :return: None
        """
        db_project = SysProject(**project.model_dump(exclude_unset=True))
        db.add(db_project)
        await db.flush()
        return db_project

    @classmethod
    async def edit_project_dao(cls, db: AsyncSession, project: ProjectModel):
        """
        编辑工程数据库操作

        :param db: orm对象
        :param project: 需要更新的工程对象
        :return: None
        """
        await db.execute(
            update(SysProject)
            .where(SysProject.project_id == project.project_id)
            .values(**project.model_dump(exclude_unset=True, exclude={'project_id'}))
        )

    @classmethod
    async def delete_project_dao(cls, db: AsyncSession, project: DeleteProjectModel):
        """
        删除工程数据库操作

        :param db: orm对象
        :param project: 删除工程对象
        :return: None
        """
        project_id_list = project.project_ids.split(',')
        await db.execute(
            update(SysProject)
            .where(SysProject.project_id.in_(project_id_list))
            .values(
                del_flag='2',
                update_by=project.update_by,
                update_time=project.update_time
            )
        )