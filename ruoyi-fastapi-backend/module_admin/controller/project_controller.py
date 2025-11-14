from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.project_vo import DeleteProjectModel, ProjectModel, ProjectPageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.project_service import ProjectService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


projectController = APIRouter(prefix='/project', dependencies=[Depends(LoginService.get_current_user)])


@projectController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:list'))]
)
async def get_system_project_list(
    request: Request,
    project_page_query: ProjectPageQueryModel = Depends(ProjectPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取工程列表
    """
    project_query_result = await ProjectService.get_project_list_services(
        query_db, project_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=project_query_result)


@projectController.post('', dependencies=[Depends(CheckUserInterfaceAuth('project:project:add'))])
@Log(title='工程管理', business_type=BusinessType.INSERT)
async def add_system_project(
    request: Request,
    add_project: ProjectModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    新增工程
    """
    add_project.create_by = current_user.user.user_name
    add_project.create_time = datetime.now()
    add_project.update_by = current_user.user.user_name
    add_project.update_time = datetime.now()
    add_project_result = await ProjectService.add_project_services(query_db, add_project)
    logger.info(add_project_result.message)

    return ResponseUtil.success(msg=add_project_result.message)


@projectController.put('', dependencies=[Depends(CheckUserInterfaceAuth('project:project:edit'))])
@Log(title='工程管理', business_type=BusinessType.UPDATE)
async def edit_system_project(
    request: Request,
    edit_project: ProjectModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑工程
    """
    edit_project.update_by = current_user.user.user_name
    edit_project.update_time = datetime.now()
    edit_project_result = await ProjectService.edit_project_services(query_db, edit_project)
    logger.info(edit_project_result.message)

    return ResponseUtil.success(msg=edit_project_result.message)


@projectController.delete('/{project_ids}', dependencies=[Depends(CheckUserInterfaceAuth('project:project:remove'))])
@Log(title='工程管理', business_type=BusinessType.DELETE)
async def delete_system_project(
    request: Request,
    project_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除工程
    """
    delete_project = DeleteProjectModel(projectIds=project_ids)
    delete_project.update_by = current_user.user.user_name
    delete_project.update_time = datetime.now()
    delete_project_result = await ProjectService.delete_project_services(query_db, delete_project)
    logger.info(delete_project_result.message)

    return ResponseUtil.success(msg=delete_project_result.message)


@projectController.get(
    '/{project_id}',
    response_model=ProjectModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))]
)
async def query_detail_system_project(
    request: Request,
    project_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取工程详情
    """
    detail_project_result = await ProjectService.project_detail_services(query_db, project_id)
    logger.info(f'获取project_id为{project_id}的信息成功')

    return ResponseUtil.success(data=detail_project_result)
