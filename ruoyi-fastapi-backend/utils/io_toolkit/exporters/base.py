from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models import ExportResult


class ExportStrategy(ABC):
    """导出策略抽象基类"""

    @abstractmethod
    async def export(self, data: Any, **options) -> ExportResult:
        """
        执行导出操作
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def content_type(self) -> str:
        """返回导出内容的MIME类型"""
        raise NotImplementedError

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """返回导出文件的扩展名"""
        raise NotImplementedError
