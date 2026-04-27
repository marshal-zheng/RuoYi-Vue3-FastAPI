from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from io import BytesIO
from urllib.parse import quote
from config.enums import BusinessType
from container.dependencies import service_provider
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.do.enums import LockStatusEnum
from module_admin.entity.vo.project_version_vo import (
    DeleteProjectVersionModel,
    ProjectVersionModel,
    ProjectVersionPageQueryModel,
    CloneProjectVersionModel,
    LockProjectVersionModel,
    ExportProjectVersionModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.project.application.services.project_version_service import ProjectVersionService
from modules.project.application.services.project_topology_service import ProjectTopologyService
from modules.identity.ports import get_current_user
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.word_util import export_version_to_word, export_version_to_excel, export_version_to_xml


projectVersionController = APIRouter(
    prefix='/project/version',
    dependencies=[Depends(get_current_user)]
)


async def _load_project_version_detail(version_id: int, project_version_service: ProjectVersionService):
    detail_version_result = await project_version_service.project_version_detail_services(version_id)
    return detail_version_result or {}


@projectVersionController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:list'))]
)
async def get_project_version_list(
    request: Request,
    version_page_query: ProjectVersionPageQueryModel = Depends(ProjectVersionPageQueryModel.as_query),
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
):
    """
    获取项目版本列表
    """
    version_query_result = await project_version_service.get_project_version_list_services(
        version_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.ok_resource(version_query_result)


@projectVersionController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:add'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.INSERT)
async def add_project_version(
    request: Request,
    add_version: ProjectVersionModel,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    新增项目版本
    """
    add_version.create_by = current_user.user.user_name
    add_version.create_time = datetime.now()
    add_version.update_by = current_user.user.user_name
    add_version.update_time = datetime.now()
    add_version_result = await project_version_service.add_project_version_services(add_version)
    logger.info(add_version_result.message)

    version_id = require_int_value(
        add_version_result.result,
        'versionId',
        'version_id',
        contract_name='project-version.create',
    )
    resource = await _load_project_version_detail(version_id, project_version_service)
    location = ResponseUtil.build_absolute_location(request, f'/project/version/{version_id}')
    return ResponseUtil.created_resource(resource, location=location)


@projectVersionController.put(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def edit_project_version(
    request: Request,
    edit_version: ProjectVersionModel,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    编辑项目版本
    """
    edit_version.update_by = current_user.user.user_name
    edit_version.update_time = datetime.now()
    edit_version_result = await project_version_service.edit_project_version_services(edit_version)
    logger.info(edit_version_result.message)

    resource = await _load_project_version_detail(edit_version.version_id, project_version_service)
    return ResponseUtil.ok_resource(resource)


@projectVersionController.delete(
    '/{version_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:remove'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.DELETE)
async def delete_project_version(
    request: Request,
    version_ids: str,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    删除项目版本
    """
    delete_version = DeleteProjectVersionModel(versionIds=version_ids)
    delete_version.update_by = current_user.user.user_name
    delete_version.update_time = datetime.now()
    delete_version_result = await project_version_service.delete_project_version_services(delete_version)
    logger.info(delete_version_result.message)

    return ResponseUtil.no_content()


@projectVersionController.get(
    '/{version_id}',
    response_model=ProjectVersionModel,
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:query'))]
)
async def query_detail_project_version(
    request: Request,
    version_id: int,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
):
    """
    获取项目版本详情
    """
    detail_version_result = await project_version_service.project_version_detail_services(version_id)
    logger.info(f'获取version_id为{version_id}的信息成功')

    return ResponseUtil.ok_resource(detail_version_result)


@projectVersionController.post(
    '/clone',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:add'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.INSERT)
async def clone_project_version(
    request: Request,
    clone_version: CloneProjectVersionModel,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    克隆项目版本
    """
    clone_version.create_by = current_user.user.user_name
    clone_version.create_time = datetime.now()
    clone_version_result = await project_version_service.clone_project_version_services(clone_version)
    logger.info(clone_version_result.message)

    version_id = require_int_value(
        clone_version_result.result,
        'versionId',
        'version_id',
        contract_name='project-version.clone',
    )
    resource = await _load_project_version_detail(version_id, project_version_service)
    location = ResponseUtil.build_absolute_location(request, f'/project/version/{version_id}')
    return ResponseUtil.created_resource(resource, location=location)


@projectVersionController.put(
    '/lock',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def lock_project_version(
    request: Request,
    lock_version: LockProjectVersionModel,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    固化/解除固化项目版本
    """
    lock_version.update_by = current_user.user.user_name
    lock_version.update_time = datetime.now()
    
    if lock_version.is_locked == LockStatusEnum.LOCKED.value:
        lock_version.locked_by = current_user.user.user_name
        lock_version.locked_time = datetime.now()
    
    lock_version_result = await project_version_service.lock_project_version_services(lock_version)
    logger.info(lock_version_result.message)

    resource = await _load_project_version_detail(lock_version.version_id, project_version_service)
    return ResponseUtil.ok_resource(resource)


@projectVersionController.put(
    '/unlock/project/{project_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:edit'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.UPDATE)
async def unlock_project_versions_by_project(
    request: Request,
    project_id: int,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    """
    批量解除指定工程下的固化版本
    """
    unlock_result = await project_version_service.unlock_project_versions_by_project_services(
        project_id, current_user.user.user_name
    )
    logger.info(unlock_result.message)
    return ResponseUtil.ok_resource(
        unlock_result.result
        or {
            'projectId': project_id,
            'status': 'unlocked',
            'unlockedCount': None,
            'unlockedVersionIds': [],
        }
    )


@projectVersionController.post(
    '/export',
    dependencies=[Depends(CheckUserInterfaceAuth('project:version:export'))]
)
@Log(title='工程管理-版本', business_type=BusinessType.EXPORT)
async def export_project_version(
    request: Request,
    export_data: ExportProjectVersionModel,
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    project_topology_service: ProjectTopologyService = Depends(service_provider('project_topology_service')),
):
    """
    导出项目版本为Word文档
    
    Args:
        export_data: 包含版本ID和可选的拓扑图base64图片数据
    """
    version_id = export_data.version_id
    image_base64 = export_data.image_base64
    
    # 获取版本详情
    version_detail = await project_version_service.project_version_detail_services(version_id)
    
    # 获取版本对应的拓扑数据
    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''
    topology_data = None

    if project_id:
        topo_result = await project_topology_service.get_project_topology(project_id, version_id)
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
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    project_topology_service: ProjectTopologyService = Depends(service_provider('project_topology_service')),
):
    """
    导出项目版本附录Excel（压缩包，每个协议一张表）
    """
    # 获取版本详情
    version_detail = await project_version_service.project_version_detail_services(version_id)

    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''

    topology_data = None
    if project_id:
        topo_result = await project_topology_service.get_project_topology(project_id, version_id)
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
    project_version_service: ProjectVersionService = Depends(service_provider('project_version_service')),
    project_topology_service: ProjectTopologyService = Depends(service_provider('project_topology_service')),
):
    """
    导出项目版本为 XML 接口控制文件
    """
    version_detail = await project_version_service.project_version_detail_services(version_id)

    project_id = None
    version_name = ''
    if version_detail:
        project_id = version_detail.get('project_id') or version_detail.get('projectId')
        version_name = version_detail.get('version_name') or version_detail.get('versionName') or ''

    topology_data = None
    if project_id:
        topo_result = await project_topology_service.get_project_topology(project_id, version_id)
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
