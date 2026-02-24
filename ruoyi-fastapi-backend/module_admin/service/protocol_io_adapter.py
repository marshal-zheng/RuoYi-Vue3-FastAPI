"""
协议导入/导出业务适配器

保持现有协议模板与解析逻辑不变，仅包装统一的返回结构，方便在业务侧复用。
"""
from typing import Optional

from fastapi import UploadFile

from utils.io_toolkit import ExportResult, ImportResult, ImportStatus
from ports import IProtocolService


class ProtocolIOAdapter:
    """
    协议导入导出适配层：不改变模板生成与解析细节，只包装成统一的 Result 结构。
    """

    def __init__(self, protocol_service: IProtocolService):
        self.protocol_service = protocol_service

    async def export_protocol_excel(self, protocol_id: int) -> ExportResult:
        raw = await self.protocol_service.export_protocol_config_services(protocol_id)
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

    async def export_import_template(self, protocol_type: Optional[str] = None) -> ExportResult:
        template_bytes = await self.protocol_service.get_protocol_import_template_services(protocol_type)
        suffix = f'_{protocol_type.upper()}' if protocol_type else ''
        filename = f'协议导入模板{suffix}.xlsx'
        return ExportResult(
            content=template_bytes,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            size=len(template_bytes or b''),
        )

    async def import_preview(self, file: UploadFile) -> ImportResult:
        """
        复用现有解析逻辑，包装成 ImportResult，保持数据与错误表现不变。
        """
        preview = await self.protocol_service.protocol_import_preview_services(file)
        return ImportResult(
            status=ImportStatus.SUCCESS,
            total_count=1,
            success_count=1,
            failed_count=0,
            data=preview,
            errors=[],
        )

    async def import_protocol(
        self,
        file: UploadFile,
        protocol_name: Optional[str],
        operator: str,
    ) -> ImportResult:
        """
        导入协议配置，创建新协议

        :param file: 上传的Excel文件
        :param protocol_name: 协议名称（可选）
        :param operator: 操作人
        :return: ImportResult
        """
        result = await self.protocol_service.import_protocol_services(file, protocol_name, operator)
        return ImportResult(
            status=ImportStatus.SUCCESS if result.is_success else ImportStatus.FAILED,
            total_count=1,
            success_count=1 if result.is_success else 0,
            failed_count=0 if result.is_success else 1,
            data=result.result,
            errors=[] if result.is_success else [result.message],
        )

    async def import_protocol_batch(
        self,
        files: list[UploadFile],
        operator: str,
    ) -> ImportResult:
        """
        批量导入协议配置
        """
        batch_result = await self.protocol_service.import_protocol_batch_services(files=files, operator=operator)
        return batch_result
