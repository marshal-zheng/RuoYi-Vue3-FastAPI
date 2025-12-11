import io
from typing import Callable, List, Optional, Type
from zipfile import ZipFile, is_zipfile

from pydantic import BaseModel

from ..exceptions import ImportException
from ..models import ImportError, ImportResult, ImportStatus
from .base import ImportStrategy


class ZipImporter(ImportStrategy):
    """ZIP解包导入器，可选文件过滤和内部导入器组合"""

    def __init__(
        self,
        file_filter: Optional[Callable[[str], bool]] = None,
        inner_importer: Optional[ImportStrategy] = None,
    ):
        self.file_filter = file_filter
        self.inner_importer = inner_importer

    @property
    def supported_extensions(self) -> list[str]:
        return ['.zip']

    async def import_data(
        self,
        content: bytes,
        model: Optional[Type[BaseModel]] = None,
        **options,
    ) -> ImportResult:
        if not content:
            raise ImportException('文件内容为空')

        buffer = io.BytesIO(content)
        if not is_zipfile(buffer):
            raise ImportException('上传文件不是有效的zip格式')

        buffer.seek(0)
        with ZipFile(buffer, 'r') as zip_file:
            file_names = [
                name for name in zip_file.namelist()
                if not name.endswith('/') and (self.file_filter(name) if self.file_filter else True)
            ]

            if not file_names:
                return ImportResult(
                    status=ImportStatus.FAILED,
                    total_count=0,
                    success_count=0,
                    failed_count=0,
                    errors=[ImportError(message='zip包中未找到可导入的文件')],
                )

            if not self.inner_importer:
                entries = {name: zip_file.read(name) for name in file_names}
                return ImportResult(
                    status=ImportStatus.SUCCESS,
                    total_count=len(entries),
                    success_count=len(entries),
                    failed_count=0,
                    data=entries,
                )

            results = []
            errors: List[ImportError] = []
            success_count = 0

            for name in file_names:
                file_bytes = zip_file.read(name)
                try:
                    inner_result = await self.inner_importer.import_data(
                        file_bytes,
                        model=model,
                        **options,
                    )
                    results.append({'fileName': name, 'result': inner_result})
                    success_count += 1 if inner_result.status == ImportStatus.SUCCESS else 0
                except Exception as exc:
                    errors.append(
                        ImportError(
                            row=None,
                            field=name,
                            message=str(exc),
                            value=None,
                        )
                    )

            status = ImportStatus.SUCCESS if not errors else ImportStatus.PARTIAL
            return ImportResult(
                status=status,
                total_count=len(file_names),
                success_count=success_count,
                failed_count=len(errors),
                data=results,
                errors=errors,
            )
