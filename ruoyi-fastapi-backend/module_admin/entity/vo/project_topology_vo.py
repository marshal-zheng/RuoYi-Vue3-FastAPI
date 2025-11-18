from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProjectTopologyModel(BaseModel):
    """
    工程拓扑数据 pydantic 模型
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )

    topology_id: Optional[int] = Field(default=None, description='拓扑ID')
    project_id: int = Field(description='工程编号')
    version_id: Optional[int] = Field(default=None, description='版本ID')
    topology_data: Dict[str, Any] = Field(
        description='拓扑数据（包含图结构、总线设计、接口控制等）'
    )
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
