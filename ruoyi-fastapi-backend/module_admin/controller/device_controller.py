from fastapi import APIRouter, Depends, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.device_vo import DeviceQueryModel, DeviceModel, CloneDeviceModel, BatchDeviceIdsModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.device_service import DeviceService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.common_util import bytes2file_response
from urllib.parse import quote
import re


deviceController = APIRouter(prefix='/device', dependencies=[Depends(LoginService.get_current_user)])


@deviceController.get(
    '/list',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:list'))]
)
async def get_device_list(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
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
        page_num = int(qp.get('page_num') or qp.get('pageNum') or 1)
    except Exception:
        page_num = 1
    try:
        page_size = int(qp.get('page_size') or qp.get('pageSize') or 10)
    except Exception:
        page_size = 10

    query = DeviceQueryModel(
        device_name=device_name,
        bus_type=bus_type,
        begin_time=begin_time,
        end_time=end_time,
        page_num=page_num,
        page_size=page_size
    )
    result = await DeviceService.get_device_list_services(
        query_db, query, current_user.user.user_name
    )
    logger.info('获取设备列表成功')
    return ResponseUtil.success(rows=result['rows'], dict_content={'total': result['total']})


@deviceController.get(
    '/checkNameUnique',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:query'))]
)
async def check_device_name_unique(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
):
    """
    检查设备名称是否唯一
    """
    qp = dict(request.query_params)
    device_name = qp.get('deviceName') or qp.get('device_name')
    device_id = qp.get('deviceId') or qp.get('device_id')
    device_id = int(device_id) if device_id else None
    
    result = await DeviceService.check_device_name_unique_services(query_db, device_name, device_id)
    logger.info(f'检查设备名称唯一性: {device_name}')
    return ResponseUtil.success(data=result)


@deviceController.get(
    '/{device_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:query'))]
)
async def get_device_detail(
    request: Request,
    device_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取设备详情（包含接口配置）
    """
    result = await DeviceService.device_detail_services(query_db, device_id)
    logger.info(f'获取设备详情成功: {device_id}')
    return ResponseUtil.success(data=result)


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
):
    """
    新增设备（包含接口）
    """
    result = await DeviceService.add_device_services(
        query_db, device_data, current_user.user.user_name
    )
    logger.info('新增设备成功')
    return ResponseUtil.success(message=result.message, data=result.result)


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
):
    """
    修改设备（包含接口）
    """
    result = await DeviceService.edit_device_services(
        query_db, device_data, current_user.user.user_name
    )
    logger.info('修改设备成功')
    return ResponseUtil.success(message=result.message)


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
):
    """
    克隆设备（包含接口）
    """
    clone_data.create_by = current_user.user.user_name
    clone_data.create_time = datetime.now()
    result = await DeviceService.clone_device_services(query_db, clone_data, current_user.user.user_name)
    logger.info('克隆设备成功')
    return ResponseUtil.success(message=result.message, data=result.result)


@deviceController.delete(
    '/{device_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:remove'))]
)
@Log(title='设备管理', business_type=BusinessType.DELETE)
async def delete_device(
    request: Request,
    device_ids: str,
    query_db: AsyncSession = Depends(get_db),
):
    """
    删除设备（级联删除接口）
    """
    result = await DeviceService.delete_device_services(query_db, device_ids)
    logger.info(f'删除设备成功: {device_ids}')
    return ResponseUtil.success(message=result.message)


@deviceController.post(
    '/export/batch',
    dependencies=[Depends(CheckUserInterfaceAuth('device:list:list'))]
)
@Log(title='设备管理-批量导出', business_type=BusinessType.EXPORT)
async def export_device_batch(
    request: Request,
    device_ids_body: BatchDeviceIdsModel,
    query_db: AsyncSession = Depends(get_db),
):
    """
    批量导出设备数据（zip）
    """
    buffer, filename = await DeviceService.export_devices_zip_services(
        query_db, device_ids_body.device_ids
    )
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
):
    """
    批量导入设备数据（zip或json）
    """
    if files:
        contents = [await f.read() for f in files]
        import_result = await DeviceService.import_devices_multi_services(
            query_db, contents, current_user.user.user_name
        )
        return ResponseUtil.success(message='批量导入完成', data=import_result)

    if file:
        file_bytes = await file.read()
        import_result = await DeviceService.import_devices_from_zip_services(
            query_db, file_bytes, current_user.user.user_name
        )
        return ResponseUtil.success(message='批量导入完成', data=import_result)

    from exceptions.exception import ValidationException
    raise ValidationException(
        user_message='未提供上传文件',
        developer_message='No file provided for device import',
        field='file'
    )
