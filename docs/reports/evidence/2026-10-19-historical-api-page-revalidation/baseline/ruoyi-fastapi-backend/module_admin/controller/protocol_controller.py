from fastapi import APIRouter, Body, Depends, File, Form, Request, UploadFile

from container.dependencies import service_provider
from config.enums import BusinessType
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.application.services.login_service import LoginService
from module_admin.service.protocol_service import ProtocolService
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.page_util import PageResponseModel
from utils.common_util import bytes2file_response
from urllib.parse import quote


protocolController = APIRouter(prefix='/system/protocol', tags=['协议管理'])


async def _load_protocol_detail(protocol_id: int, protocol_service: ProtocolService):
    protocol_detail_result = await protocol_service.get_protocol_detail(protocol_id)
    return protocol_detail_result


def _to_batch_contract(summary: dict) -> tuple[list[dict], dict[str, int]]:
    success_items = summary.get('success', []) or []
    failed_items = summary.get('failed', []) or []
    results = [
        {
            'itemId': item.get('id'),
            'success': True,
            'attempts': item.get('attempts'),
            'data': item.get('data'),
        }
        for item in success_items
    ]
    results.extend(
        [
            {
                'itemId': item.get('id'),
                'success': False,
                'attempts': item.get('attempts'),
                'error': {
                    'title': '操作失败',
                    'detail': item.get('error') or '操作失败',
                },
            }
            for item in failed_items
        ]
    )
    normalized_summary = {
        'total': len(results),
        'succeeded': len(success_items),
        'failed': len(failed_items),
    }
    return results, normalized_summary


def _to_import_batch_contract(import_data: dict | None, *, total: int, succeeded: int, failed: int) -> tuple[list[dict], dict[str, int]]:
    payload = import_data or {}
    success_items = payload.get('success', []) or []
    failed_items = payload.get('failed', []) or []
    results = [
        {
            'itemId': item.get('filename') or item.get('protocolName'),
            'protocolId': item.get('protocolId'),
            'filename': item.get('filename'),
            'protocolName': item.get('protocolName'),
            'protocolType': item.get('protocolType'),
            'success': True,
        }
        for item in success_items
    ]
    results.extend(
        [
            {
                'itemId': item.get('filename'),
                'filename': item.get('filename'),
                'success': False,
                'error': {
                    'title': '导入失败',
                    'detail': item.get('reason') or '导入失败',
                },
            }
            for item in failed_items
        ]
    )
    return results, {
        'total': total,
        'succeeded': succeeded,
        'failed': failed,
    }


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
    return ResponseUtil.ok_resource(protocol_page_query_result)


@protocolController.post(
    '',
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
    protocol_id = require_int_value(
        add_protocol_result.result,
        'protocolId',
        'protocol_id',
        contract_name='protocol.create',
    )
    resource = await _load_protocol_detail(protocol_id, protocol_service)
    location = ResponseUtil.build_absolute_location(request, f'/system/protocol/{protocol_id}')
    return ResponseUtil.created_resource(resource, location=location)


@protocolController.put(
    '',
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
    resource = await _load_protocol_detail(edit_protocol.protocol_id, protocol_service)
    return ResponseUtil.ok_resource(resource)


@protocolController.delete(
    '/{protocol_ids}',
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
    return ResponseUtil.no_content()


@protocolController.post(
    '/deleteBatch',
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
    results, normalized_summary = _to_batch_contract(summary)
    return ResponseUtil.batch_result(results=results, summary=normalized_summary)


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
    return ResponseUtil.ok_resource(preview_result)


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
    protocol_id = require_int_value(
        import_result.result,
        'protocolId',
        'protocol_id',
        contract_name='protocol.import',
    )
    resource = await _load_protocol_detail(protocol_id, protocol_service)
    location = ResponseUtil.build_absolute_location(request, f'/system/protocol/{protocol_id}')
    return ResponseUtil.created_resource(resource, location=location)


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
    results, summary = _to_import_batch_contract(
        import_result.data,
        total=import_result.total_count,
        succeeded=import_result.success_count,
        failed=import_result.failed_count,
    )
    return ResponseUtil.batch_result(results=results, summary=summary)


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
    return ResponseUtil.ok_resource(protocol_detail_result)
