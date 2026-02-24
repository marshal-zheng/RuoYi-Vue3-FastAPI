from fastapi import APIRouter, Body, Depends, File, Form, Request, UploadFile

from container.dependencies import service_provider
from config.enums import BusinessType
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.application.services.login_service import LoginService
from module_admin.service.protocol_service import ProtocolService
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.page_util import PageResponseModel
from utils.common_util import bytes2file_response
from urllib.parse import quote


protocolController = APIRouter(prefix='/system/protocol', tags=['协议管理'])


@protocolController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:list'))]
)
async def get_protocol_list(
    request: Request,
    protocol_page_query: ProtocolPageQueryModel = Depends(ProtocolPageQueryModel.as_query),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
):
    """
    获取协议列表
    """
    # 获取分页数据
    protocol_page_query_result = await protocol_service.get_protocol_list(protocol_page_query, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=protocol_page_query_result)


@protocolController.post(
    '',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:add')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.INSERT, log_type='operation')
async def add_protocol(
    request: Request,
    add_protocol: ProtocolModel,
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    新增协议
    """
    add_protocol_result = await protocol_service.add_protocol(
        add_protocol,
        operator=current_user.user.user_name,
    )
    logger.info(add_protocol_result.message)
    return ResponseUtil.success(message=add_protocol_result.message)


@protocolController.put(
    '',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:edit')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.UPDATE, log_type='operation')
async def edit_protocol(
    request: Request,
    edit_protocol: ProtocolModel,
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    编辑协议
    """
    edit_protocol_result = await protocol_service.edit_protocol(
        edit_protocol,
        operator=current_user.user.user_name,
    )
    logger.info(edit_protocol_result.message)
    return ResponseUtil.success(message=edit_protocol_result.message)


@protocolController.delete(
    '/{protocol_ids}',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:remove')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.DELETE, log_type='operation')
async def delete_protocol(
    request: Request,
    protocol_ids: str,
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    删除协议
    """
    delete_protocol = DeleteProtocolModel(protocolIds=protocol_ids, updateBy=current_user.user.user_name)
    delete_protocol_result = await protocol_service.delete_protocol(
        delete_protocol,
        operator=current_user.user.user_name,
    )
    logger.info(delete_protocol_result.message)
    return ResponseUtil.success(message=delete_protocol_result.message)


@protocolController.post(
    '/deleteBatch',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:remove')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.DELETE, log_type='operation')
async def delete_protocol_batch(
    request: Request,
    protocolIds: list[int] = Body(..., embed=True),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    批量删除协议（使用 BatchActionExecutor 收敛结果）
    """
    summary = await protocol_service.delete_protocol_batch(
        protocol_ids=protocolIds,
        operator=current_user.user.user_name,
    )
    return ResponseUtil.success(data={'summary': summary}, message='批量删除完成')


@protocolController.get(
    '/importTemplate',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:edit'))]
)
async def download_protocol_import_template(
    request: Request,
    protocolType: str = None,
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
):
    """
    下载协议导入模板
    """
    template_bytes = await protocol_service.get_protocol_import_template_services(protocolType)
    suffix = f'_{protocolType.upper()}' if protocolType else ''
    filename = quote(f'协议导入模板{suffix}.xlsx')
    headers = {
        'Content-Disposition': f"attachment; filename*=UTF-8''{filename}",
        'download-filename': filename
    }
    return ResponseUtil.streaming(
        data=bytes2file_response(template_bytes),
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@protocolController.post(
    '/importPreview',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:edit'))]
)
async def protocol_import_preview(
    request: Request,
    file: UploadFile = File(...),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
):
    """
    解析协议导入文件，返回预览数据
    """
    preview_result = await protocol_service.protocol_import_preview_services(file)
    logger.info('协议导入文件解析成功')
    return ResponseUtil.success(data=preview_result)


@protocolController.post(
    '/export',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:export'))]
)
@Log(title='协议管理', business_type=BusinessType.EXPORT, log_type='operation')
async def export_protocol_config(
    request: Request,
    protocolId: int = Form(...),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
):
    """
    导出协议配置
    """
    export_result = await protocol_service.export_protocol_config_services(protocolId)
    protocol_name = export_result.get('protocol_name', '协议配置')
    content = export_result.get('content', b'')
    filename = quote(f'{protocol_name}_配置.xlsx')
    headers = {
        'Content-Disposition': f"attachment; filename*=UTF-8''{filename}",
        'download-filename': filename
    }
    return ResponseUtil.streaming(
        data=bytes2file_response(content),
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@protocolController.post(
    '/import',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:add'))]
)
@Log(title='协议管理', business_type=BusinessType.IMPORT, log_type='operation')
async def import_protocol(
    request: Request,
    file: UploadFile = File(...),
    protocolName: str = Form(default=None),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    导入协议配置
    """
    import_result = await protocol_service.import_protocol_services(file, protocolName, current_user.user.user_name)
    logger.info('协议导入成功')
    return ResponseUtil.success(data=import_result.result, message=import_result.message)


@protocolController.post(
    '/importBatch',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:add'))]
)
@Log(title='协议管理', business_type=BusinessType.IMPORT, log_type='operation')
async def import_protocol_batch(
    request: Request,
    files: list[UploadFile] = File(...),
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    批量导入协议配置
    """
    import_result = await protocol_service.import_protocol_batch_services(
        files=files, operator=current_user.user.user_name
    )
    msg = '批量导入成功' if import_result.failed_count == 0 else '部分导入成功'
    return ResponseUtil.success(data=import_result.model_dump(), message=msg)


@protocolController.get(
    '/{protocol_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:query'))]
)
async def query_protocol_detail(
    request: Request,
    protocol_id: int,
    protocol_service: ProtocolService = Depends(service_provider('protocol_service')),
):
    """
    获取协议详情
    """
    protocol_detail_result = await protocol_service.get_protocol_detail(protocol_id)
    logger.info('获取成功')
    return ResponseUtil.success(data=protocol_detail_result)
