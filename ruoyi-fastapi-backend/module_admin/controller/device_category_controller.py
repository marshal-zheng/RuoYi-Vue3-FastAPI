from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from container.dependencies import service_provider
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.device_category_vo import DeviceCategoryQueryModel, DeviceCategoryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.device_category_service import DeviceCategoryService
from modules.identity.application.services.login_service import LoginService
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.response_util import ResponseUtil


deviceCategoryController = APIRouter(prefix='/device/category', dependencies=[Depends(LoginService.get_current_user)])


async def _load_device_category_detail(category_id: int, device_category_service: DeviceCategoryService):
    result = await device_category_service.device_category_detail_services(category_id)
    return result or {}


@deviceCategoryController.get(
    '/list',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:list'))]
)
async def get_device_category_list(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    获取设备分类列表
    """
    qp = dict(request.query_params)
    name = qp.get('name')
    status = qp.get('status')
    begin_time = qp.get('begin_time') or qp.get('beginTime')
    end_time = qp.get('end_time') or qp.get('endTime')
    try:
        page = int(qp.get('page') or 1)
    except Exception:
        page = 1
    try:
        page_size = int(qp.get('pageSize') or qp.get('page_size') or 10)
    except Exception:
        page_size = 10

    query = DeviceCategoryQueryModel(
        name=name,
        status=status,
        begin_time=begin_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    result = await device_category_service.get_device_category_list_services(query, current_user.user.user_name)
    logger.info('获取设备分类列表成功')
    return ResponseUtil.ok_page(items=result['items'], total=result['total'], page=page, page_size=page_size)


@deviceCategoryController.get(
    '/{category_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:query'))]
)
async def get_device_category_detail(
    request: Request,
    category_id: int,
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    获取设备分类详情
    """
    result = await device_category_service.device_category_detail_services(category_id)
    logger.info(f'获取设备分类详情成功: {category_id}')
    return ResponseUtil.ok_resource(result)


@deviceCategoryController.post(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:add'))]
)
@Log(title='设备分类管理', business_type=BusinessType.INSERT)
async def add_device_category(
    request: Request,
    category_data: DeviceCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    新增设备分类
    """
    result = await device_category_service.add_device_category_services(category_data, current_user.user.user_name)
    logger.info('新增设备分类成功')
    category_id = require_int_value(
        result.result,
        'deviceCategoryId',
        'device_category_id',
        contract_name='device-category.create',
    )
    resource = await _load_device_category_detail(category_id, device_category_service)
    location = ResponseUtil.build_absolute_location(request, f'/device/category/{category_id}')
    return ResponseUtil.created_resource(resource, location=location)


@deviceCategoryController.put(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:edit'))]
)
@Log(title='设备分类管理', business_type=BusinessType.UPDATE)
async def update_device_category(
    request: Request,
    category_data: DeviceCategoryModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    修改设备分类
    """
    result = await device_category_service.edit_device_category_services(category_data, current_user.user.user_name)
    logger.info('修改设备分类成功')
    resource = await _load_device_category_detail(category_data.device_category_id, device_category_service)
    return ResponseUtil.ok_resource(resource)


@deviceCategoryController.delete(
    '/{category_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:remove'))]
)
@Log(title='设备分类管理', business_type=BusinessType.DELETE)
async def delete_device_category(
    request: Request,
    category_ids: str,
    query_db: AsyncSession = Depends(get_db),
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    删除设备分类
    """
    result = await device_category_service.delete_device_category_services(category_ids)
    logger.info(f'删除设备分类成功: {category_ids}')
    return ResponseUtil.no_content()


@deviceCategoryController.get(
    '/options',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:query'))]
)
async def get_device_category_options(
    request: Request,
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    获取设备分类选项（用于下拉选择）
    """
    result = await device_category_service.get_device_category_options_services()
    logger.info('获取设备分类选项成功')
    return ResponseUtil.ok_resource(result)


@deviceCategoryController.get(
    '/checkNameUnique',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:query'))]
)
async def check_device_category_name_unique(
    request: Request,
    name: str,
    category_id: int = None,
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    检查设备分类名称是否唯一
    """
    result = await device_category_service.check_device_category_name_unique_services(name, category_id)
    return ResponseUtil.ok_resource(result)
