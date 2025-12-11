from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportResult(BaseModel):
    """导出结果模型"""

    content: bytes = Field(description='导出内容字节')
    filename: str = Field(description='文件名')
    content_type: str = Field(description='MIME类型')
    size: int = Field(description='文件大小(字节)')
    created_at: datetime = Field(default_factory=datetime.now, description='创建时间')

    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat(),
        }
    }


class ImportStatus(str, Enum):
    SUCCESS = 'success'
    PARTIAL = 'partial'
    FAILED = 'failed'


class ImportError(BaseModel):
    """导入错误详情"""

    row: Optional[int] = Field(default=None, description='错误行号')
    field: Optional[str] = Field(default=None, description='错误字段')
    message: str = Field(description='错误信息')
    value: Optional[Any] = Field(default=None, description='错误值')


class ImportResult(BaseModel):
    """导入结果模型"""

    status: ImportStatus = Field(description='导入状态')
    total_count: int = Field(default=0, description='总记录数')
    success_count: int = Field(default=0, description='成功数')
    failed_count: int = Field(default=0, description='失败数')
    data: Optional[Any] = Field(default=None, description='导入的数据')
    errors: List[ImportError] = Field(default_factory=list, description='错误列表')

    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat(),
        }
    }


class ExportDataModel(BaseModel):
    """导出数据基类，强制包含版本信息"""

    export_version: str = Field(description='导出格式版本号')
    export_time: datetime = Field(default_factory=datetime.now, description='导出时间')

    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat(),
        }
    }


class ZipEntry(BaseModel):
    """ZIP文件条目"""

    filename: str = Field(description='文件名')
    content: bytes = Field(description='文件内容')
    compress_type: Optional[int] = Field(default=None, description='压缩类型')
