"""
协议导入/导出业务适配器

保持现有协议模板与解析逻辑不变，仅包装统一的返回结构，方便在业务侧复用。
"""
from urllib.parse import quote
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from utils.io_toolkit import ExportResult, ImportResult, ImportStatus
from module_admin.service.protocol_service import ProtocolService


class ProtocolIOAdapter:
    """
    协议导入导出适配层：不改变模板生成与解析细节，只包装成统一的 Result 结构。
    """

    @staticmethod
    async def export_protocol_excel(query_db: AsyncSession, protocol_id: int) -> ExportResult:
        raw = await ProtocolService.export_protocol_config_services(query_db, protocol_id)
        protocol_name = raw.get('protocol_name', '协议配置')
        filename = f'{protocol_name}_配置.xlsx'
        content = raw.get('content')
        if not content:
            raise ValueError('协议导出内容为空')
        return ExportResult(
            content=content,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            size=len(content),
        )

    @staticmethod
    async def export_import_template(protocol_type: Optional[str] = None) -> ExportResult:
        template_bytes = await ProtocolService.get_protocol_import_template_services(protocol_type)
        suffix = f'_{protocol_type.upper()}' if protocol_type else ''
        filename = f'协议导入模板{suffix}.xlsx'
        return ExportResult(
            content=template_bytes,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            size=len(template_bytes or b''),
        )

    @staticmethod
    async def import_preview(file: UploadFile) -> ImportResult:
        """
        复用现有解析逻辑，包装成 ImportResult，保持数据与错误表现不变。
        """
        preview = await ProtocolService.protocol_import_preview_services(file)
        return ImportResult(
            status=ImportStatus.SUCCESS,
            total_count=1,
            success_count=1,
            failed_count=0,
            data=preview,
            errors=[],
        )
