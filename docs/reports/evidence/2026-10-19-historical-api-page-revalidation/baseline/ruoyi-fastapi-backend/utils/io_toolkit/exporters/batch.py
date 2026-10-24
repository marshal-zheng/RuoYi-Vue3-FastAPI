"""
批量导出聚合器

在不改动现有导出策略的前提下，提供并发、安全的批量导出能力，并统一打包为 ZIP。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..exceptions import ExportException
from ..models import ExportResult, ZipEntry
from .base import ExportStrategy
from .zip import ZipExporter


@dataclass
class BatchExportTask:
    """
    单个导出任务描述
    """

    strategy: ExportStrategy
    data: Any
    filename: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchExportSummary:
    """
    批量导出结果摘要，可用于前端展示或日志记录
    """

    success: List[str]
    failed: List[Dict[str, str]]

    def as_dict(self) -> Dict[str, Any]:
        return {'success': self.success, 'failed': self.failed}


class BatchExporter:
    """
    批量导出器：并发执行多种 ExportStrategy，将结果打包为 ZIP

    - 复杂度：时间 O(n)，空间 O(total_bytes)；可通过限制并发降低峰值内存
    - 线程安全：通过 asyncio.Semaphore 控制并发，无全局可变状态
    - 可扩展：接受任意 ExportStrategy 实例，不侵入现有业务
    """

    def __init__(self, zip_exporter: Optional[ZipExporter] = None, concurrency: int = 4):
        if concurrency <= 0:
            raise ValueError('concurrency must be greater than 0')
        self.zip_exporter = zip_exporter or ZipExporter()
        self._semaphore = asyncio.Semaphore(concurrency)

    async def export(
        self,
        tasks: List[BatchExportTask],
        bundle_name: str = 'batch_export',
    ) -> tuple[ExportResult, BatchExportSummary]:
        if not tasks:
            raise ExportException('批量导出任务为空')

        async def _run_task(task: BatchExportTask):
            async with self._semaphore:
                return await self._safe_export(task)

        results = await asyncio.gather(*(_run_task(t) for t in tasks))

        entries: List[ZipEntry] = []
        failed: List[Dict[str, str]] = []
        success_names: List[str] = []

        for res in results:
            if res['result']:
                export_res: ExportResult = res['result']
                entries.append(
                    ZipEntry(
                        filename=export_res.filename,
                        content=export_res.content,
                        compress_type=None,
                    )
                )
                success_names.append(export_res.filename)
            else:
                failed.append({'filename': res['filename'], 'reason': res['error']})

        # 即便部分失败，也返回成功项的 ZIP，调用方可根据 summary 决定响应
        if not entries:
            raise ExportException('批量导出全部失败')

        bundle = await self.zip_exporter.export(entries, filename=bundle_name)
        summary = BatchExportSummary(success=success_names, failed=failed)
        return bundle, summary

    async def _safe_export(self, task: BatchExportTask):
        try:
            result = await task.strategy.export(task.data, filename=task.filename, **task.options)
            return {'filename': task.filename, 'result': result, 'error': None}
        except Exception as exc:  # noqa: BLE001
            return {'filename': task.filename, 'result': None, 'error': str(exc)}
