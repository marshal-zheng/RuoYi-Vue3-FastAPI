from fastapi import APIRouter, Depends, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.device_vo import DeviceQueryModel, DeviceModel, CloneDeviceModel, BatchDeviceIdsModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.device_service import DeviceService
from modules.identity.application.services.login_service import LoginService
from utils.http_contract_responses import import_summary_to_batch_contract, require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.common_util import bytes2file_response
from urllib.parse import quote
import re


deviceController = APIRouter(prefix='/device', dependencies=[Depends(LoginService.get_current_user)])


async def _load_device_detail(device_id: int, device_service: DeviceService):
    result = await device_service.device_detail_services(device_id)
    return result or {}


@deviceController.get(
    '/list',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:list'))]
)
async def get_device_list(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    获取设备列表
    """
    qp = dict(request.query_params)
    device_name = qp.get('device_name') or qp.get('deviceName')
    bus_type = qp.get('bus_type') or qp.get('busType')
    begin_time = qp.get('begin_time') or qp.get('beginTime')
    end_time = qp.get('end_time') or qp.get('endTime')
    # 兼容 dateRange
    date_range = qp.get('dateRange')
    if date_range and (not begin_time or not end_time):
        parts = [p.strip() for p in date_range.split(',') if p.strip()]
        if len(parts) == 2:
            begin_time = begin_time or parts[0]
            end_time = end_time or parts[1]
    try:
        page = int(qp.get('page') or 1)
    except Exception:
        page = 1
    try:
        page_size = int(qp.get('pageSize') or qp.get('page_size') or 10)
    except Exception:
        page_size = 10

    query = DeviceQueryModel(
        device_name=device_name,
        bus_type=bus_type,
        begin_time=begin_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    result = await device_service.get_device_list_services(query, current_user.user.user_name)
    logger.info('获取设备列表成功')
    return ResponseUtil.ok_page(items=result['items'], total=result['total'], page=page, page_size=page_size)


@deviceController.get(
    '/checkNameUnique',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:query'))]
)
async def check_device_name_unique(
    request: Request,
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    检查设备名称是否唯一
    """
    qp = dict(request.query_params)
    device_name = qp.get('deviceName') or qp.get('device_name')
    device_id = qp.get('deviceId') or qp.get('device_id')
    device_id = int(device_id) if device_id else None
    
    result = await device_service.check_device_name_unique_services(device_name, device_id)
    logger.info(f'检查设备名称唯一性: {device_name}')
    return ResponseUtil.ok_resource(result)


@deviceController.get(
    '/{device_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:query'))]
)
async def get_device_detail(
    request: Request,
    device_id: int,
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    获取设备详情（包含接口配置）
    """
    result = await device_service.device_detail_services(device_id)
    logger.info(f'获取设备详情成功: {device_id}')
    return ResponseUtil.ok_resource(result)


@deviceController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:add'))]
)
@Log(title='设备管理', business_type=BusinessType.INSERT)
async def add_device(
    request: Request,
    device_data: DeviceModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    新增设备（包含接口）
    """
    result = await device_service.add_device_services(device_data, current_user.user.user_name)
    logger.info('新增设备成功')
    device_id = require_int_value(result.result, 'deviceId', 'device_id', contract_name='device.create')
    resource = await _load_device_detail(device_id, device_service)
    location = ResponseUtil.build_absolute_location(request, f'/device/{device_id}')
    return ResponseUtil.created_resource(resource, location=location)


@deviceController.put(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:edit'))]
)
@Log(title='设备管理', business_type=BusinessType.UPDATE)
async def update_device(
    request: Request,
    device_data: DeviceModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    修改设备（包含接口）
    """
    result = await device_service.edit_device_services(device_data, current_user.user.user_name)
    logger.info('修改设备成功')
    resource = await _load_device_detail(device_data.device_id, device_service)
    return ResponseUtil.ok_resource(resource)


@deviceController.post(
    '/clone',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:add'))]
)
@Log(title='设备管理', business_type=BusinessType.INSERT)
async def clone_device(
    request: Request,
    clone_data: CloneDeviceModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    克隆设备（包含接口）
    """
    clone_data.create_by = current_user.user.user_name
    clone_data.create_time = datetime.now()
    result = await device_service.clone_device_services(clone_data, current_user.user.user_name)
    logger.info('克隆设备成功')
    device_id = require_int_value(result.result, 'deviceId', 'device_id', contract_name='device.clone')
    resource = await _load_device_detail(device_id, device_service)
    location = ResponseUtil.build_absolute_location(request, f'/device/{device_id}')
    return ResponseUtil.created_resource(resource, location=location)


@deviceController.delete(
    '/{device_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:remove'))]
)
@Log(title='设备管理', business_type=BusinessType.DELETE)
async def delete_device(
    request: Request,
    device_ids: str,
    query_db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    删除设备（级联删除接口）
    """
    result = await device_service.delete_device_services(device_ids)
    logger.info(f'删除设备成功: {device_ids}')
    return ResponseUtil.no_content()


@deviceController.post(
    '/export/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:list'))]
)
@Log(title='设备管理-批量导出', business_type=BusinessType.EXPORT)
async def export_device_batch(
    request: Request,
    device_ids_body: BatchDeviceIdsModel,
    query_db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    批量导出设备数据（zip）
    """
    buffer, filename = await device_service.export_devices_zip_services(device_ids_body.device_ids)
    encoded_filename = quote(filename)
    ascii_fallback = re.sub(r'[^0-9A-Za-z._-]+', '_', filename)
    content_disposition = f"attachment; filename={ascii_fallback}; filename*=UTF-8''{encoded_filename}"
    return ResponseUtil.streaming(
        data=bytes2file_response(buffer.getvalue()),
        headers={'Content-Disposition': content_disposition},
        media_type='application/zip',
    )


@deviceController.post(
    '/import/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:add'))]
)
@Log(title='设备管理-批量导入', business_type=BusinessType.IMPORT)
async def import_device_batch(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    file: UploadFile = File(default=None),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_service: DeviceService = Depends(service_provider('device_service')),
):
    """
    批量导入设备数据（zip或json）
    """
    if files:
        contents = [await f.read() for f in files]
        import_result = await device_service.import_devices_multi_services(
            contents, current_user.user.user_name
        )
        results, summary = import_summary_to_batch_contract(
            import_result.get('details'),
            item_id_keys=('deviceId', 'fileName'),
            data_keys=('deviceId', 'deviceName', 'fileName'),
        )
        return ResponseUtil.batch_result(results=results, summary=summary)

    if file:
        file_bytes = await file.read()
        import_result = await device_service.import_devices_from_zip_services(
            file_bytes, current_user.user.user_name
        )
        results, summary = import_summary_to_batch_contract(
            import_result.get('details'),
            item_id_keys=('deviceId', 'fileName'),
            data_keys=('deviceId', 'deviceName', 'fileName'),
        )
        return ResponseUtil.batch_result(results=results, summary=summary)

    from exceptions.exception import ValidationException
    raise ValidationException(
        user_message='未提供上传文件',
        developer_message='No file provided for device import',
        field='file'
    )
