from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.device_category_do import DeviceCategoryDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.device_category_vo import DeviceCategoryModel, DeviceCategoryOptionModel, DeviceCategoryQueryModel
from ports import IDeviceCategoryRepository, IDeviceRepository
from utils.transaction_manager import transactional


class DeviceCategoryService:
    """
    设备分类服务类
    """

    def __init__(
        self,
        category_repo: IDeviceCategoryRepository,
        device_repo: IDeviceRepository,
        query_db: AsyncSession,
    ):
        self.category_repo = category_repo
        self.device_repo = device_repo
        self.query_db = query_db

    async def get_device_category_list_services(self, query: DeviceCategoryQueryModel, current_user: str):
        """
        获取设备分类列表
        """
        categories, total = await self.category_repo.paginate_with_filters(
            page=query.page,
            page_size=query.page_size,
            name=query.name,
            status=query.status,
            begin_time=query.begin_time,
            end_time=query.end_time,
        )

        category_list = [DeviceCategoryModel.model_validate(cat) for cat in categories]
        return {
            'items': [cat.model_dump() for cat in category_list],
            'page': query.page,
            'pageSize': query.page_size,
            'total': total,
        }

    async def device_category_detail_services(self, category_id: int):
        """
        获取设备分类详情
        """
        category = await self.category_repo.find_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail='设备分类不存在')

        category_vo = DeviceCategoryModel.model_validate(category)
        return category_vo.model_dump()

    @transactional()
    async def add_device_category_services(self, category_data: DeviceCategoryModel, current_user: str):
        """
        新增设备分类
        """
        # 检查名称是否已存在
        existing = await self.category_repo.find_by_name(category_data.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"分类名称'{category_data.name}'已存在")

        # 创建DO对象
        category_do = DeviceCategoryDO(
            name=category_data.name,
            descr=category_data.descr,
            status=category_data.status,
            create_by=current_user,
            create_time=datetime.now(),
            remark=category_data.remark,
        )

        # 保存到数据库
        add_result = await self.category_repo.add(category_do)

        return CrudResponseModel(
            is_success=True,
            message='新增成功',
            result={'deviceCategoryId': add_result.device_category_id},
        )

    @transactional()
    async def edit_device_category_services(self, category_data: DeviceCategoryModel, current_user: str):
        """
        更新设备分类
        """
        # 检查分类是否存在
        existing = await self.category_repo.find_by_id(category_data.device_category_id)
        if not existing:
            raise HTTPException(status_code=404, detail='设备分类不存在')

        # 检查名称是否与其他分类重复
        name_check = await self.category_repo.find_by_name(category_data.name)
        if name_check and name_check.device_category_id != category_data.device_category_id:
            raise HTTPException(status_code=400, detail=f"分类名称'{category_data.name}'已存在")

        # 更新字段
        existing.name = category_data.name
        existing.descr = category_data.descr
        existing.status = category_data.status
        existing.remark = category_data.remark
        existing.update_by = current_user
        existing.update_time = datetime.now()

        await self.category_repo.update(existing)

        return CrudResponseModel(
            is_success=True,
            message='修改成功',
            result={'deviceCategoryId': existing.device_category_id},
        )

    @transactional()
    async def delete_device_category_services(self, category_ids: str):
        """
        删除设备分类
        """
        # 解析ID列表
        id_list = [int(id_str) for id_str in category_ids.split(',') if id_str.strip()]

        referenced_count = await self.device_repo.count_by_category_ids(id_list)
        if referenced_count > 0:
            raise HTTPException(status_code=400, detail='所选设备分类已被设备引用，无法删除')

        # 删除分类
        deleted_count = await self.category_repo.delete_by_ids(id_list)

        return CrudResponseModel(is_success=True, message=f'删除成功，共删除{deleted_count}条记录')

    async def get_device_category_options_services(self):
        """
        获取设备分类选项（用于下拉选择）
        """
        categories = await self.category_repo.find_all_active()

        # 转换为选项模型
        options = [DeviceCategoryOptionModel.model_validate(cat) for cat in categories]

        return [opt.model_dump() for opt in options]

    async def check_device_category_name_unique_services(self, name: str, category_id: int = None):
        """
        检查分类名称是否唯一
        """
        existing = await self.category_repo.find_by_name(name)

        if not existing:
            return True

        if category_id and existing.device_category_id == category_id:
            return True

        return False
