from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.project_version_do import SysProjectVersion
from module_admin.entity.vo.project_version_vo import (
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    DeleteProjectVersionModel,
    CloneProjectVersionModel,
    LockProjectVersionModel
)
from utils.page_util import PageUtil


class ProjectVersionDao:
    """
    项目版本管理模块数据库操作层
    """

    @classmethod
    async def get_project_version_detail_by_id(cls, db: AsyncSession, version_id: int):
        """
        根据版本ID获取版本详细信息

        :param db: orm对象
        :param version_id: 版本ID
        :return: 版本信息对象
        """
        version_info = (
            await db.execute(
                select(SysProjectVersion).where(
                    SysProjectVersion.version_id == version_id,
                    SysProjectVersion.del_flag == '0'
                )
            )
        ).scalars().first()

        return version_info

    @classmethod
    async def get_project_version_list(
        cls, db: AsyncSession, query_object: ProjectVersionPageQueryModel, is_page: bool = False
    ):
        """
        根据查询参数获取版本列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 版本列表信息对象
        """
        query = select(SysProjectVersion).where(
            SysProjectVersion.del_flag == '0'
        )
        
        # 按项目ID筛选
        if query_object.project_id:
            query = query.where(SysProjectVersion.project_id == query_object.project_id)
        
        # 按版本名称筛选
        if query_object.version_name:
            query = query.where(
                SysProjectVersion.version_name.like(f'%{query_object.version_name}%')
            )
        
        # 按版本号筛选
        if query_object.version_number:
            query = query.where(
                SysProjectVersion.version_number.like(f'%{query_object.version_number}%')
            )
        
        # 按时间范围筛选
        if query_object.begin_time and query_object.end_time:
            query = query.where(
                SysProjectVersion.create_time.between(query_object.begin_time, query_object.end_time)
            )
        
        query = query.order_by(desc(SysProjectVersion.create_time))
        
        if is_page:
            return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, True)
        else:
            version_list = (await db.execute(query)).scalars().all()
            return version_list

    @classmethod
    async def add_project_version_dao(cls, db: AsyncSession, version: ProjectVersionModel):
        """
        新增版本数据库操作

        :param db: orm对象
        :param version: 版本对象
        :return: 新增的版本对象
        """
        db_version = SysProjectVersion(**version.model_dump(exclude_unset=True))
        db.add(db_version)
        await db.flush()
        return db_version

    @classmethod
    async def edit_project_version_dao(cls, db: AsyncSession, version: ProjectVersionModel):
        """
        编辑版本数据库操作

        :param db: orm对象
        :param version: 需要更新的版本对象
        :return: None
        """
        await db.execute(
            update(SysProjectVersion)
            .where(SysProjectVersion.version_id == version.version_id)
            .values(**version.model_dump(exclude_unset=True, exclude={'version_id'}))
        )

    @classmethod
    async def delete_project_version_dao(cls, db: AsyncSession, version: DeleteProjectVersionModel):
        """
        删除版本数据库操作

        :param db: orm对象
        :param version: 删除版本对象
        :return: None
        """
        version_id_list = version.version_ids.split(',')
        await db.execute(
            update(SysProjectVersion)
            .where(SysProjectVersion.version_id.in_(version_id_list))
            .values(
                del_flag='2',
                update_by=version.update_by,
                update_time=version.update_time
            )
        )

    @classmethod
    async def check_version_number_unique(
        cls, db: AsyncSession, project_id: int, version_number: str, version_id: int = None
    ):
        """
        检查版本号是否唯一

        :param db: orm对象
        :param project_id: 项目ID
        :param version_number: 版本号
        :param version_id: 版本ID（编辑时传入）
        :return: 是否唯一
        """
        query = select(SysProjectVersion).where(
            SysProjectVersion.project_id == project_id,
            SysProjectVersion.version_number == version_number,
            SysProjectVersion.del_flag == '0'
        )
        
        if version_id:
            query = query.where(SysProjectVersion.version_id != version_id)
        
        result = await db.execute(query)
        existing_version = result.scalars().first()
        
        return existing_version is None

    @classmethod
    async def lock_project_version_dao(cls, db: AsyncSession, lock_model: LockProjectVersionModel):
        """
        固化/解除固化版本数据库操作

        :param db: orm对象
        :param lock_model: 固化模型
        :return: None
        """
        update_data = {
            'is_locked': lock_model.is_locked,
            'update_by': lock_model.update_by,
            'update_time': lock_model.update_time
        }
        
        if lock_model.is_locked == '1':
            update_data['locked_by'] = lock_model.locked_by
            update_data['locked_time'] = lock_model.locked_time
        else:
            update_data['locked_by'] = None
            update_data['locked_time'] = None
        
        await db.execute(
            update(SysProjectVersion)
            .where(SysProjectVersion.version_id == lock_model.version_id)
            .values(**update_data)
        )
