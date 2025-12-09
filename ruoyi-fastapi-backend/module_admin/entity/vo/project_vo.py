from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Any, Dict, List, Optional
from module_admin.annotation.pydantic_annotation import as_query


class ProjectModel(BaseModel):
    """
    工程管理表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    project_id: Optional[int] = Field(default=None, description='工程编号')
    project_name: Optional[str] = Field(default=None, description='工程名称')
    project_code: Optional[str] = Field(default=None, description='工程编码')
    project_desc: Optional[str] = Field(default=None, description='工程描述')
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    del_flag: Optional[str] = Field(default='0', description='删除标志（0代表存在 2代表删除）')


class ProjectQueryModel(ProjectModel):
    """
    工程管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class ProjectPageQueryModel(ProjectQueryModel):
    """
    工程管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProjectModel(BaseModel):
    """
    删除工程模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    project_ids: str = Field(description='需要删除的工程id')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class BatchProjectIdsModel(BaseModel):
    """
    批量工程ID模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    project_ids: List[int] = Field(default_factory=list, description='工程ID列表')


# ========== 工程导出/导入相关模型 ==========

class ExportDeviceInterfaceModel(BaseModel):
    """
    导出设备接口模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    interface_name: Optional[str] = Field(default=None, description='接口名称')
    interface_type: Optional[str] = Field(default=None, description='接口类型')
    position: Optional[str] = Field(default='right', description='端口位置')
    description: Optional[str] = Field(default=None, description='接口描述')
    params: Optional[Dict[str, Any]] = Field(default=None, description='接口参数配置')
    message_config: Optional[Dict[str, Any]] = Field(default=None, description='报文配置')


class ExportDeviceModel(BaseModel):
    """
    导出设备模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    device_id: Optional[int] = Field(default=None, description='设备ID（导出用于映射）')
    device_name: str = Field(description='设备名称')
    device_type: Optional[str] = Field(default=None, description='设备类型')
    category_name: Optional[str] = Field(default=None, description='分类名称')
    manufacturer: Optional[str] = Field(default=None, description='制造商')
    model: Optional[str] = Field(default=None, description='型号')
    version: Optional[str] = Field(default=None, description='版本')
    bus_type: Optional[str] = Field(default=None, description='总线类型')
    remark: Optional[str] = Field(default=None, description='备注')
    interfaces: List[ExportDeviceInterfaceModel] = Field(default_factory=list, description='接口列表')


class ExportVersionModel(BaseModel):
    """
    导出版本模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    version_number: str = Field(description='版本号')
    version_name: str = Field(description='版本名称')
    description: Optional[str] = Field(default=None, description='版本描述')
    status: Optional[str] = Field(default='1', description='状态')
    is_locked: Optional[str] = Field(default='0', description='是否固化')
    topology: Optional[Dict[str, Any]] = Field(default=None, description='拓扑数据')


class ExportProjectModel(BaseModel):
    """
    导出工程基本信息模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    project_name: str = Field(description='工程名称')
    project_code: Optional[str] = Field(default=None, description='工程编码')
    project_desc: Optional[str] = Field(default=None, description='工程描述')
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class ProjectExportDataModel(BaseModel):
    """
    完整的工程导出数据模型
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    export_version: str = Field(default='1.0.0', description='导出格式版本')
    export_time: datetime = Field(description='导出时间')
    project: ExportProjectModel = Field(description='工程基本信息')
    versions: List[ExportVersionModel] = Field(default_factory=list, description='版本列表')
    devices: List[ExportDeviceModel] = Field(default_factory=list, description='设备列表')


class ProjectImportDataModel(BaseModel):
    """
    工程导入数据模型（与导出模型结构一致）
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    export_version: str = Field(description='导出格式版本')
    export_time: Optional[datetime] = Field(default=None, description='导出时间')
    project: ExportProjectModel = Field(description='工程基本信息')
    versions: List[ExportVersionModel] = Field(default_factory=list, description='版本列表')
    devices: List[ExportDeviceModel] = Field(default_factory=list, description='设备列表')
