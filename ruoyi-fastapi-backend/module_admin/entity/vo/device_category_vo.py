from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from module_admin.annotation.pydantic_annotation import as_query


@as_query
class DeviceCategoryQueryModel(BaseModel):
    """
    设备分类查询模型
    """
    name: Optional[str] = Field(None, description="分类名称")
    status: Optional[str] = Field(None, description="状态（0正常 1停用）")
    begin_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    page_num: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class DeviceCategoryModel(BaseModel):
    """
    设备分类模型
    """
    device_category_id: Optional[int] = Field(None, description="设备分类ID")
    name: str = Field(..., min_length=2, max_length=50, description="分类名称")
    descr: Optional[str] = Field(None, max_length=255, description="分类描述")
    status: str = Field('0', description="状态（0正常 1停用）")
    create_by: Optional[str] = Field(None, description="创建者")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_by: Optional[str] = Field(None, description="更新者")
    update_time: Optional[datetime] = Field(None, description="更新时间")
    remark: Optional[str] = Field(None, max_length=500, description="备注")

    class Config:
        from_attributes = True


class DeviceCategoryOptionModel(BaseModel):
    """
    设备分类选项模型（用于下拉选择）
    """
    device_category_id: int = Field(..., description="设备分类ID")
    name: str = Field(..., description="分类名称")

    class Config:
        from_attributes = True
