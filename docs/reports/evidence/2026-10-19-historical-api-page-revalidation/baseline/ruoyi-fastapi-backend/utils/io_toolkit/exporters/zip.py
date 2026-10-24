import io
from typing import List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from ..exceptions import ExportException
from ..models import ExportResult, ZipEntry
from .base import ExportStrategy


class ZipExporter(ExportStrategy):
    """ZIP打包导出器"""

    def __init__(self, compression: int = ZIP_DEFLATED):
        self.compression = compression

    @property
    def content_type(self) -> str:
        return 'application/zip'

    @property
    def file_extension(self) -> str:
        return '.zip'

    async def export(
        self,
        entries: List[ZipEntry],
        filename: Optional[str] = None,
        **options,
    ) -> ExportResult:
        if not entries:
            raise ExportException('打包内容为空')

        buffer = io.BytesIO()
        with ZipFile(buffer, 'w', compression=self.compression) as zip_file:
            for entry in entries:
                zip_file.writestr(
                    entry.filename,
                    entry.content,
                    compress_type=entry.compress_type or self.compression,
                )

        content = buffer.getvalue()
        safe_filename = filename or 'export'
        if not safe_filename.endswith(self.file_extension):
            safe_filename = f'{safe_filename}{self.file_extension}'

        return ExportResult(
            content=content,
            filename=safe_filename,
            content_type=self.content_type,
            size=len(content),
        )
