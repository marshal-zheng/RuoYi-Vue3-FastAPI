from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.device_vo import DeviceQueryModel, DeviceModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.device_service import DeviceService
from module_admin.service.login_service import LoginService
from utils.log_util import logger
from utils.response_util import ResponseUtil


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
    result = await DeviceService.get_device_list(
        query_db, query, current_user.user.user_name
    )
    logger.info('获取设备列表成功')
    return result


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
    result = await DeviceService.get_device_detail(query_db, device_id)
    logger.info(f'获取设备详情成功: {device_id}')
    return result


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
    result = await DeviceService.add_device(
        query_db, device_data, current_user.user.user_name
    )
    logger.info('新增设备成功')
    return result


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
    result = await DeviceService.update_device(
        query_db, device_data, current_user.user.user_name
    )
    logger.info('修改设备成功')
    return result


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
    result = await DeviceService.delete_device(query_db, device_ids)
    logger.info(f'删除设备成功: {device_ids}')
    return result
