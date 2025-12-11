import io
from typing import Dict, List, Optional, Type, Any

import pandas as pd
from pydantic import BaseModel, ValidationError

from ..exceptions import ImportException, ImportValidationException
from ..models import ImportError, ImportResult, ImportStatus
from .base import ImportStrategy


class ExcelImporter(ImportStrategy):
    """Excel导入器：支持列映射与可选模型验证"""

    def __init__(
        self,
        header_mapping: Optional[Dict[str, str]] = None,
        sheet_name: Optional[str] = None,
        skip_rows: int = 0,
    ):
        self.header_mapping = header_mapping or {}
        self.sheet_name = sheet_name
        self.skip_rows = skip_rows

    @property
    def supported_extensions(self) -> list[str]:
        return ['.xlsx', '.xls']

    async def import_data(
        self,
        content: bytes,
        model: Optional[Type[BaseModel]] = None,
        **options,
    ) -> ImportResult:
        if not content:
            raise ImportException('文件内容为空')

        df = pd.read_excel(
            io.BytesIO(content),
            sheet_name=self.sheet_name,
            skiprows=self.skip_rows,
            dtype=object,
        )

        records = self._apply_mapping(df.to_dict(orient='records'))

        if model:
            return self._validate_with_model(records, model)

        total = len(records)
        return ImportResult(
            status=ImportStatus.SUCCESS,
            total_count=total,
            success_count=total,
            failed_count=0,
            data=records,
        )

    def _apply_mapping(self, records: List[Dict]) -> List[Dict]:
        if not self.header_mapping:
            return records
        mapped = []
        for row in records:
            mapped.append({self.header_mapping.get(k, k): v for k, v in row.items()})
        return mapped

    def _validate_with_model(self, records: List[Dict], model: Type[BaseModel]) -> ImportResult:
        errors: List[ImportError] = []
        validated: List[Any] = []

        for idx, row in enumerate(records, start=2):  # Excel数据通常从第2行开始
            try:
                if hasattr(model, 'model_validate'):
                    validated.append(model.model_validate(row))
                else:
                    validated.append(model.parse_obj(row))
            except ValidationError as exc:
                for err in exc.errors():
                    errors.append(
                        ImportError(
                            row=idx,
                            field='.'.join(map(str, err.get('loc', []))),
                            message=err.get('msg', '校验失败'),
                            value=row.get(err.get('loc', [None])[0]) if err.get('loc') else None,
                        )
                    )

        total = len(records)
        failed = len(errors)
        success = total - failed
        status = ImportStatus.SUCCESS if failed == 0 else ImportStatus.PARTIAL

        if errors:
            # 返回部分成功而非直接抛异常，调用侧可根据需要处理
            return ImportResult(
                status=status,
                total_count=total,
                success_count=success,
                failed_count=failed,
                data=validated,
                errors=errors,
            )

        return ImportResult(
            status=status,
            total_count=total,
            success_count=success,
            failed_count=failed,
            data=validated,
            errors=[],
        )
