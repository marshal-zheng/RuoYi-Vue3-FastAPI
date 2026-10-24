import io
from typing import Dict, List, Optional, Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

from ..exceptions import ExportException
from ..models import ExportResult
from .base import ExportStrategy


class ExcelExporter(ExportStrategy):
    """Excel导出器：支持字段映射与简单表头样式"""

    def __init__(
        self,
        mapping_dict: Optional[Dict[str, str]] = None,
        sheet_name: str = 'Sheet1',
        header_style: Optional[Dict[str, Any]] = None,
    ):
        self.mapping_dict = mapping_dict or {}
        self.sheet_name = sheet_name
        self.header_style = header_style or {}

    @property
    def content_type(self) -> str:
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    @property
    def file_extension(self) -> str:
        return '.xlsx'

    async def export(
        self,
        data: List[Dict],
        filename: Optional[str] = None,
        **options,
    ) -> ExportResult:
        if data is None:
            raise ExportException('导出数据为空')

        # 应用字段映射：key -> label
        mapped_data = self._apply_mapping(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(mapped_data).to_excel(
                writer,
                index=False,
                sheet_name=self.sheet_name,
            )
            self._apply_header_style(writer)

        content = output.getvalue()
        safe_filename = filename or 'export'
        if not safe_filename.endswith(self.file_extension):
            safe_filename = f'{safe_filename}{self.file_extension}'

        return ExportResult(
            content=content,
            filename=safe_filename,
            content_type=self.content_type,
            size=len(content),
        )

    def _apply_mapping(self, data: List[Dict]) -> List[Dict]:
        if not self.mapping_dict:
            return data
        return [
            {self.mapping_dict.get(k, k): v for k, v in row.items() if k in self.mapping_dict or not self.mapping_dict}
            for row in data
        ]

    def _apply_header_style(self, writer: pd.ExcelWriter):
        if not self.header_style:
            return
        workbook = writer.book
        sheet = workbook[self.sheet_name]
        fill_color = self.header_style.get('fill_color', 'f2f2f2')
        bold = self.header_style.get('bold', True)
        align_center = self.header_style.get('align_center', True)

        fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
        font = Font(bold=bold)
        alignment = Alignment(horizontal='center') if align_center else None

        for cell in sheet[1]:
            cell.fill = fill
            cell.font = font
            if alignment:
                cell.alignment = alignment
