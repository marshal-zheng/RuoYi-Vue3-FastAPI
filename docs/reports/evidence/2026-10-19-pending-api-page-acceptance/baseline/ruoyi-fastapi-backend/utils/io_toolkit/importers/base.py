from abc import ABC, abstractmethod
from typing import Optional, Type

from pydantic import BaseModel

from ..models import ImportResult


class ImportStrategy(ABC):
    """导入策略抽象基类"""

    @abstractmethod
    async def import_data(
        self,
        content: bytes,
        model: Optional[Type[BaseModel]] = None,
        **options,
    ) -> ImportResult:
        """
        执行导入操作
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """返回支持的文件扩展名列表"""
        raise NotImplementedError
