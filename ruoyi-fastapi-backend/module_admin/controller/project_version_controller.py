from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.project_version_vo import (
    DeleteProjectVersionModel,
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    CloneProjectVersionModel,
    LockProjectVersionModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.project_version_service import ProjectVersionService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


projectVersionController = APIRouter(
    prefix='/project/version',
    dependencies=[Depends(LoginService.get_current_user)]
)


@projectVersionController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:list'))]
)
async def get_project_version_list(
    request: Request,
    version_page_query: ProjectVersionPageQueryModel = Depends(ProjectVersionPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取项目版本列表
    """
    version_query_result = await ProjectVersionService.get_project_version_list_services(
        query_db, version_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=version_query_result)


@projectVersionController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:add'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.INSERT)
async def add_project_version(
    request: Request,
    add_version: ProjectVersionModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    新增项目版本
    """
    add_version.create_by = current_user.user.user_name
    add_version.create_time = datetime.now()
    add_version.update_by = current_user.user.user_name
    add_version.update_time = datetime.now()
    add_version_result = await ProjectVersionService.add_project_version_services(query_db, add_version)
    logger.info(add_version_result.message)

    return ResponseUtil.success(msg=add_version_result.message)


@projectVersionController.put(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def edit_project_version(
    request: Request,
    edit_version: ProjectVersionModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑项目版本
    """
    edit_version.update_by = current_user.user.user_name
    edit_version.update_time = datetime.now()
    edit_version_result = await ProjectVersionService.edit_project_version_services(query_db, edit_version)
    logger.info(edit_version_result.message)

    return ResponseUtil.success(msg=edit_version_result.message)


@projectVersionController.delete(
    '/{version_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:remove'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.DELETE)
async def delete_project_version(
    request: Request,
    version_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除项目版本
    """
    delete_version = DeleteProjectVersionModel(versionIds=version_ids)
    delete_version.update_by = current_user.user.user_name
    delete_version.update_time = datetime.now()
    delete_version_result = await ProjectVersionService.delete_project_version_services(query_db, delete_version)
    logger.info(delete_version_result.message)

    return ResponseUtil.success(msg=delete_version_result.message)


@projectVersionController.get(
    '/{version_id}',
    response_model=ProjectVersionModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:query'))]
)
async def query_detail_project_version(
    request: Request,
    version_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取项目版本详情
    """
    detail_version_result = await ProjectVersionService.project_version_detail_services(query_db, version_id)
    logger.info(f'获取version_id为{version_id}的信息成功')

    return ResponseUtil.success(data=detail_version_result)


@projectVersionController.post(
    '/clone',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:add'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.INSERT)
async def clone_project_version(
    request: Request,
    clone_version: CloneProjectVersionModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    克隆项目版本
    """
    clone_version.create_by = current_user.user.user_name
    clone_version.create_time = datetime.now()
    clone_version_result = await ProjectVersionService.clone_project_version_services(query_db, clone_version)
    logger.info(clone_version_result.message)

    return ResponseUtil.success(msg=clone_version_result.message)


@projectVersionController.put(
    '/lock',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def lock_project_version(
    request: Request,
    lock_version: LockProjectVersionModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    固化/解除固化项目版本
    """
    lock_version.update_by = current_user.user.user_name
    lock_version.update_time = datetime.now()
    
    if lock_version.is_locked == '1':
        lock_version.locked_by = current_user.user.user_name
        lock_version.locked_time = datetime.now()
    
    lock_version_result = await ProjectVersionService.lock_project_version_services(query_db, lock_version)
    logger.info(lock_version_result.message)

    return ResponseUtil.success(msg=lock_version_result.message)


@projectVersionController.put(
    '/unlock/project/{project_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def unlock_project_versions_by_project(
    request: Request,
    project_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    批量解除指定工程下的固化版本
    """
    unlock_result = await ProjectVersionService.unlock_project_versions_by_project_services(
        query_db, project_id, current_user.user.user_name
    )
    logger.info(unlock_result.message)
    return ResponseUtil.success(msg=unlock_result.message)
