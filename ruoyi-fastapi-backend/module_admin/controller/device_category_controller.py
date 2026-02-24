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
from utils.log_util import logger
from utils.response_util import ResponseUtil


deviceCategoryController = APIRouter(prefix='/device/category', dependencies=[Depends(LoginService.get_current_user)])


@deviceCategoryController.get(
    '/list',
    dependencies=[Depends(CheckUserInterfaceAuth('device:category:list'))]
)
async def get_device_category_list(
    request: Request,
    name: str = None,
    status: str = None,
    begin_time: str = None,
    end_time: str = None,
    page_num: int = 1,
    page_size: int = 10,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    device_category_service: DeviceCategoryService = Depends(service_provider('device_category_service')),
):
    """
    获取设备分类列表
    """
    query = DeviceCategoryQueryModel(
        name=name,
        status=status,
        begin_time=begin_time,
        end_time=end_time,
        page_num=page_num,
        page_size=page_size
    )
    result = await device_category_service.get_device_category_list_services(query, current_user.user.user_name)
    logger.info('获取设备分类列表成功')
    return ResponseUtil.success(rows=result['rows'], dict_content={'total': result['total']})


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
    return ResponseUtil.success(data=result)


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
    return ResponseUtil.success(message=result.message)


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
    return ResponseUtil.success(message=result.message)


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
    return ResponseUtil.success(message=result.message)


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
    return ResponseUtil.success(data=result)


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
    return ResponseUtil.success(data=result)
