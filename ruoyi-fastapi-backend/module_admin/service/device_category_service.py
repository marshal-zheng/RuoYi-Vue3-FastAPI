from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List
from fastapi import HTTPException
from module_admin.dao.device_category_dao import DeviceCategoryDao
from module_admin.entity.do.device_category_do import DeviceCategoryDO
from module_admin.entity.vo.device_category_vo import DeviceCategoryQueryModel, DeviceCategoryModel, DeviceCategoryOptionModel
from utils.response_util import ResponseUtil


class DeviceCategoryService:
    """
    设备分类服务类
    """

    @classmethod
    async def get_device_category_list(cls, db: AsyncSession, query: DeviceCategoryQueryModel, current_user: str):
        """
        获取设备分类列表
        """
        categories, total = await DeviceCategoryDao.get_device_category_list(db, query)

        category_list = [DeviceCategoryModel.model_validate(cat) for cat in categories]
        return ResponseUtil.success(
            rows=[cat.model_dump() for cat in category_list],
            dict_content={'total': total}
        )

    @classmethod
    async def get_device_category_detail(cls, db: AsyncSession, category_id: int):
        """
        获取设备分类详情
        """
        category = await DeviceCategoryDao.get_device_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="设备分类不存在")
        
        category_vo = DeviceCategoryModel.model_validate(category)
        return ResponseUtil.success(data=category_vo.model_dump())

    @classmethod
    async def add_device_category(cls, db: AsyncSession, category_data: DeviceCategoryModel, current_user: str):
        """
        新增设备分类
        """
        # 检查名称是否已存在
        existing = await DeviceCategoryDao.get_device_category_by_name(db, category_data.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"分类名称'{category_data.name}'已存在")
        
        # 创建DO对象
        category_do = DeviceCategoryDO(
            name=category_data.name,
            descr=category_data.descr,
            status=category_data.status,
            create_by=current_user,
            create_time=datetime.now(),
            remark=category_data.remark
        )
        
        # 保存到数据库
        result = await DeviceCategoryDao.add_device_category(db, category_do)
        await db.commit()
        
        return ResponseUtil.success(msg="新增成功")

    @classmethod
    async def update_device_category(cls, db: AsyncSession, category_data: DeviceCategoryModel, current_user: str):
        """
        更新设备分类
        """
        # 检查分类是否存在
        existing = await DeviceCategoryDao.get_device_category_by_id(db, category_data.device_category_id)
        if not existing:
            raise HTTPException(status_code=404, detail="设备分类不存在")
        
        # 检查名称是否与其他分类重复
        name_check = await DeviceCategoryDao.get_device_category_by_name(db, category_data.name)
        if name_check and name_check.device_category_id != category_data.device_category_id:
            raise HTTPException(status_code=400, detail=f"分类名称'{category_data.name}'已存在")
        
        # 更新字段
        existing.name = category_data.name
        existing.descr = category_data.descr
        existing.status = category_data.status
        existing.remark = category_data.remark
        existing.update_by = current_user
        existing.update_time = datetime.now()
        
        # 保存到数据库
        await DeviceCategoryDao.update_device_category(db, existing)
        await db.commit()
        
        return ResponseUtil.success(msg="修改成功")

    @classmethod
    async def delete_device_category(cls, db: AsyncSession, category_ids: str):
        """
        删除设备分类
        """
        # 解析ID列表
        id_list = [int(id_str) for id_str in category_ids.split(',')]
        
        # TODO: 检查分类是否被设备使用
        # 如果有设备使用该分类，应该抛出异常
        
        # 删除分类
        deleted_count = await DeviceCategoryDao.delete_device_category(db, id_list)
        await db.commit()
        
        return ResponseUtil.success(msg=f"删除成功，共删除{deleted_count}条记录")

    @classmethod
    async def get_device_category_options(cls, db: AsyncSession):
        """
        获取设备分类选项（用于下拉选择）
        """
        categories = await DeviceCategoryDao.get_all_device_categories(db)
        
        # 转换为选项模型
        options = [DeviceCategoryOptionModel.model_validate(cat) for cat in categories]
        
        return ResponseUtil.success(data=[opt.model_dump() for opt in options])

    @classmethod
    async def check_name_unique(cls, db: AsyncSession, name: str, category_id: int = None):
        """
        检查分类名称是否唯一
        """
        existing = await DeviceCategoryDao.get_device_category_by_name(db, name)
        
        if not existing:
            return ResponseUtil.success(data=True)
        
        if category_id and existing.device_category_id == category_id:
            return ResponseUtil.success(data=True)
        
        return ResponseUtil.success(data=False)
