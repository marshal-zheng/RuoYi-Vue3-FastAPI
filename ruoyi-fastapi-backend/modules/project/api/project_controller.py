from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from utils.validation_util import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from module_admin.entity.vo.project_vo import (
    BatchProjectIdsModel,
    DeleteProjectModel,
    ProjectImportDataModel,
    ProjectModel,
    ProjectPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.project.application.services.project_service import ProjectService
from modules.project.application.services.project_topology_service import ProjectTopologyService, get_project_topology_service
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from urllib.parse import quote
import re


projectController = APIRouter(prefix='/project', dependencies=[Depends(get_current_user)])


@projectController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:list'))]
)
async def get_system_project_list(
    request: Request,
    project_page_query: ProjectPageQueryModel = Depends(ProjectPageQueryModel.as_query),
    project_service: ProjectService = Depends(service_provider('project_service')),
):
    """
    获取工程列表
    """
    project_query_result = await project_service.get_project_list(project_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=project_query_result)


@projectController.post('', dependencies=[Depends(CheckUserInterfaceAuth('project:project:add'))])
@Log(title='工程管理-工程', business_type=BusinessType.INSERT)
async def add_system_project(
    request: Request,
    add_project: ProjectModel,
    project_service: ProjectService = Depends(service_provider('project_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    新增工程
    """
    add_project_result = await project_service.add_project(
        add_project,
        operator=current_user.user.user_name,
    )
    logger.info(add_project_result.message)

    return ResponseUtil.success(message=add_project_result.message, data=add_project_result.result)


@projectController.put('', dependencies=[Depends(CheckUserInterfaceAuth('project:project:edit'))])
@Log(title='工程管理-工程', business_type=BusinessType.UPDATE)
async def edit_system_project(
    request: Request,
    edit_project: ProjectModel,
    project_service: ProjectService = Depends(service_provider('project_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    编辑工程
    """
    edit_project_result = await project_service.edit_project(
        edit_project,
        operator=current_user.user.user_name,
    )
    logger.info(edit_project_result.message)

    return ResponseUtil.success(message=edit_project_result.message)


@projectController.delete('/{project_ids}', dependencies=[Depends(CheckUserInterfaceAuth('project:project:remove'))])
@Log(title='工程管理-工程', business_type=BusinessType.DELETE)
async def delete_system_project(
    request: Request,
    project_ids: str,
    project_service: ProjectService = Depends(service_provider('project_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    删除工程
    """
    delete_project = DeleteProjectModel(projectIds=project_ids)
    delete_project_result = await project_service.delete_project(
        delete_project,
        operator=current_user.user.user_name,
    )
    logger.info(delete_project_result.message)

    return ResponseUtil.success(message=delete_project_result.message)


@projectController.get(
    '/{project_id}',
    response_model=ProjectModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))]
)
async def query_detail_system_project(
    request: Request,
    project_id: int,
    project_service: ProjectService = Depends(service_provider('project_service')),
):
    """
    获取工程详情
    """
    detail_project_result = await project_service.get_project_detail(project_id)
    logger.info(f'获取project_id为{project_id}的信息成功')

    return ResponseUtil.success(data=detail_project_result)


@projectController.post(
    '/topology/save',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:edit'))],
)
@Log(title='工程管理-拓扑', business_type=BusinessType.UPDATE)
@ValidateFields(validate_model='project_topology')
async def save_project_topology(
    request: Request,
    topology: ProjectTopologyModel,
    topology_service: ProjectTopologyService = Depends(get_project_topology_service),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    保存工程拓扑数据
    """
    save_result = await topology_service.save_project_topology(
        topology,
        operator=current_user.user.user_name,
    )
    logger.info(save_result.message)
    return ResponseUtil.success(message=save_result.message)


@projectController.get(
    '/topology/{project_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))],
)
async def get_project_topology(
    request: Request,
    project_id: int,
    version_id: Optional[int] = Query(default=None, description='版本ID'),
    topology_service: ProjectTopologyService = Depends(get_project_topology_service),
):
    """
    获取工程拓扑数据
    """
    topo_result = await topology_service.get_project_topology(project_id, version_id)
    logger.info(f'获取project_id为{project_id}的拓扑数据成功')

    return ResponseUtil.success(data=topo_result)


@projectController.get(
    '/export/{project_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))],
)
@Log(title='工程管理-导出', business_type=BusinessType.EXPORT)
async def export_project(
    request: Request,
    project_id: int,
    project_service: ProjectService = Depends(service_provider('project_service')),
):
    """
    导出工程数据（zip包）
    """
    zip_buffer, filename = await project_service.export_project_zip(project_id)
    logger.info(f'导出project_id为{project_id}的工程数据成功')
    encoded_filename = quote(filename)
    # 提供 ASCII 兜底，避免非拉丁字符导致 Header 编码失败
    ascii_fallback = re.sub(r'[^0-9A-Za-z._-]+', '_', filename)
    content_disposition = f"attachment; filename={ascii_fallback}; filename*=UTF-8''{encoded_filename}"
    return StreamingResponse(
        content=zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': content_disposition},
    )


@projectController.post(
    '/export',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))],
)
@Log(title='工程管理-导出', business_type=BusinessType.EXPORT)
async def export_project_placeholder(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
):
    """
    兼容导出入口（需传入 project_id）
    """
    from exceptions.exception import ValidationException
    raise ValidationException(
        user_message='请在路径中提供project_id',
        developer_message='Project ID is required in the path',
        field='project_id'
    )


@projectController.post(
    '/export/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:query'))],
)
@Log(title='工程管理-批量导出', business_type=BusinessType.EXPORT)
async def export_projects_batch(
    request: Request,
    project_ids_body: BatchProjectIdsModel,
    project_service: ProjectService = Depends(service_provider('project_service')),
):
    """
    批量导出工程数据（返回zip包）
    """
    zip_buffer, filename = await project_service.export_projects_zip(project_ids_body.project_ids)
    encoded_filename = quote(filename)
    ascii_fallback = re.sub(r'[^0-9A-Za-z._-]+', '_', filename)
    content_disposition = f"attachment; filename={ascii_fallback}; filename*=UTF-8''{encoded_filename}"
    return StreamingResponse(
        content=zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': content_disposition},
    )


@projectController.post(
    '/import',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:add'))],
)
@Log(title='工程管理-导入', business_type=BusinessType.IMPORT)
async def import_project(
    request: Request,
    import_data: ProjectImportDataModel,
    project_service: ProjectService = Depends(service_provider('project_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    导入工程数据
    """
    import_result = await project_service.import_project(import_data, current_user.user.user_name)
    logger.info(import_result.message)

    return ResponseUtil.success(message=import_result.message, data=import_result.result)


@projectController.post(
    '/import/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('project:project:add'))],
)
@Log(title='工程管理-批量导入', business_type=BusinessType.IMPORT)
async def import_projects_batch(
    request: Request,
    file: UploadFile = File(...),
    project_service: ProjectService = Depends(service_provider('project_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    批量导入工程（zip包）
    """
    file_bytes = await file.read()
    import_result = await project_service.import_projects_from_zip(file_bytes, current_user.user.user_name)
    return ResponseUtil.success(message='批量导入完成', data=import_result)
