from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from urllib.parse import quote
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.project_version_vo import (
    DeleteProjectVersionModel,
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    CloneProjectVersionModel,
    LockProjectVersionModel,
    ExportProjectVersionModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.project_version_service import ProjectVersionService
from module_admin.service.project_topology_service import ProjectTopologyService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.word_util import export_version_to_word, export_version_to_excel, export_version_to_xml


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

    return ResponseUtil.success(message=add_version_result.message)


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

    return ResponseUtil.success(message=edit_version_result.message)


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

    return ResponseUtil.success(message=delete_version_result.message)


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

    return ResponseUtil.success(message=clone_version_result.message)


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

    return ResponseUtil.success(message=lock_version_result.message)


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
    return ResponseUtil.success(message=unlock_result.message)


@projectVersionController.post(
    '/export',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:export'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.EXPORT)
async def export_project_version(
    request: Request,
    export_data: ExportProjectVersionModel,
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出项目版本为Word文档
    
    Args:
        export_data: 包含版本ID和可选的拓扑图base64图片数据
    """
    version_id = export_data.version_id
    image_base64 = export_data.image_base64
    
    # 获取版本详情
    version_detail = await ProjectVersionService.project_version_detail_services(query_db, version_id)
    
    # 获取版本对应的拓扑数据
    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''
    topology_data = None

    if project_id:
        topo_result = await ProjectTopologyService.get_project_topology_services(
            query_db, project_id, version_id
        )
        if topo_result:
            topology_data = topo_result.get('topology_data') or topo_result.get('topologyData')
    
    # 生成Word文档（传入图片base64数据）
    word_content = export_version_to_word(topology_data, image_base64)
    
    # 设置文件名
    file_name = f"{version_name}_接口控制文件.doc" if version_name else "接口控制文件.doc"
    
    # 对文件名进行URL编码
    encoded_filename = quote(file_name)
    
    logger.info(f'导出版本 {version_id} 成功')
    
    return StreamingResponse(
        BytesIO(word_content),
        media_type='application/msword',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@projectVersionController.get(
    '/export-excel/{version_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:export'))]
)
@Log(title='工程管理-版本Excel', business_type=BusinessType.EXPORT)
async def export_project_version_excel(
    request: Request,
    version_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出项目版本附录Excel（压缩包，每个协议一张表）
    """
    # 获取版本详情
    version_detail = await ProjectVersionService.project_version_detail_services(query_db, version_id)

    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''

    topology_data = None
    if project_id:
        topo_result = await ProjectTopologyService.get_project_topology_services(
            query_db, project_id, version_id
        )
        if topo_result:
            topology_data = topo_result.get('topology_data') or topo_result.get('topologyData')

    zip_content = export_version_to_excel(topology_data)

    file_name = f"{version_name}_附录表.zip" if version_name else "附录表.zip"
    encoded_filename = quote(file_name)

    logger.info(f'导出版本 {version_id} Excel 成功')

    return StreamingResponse(
        BytesIO(zip_content),
        media_type='application/zip',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@projectVersionController.get(
    '/export-xml/{version_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:export'))]
)
@Log(title='工程管理-版本XML', business_type=BusinessType.EXPORT)
async def export_project_version_xml(
    request: Request,
    version_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """
    导出项目版本为 XML 接口控制文件
    """
    version_detail = await ProjectVersionService.project_version_detail_services(query_db, version_id)

    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''

    topology_data = None
    if project_id:
        topo_result = await ProjectTopologyService.get_project_topology_services(
            query_db, project_id, version_id
        )
        if topo_result:
            topology_data = topo_result.get('topology_data') or topo_result.get('topologyData')

    xml_content = export_version_to_xml(version_detail, topology_data)

    file_name = f"{version_name}_接口控制文件.xml" if version_name else "接口控制文件.xml"
    encoded_filename = quote(file_name)

    logger.info(f'导出版本 {version_id} XML 成功')

    return StreamingResponse(
        BytesIO(xml_content),
        media_type='application/xml',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
