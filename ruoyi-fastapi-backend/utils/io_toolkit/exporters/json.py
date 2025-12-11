from typing import Any, Optional, Union, List, Dict
import json

try:
    import orjson
except ImportError:  # pragma: no cover - 运行时可选依赖
    orjson = None

from pydantic import BaseModel

from ..exceptions import ExportException
from ..models import ExportResult
from .base import ExportStrategy


class JsonExporter(ExportStrategy):
    """JSON导出器：支持Pydantic模型和自定义编码选项"""

    def __init__(
        self,
        ensure_ascii: bool = False,
        indent: Optional[int] = None,
    ):
        self.ensure_ascii = ensure_ascii
        self.indent = indent

    @property
    def content_type(self) -> str:
        return 'application/json'

    @property
    def file_extension(self) -> str:
        return '.json'

    async def export(
        self,
        data: Union[BaseModel, Dict, List, Any],
        filename: Optional[str] = None,
        **options,
    ) -> ExportResult:
        if data is None:
            raise ExportException('导出数据为空')

        content_bytes = self._serialize(data)
        safe_filename = filename or 'export'
        if not safe_filename.endswith(self.file_extension):
            safe_filename = f'{safe_filename}{self.file_extension}'

        return ExportResult(
            content=content_bytes,
            filename=safe_filename,
            content_type=self.content_type,
            size=len(content_bytes),
        )

    def _serialize(self, data: Any) -> bytes:
        if isinstance(data, BaseModel):
            payload = data.model_dump(mode='json')
        else:
            payload = data

        if orjson:
            return orjson.dumps(payload, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY)

        return json.dumps(payload, ensure_ascii=self.ensure_ascii, indent=self.indent, default=str).encode('utf-8')
