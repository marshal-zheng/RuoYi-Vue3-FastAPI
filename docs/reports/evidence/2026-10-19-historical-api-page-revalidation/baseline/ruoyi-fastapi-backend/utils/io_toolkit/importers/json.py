import json
from typing import Any, Optional, Type

try:
    import orjson
except ImportError:  # pragma: no cover
    orjson = None

from pydantic import BaseModel, ValidationError

from ..exceptions import ImportException
from ..models import ImportError, ImportResult, ImportStatus
from .base import ImportStrategy


class JsonImporter(ImportStrategy):
    """JSON导入器：支持Pydantic模型验证"""

    @property
    def supported_extensions(self) -> list[str]:
        return ['.json']

    async def import_data(
        self,
        content: bytes,
        model: Optional[Type[BaseModel]] = None,
        **options,
    ) -> ImportResult:
        if not content:
            raise ImportException('文件内容为空')

        payload = self._loads(content)

        if model is None:
            return ImportResult(
                status=ImportStatus.SUCCESS,
                total_count=1 if payload is not None else 0,
                success_count=1 if payload is not None else 0,
                failed_count=0,
                data=payload,
            )

        try:
            if isinstance(payload, list):
                validated = [self._validate_model(model, item) for item in payload]
            else:
                validated = self._validate_model(model, payload)
            success_count = len(validated) if isinstance(validated, list) else 1
            return ImportResult(
                status=ImportStatus.SUCCESS,
                total_count=success_count,
                success_count=success_count,
                failed_count=0,
                data=validated,
            )
        except ValidationError as exc:
            errors = []
            for err in exc.errors():
                errors.append(
                    ImportError(
                        row=None,
                        field='.'.join(map(str, err.get('loc', []))),
                        message=err.get('msg', '校验失败'),
                        value=None,
                    )
                )
            return ImportResult(
                status=ImportStatus.FAILED,
                total_count=1,
                success_count=0,
                failed_count=1,
                errors=errors,
            )

    def _loads(self, content: bytes) -> Any:
        if orjson:
            return orjson.loads(content)
        return json.loads(content.decode('utf-8'))

    def _validate_model(self, model: Type[BaseModel], data: Any):
        if hasattr(model, 'model_validate'):
            return model.model_validate(data)
        return model.parse_obj(data)
