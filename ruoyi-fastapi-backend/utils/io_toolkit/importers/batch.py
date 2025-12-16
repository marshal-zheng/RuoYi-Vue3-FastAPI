"""
批量导入聚合器

在不影响现有业务导入实现的前提下，提供统一的批量处理、并发和结果汇总。
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from ..exceptions import ImportException
from ..models import ImportError, ImportResult, ImportStatus
from .base import ImportStrategy


@dataclass
class BatchImportSource:
    """
    待导入的单个文件源
    """

    filename: str
    content: bytes
    strategy: Optional[ImportStrategy] = None
    model: Optional[Type[BaseModel]] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchImportSummary:
    """
    批量导入摘要
    """

    success: List[Dict[str, Any]]
    failed: List[ImportError]

    def as_dict(self) -> Dict[str, Any]:
        return {'success': self.success, 'failed': [err.model_dump() for err in self.failed]}


class BatchImporter:
    """
    批量导入器：根据文件后缀自动选择 ImportStrategy，支持并发与统一结果汇总

    - 时间复杂度 O(n)；空间受文件总大小和模型校验结果影响
    - 可扩展：外部可注册/传入策略，不改动现有业务逻辑
    - 容错：单文件失败不影响整体，统一收敛错误
    """

    def __init__(self, strategies: List[ImportStrategy], concurrency: int = 4):
        if not strategies:
            raise ValueError('strategies 不能为空')
        if concurrency <= 0:
            raise ValueError('concurrency must be greater than 0')
        self._strategy_map = self._build_strategy_map(strategies)
        self._semaphore = asyncio.Semaphore(concurrency)

    def _build_strategy_map(self, strategies: List[ImportStrategy]) -> Dict[str, ImportStrategy]:
        mapping: Dict[str, ImportStrategy] = {}
        for strategy in strategies:
            for ext in strategy.supported_extensions:
                # 后注册的策略覆盖同后缀的旧策略，方便业务层自定义
                mapping[ext.lower()] = strategy
        return mapping

    def _select_strategy(self, filename: str, explicit: Optional[ImportStrategy]) -> ImportStrategy:
        if explicit:
            return explicit
        _, ext = os.path.splitext(filename or '')
        strategy = self._strategy_map.get(ext.lower())
        if not strategy:
            raise ImportException(f'不支持的文件类型: {ext or "未知"}')
        return strategy

    async def import_batch(
        self,
        sources: List[BatchImportSource],
    ) -> tuple[List[ImportResult], BatchImportSummary]:
        if not sources:
            raise ImportException('批量导入源为空')

        async def _run(source: BatchImportSource):
            async with self._semaphore:
                return await self._safe_import(source)

        results = await asyncio.gather(*(_run(s) for s in sources))

        successes: List[Dict[str, Any]] = []
        failed_errors: List[ImportError] = []

        for res in results:
            if res['result'] and res['result'].status != ImportStatus.FAILED:
                successes.append(
                    {
                        'filename': res['filename'],
                        'status': res['result'].status,
                        'total': res['result'].total_count,
                        'success': res['result'].success_count,
                        'failed': res['result'].failed_count,
                    }
                )
            else:
                failed_errors.append(res['error'])

        summary = BatchImportSummary(success=successes, failed=failed_errors)
        return [r['result'] for r in results if r['result']], summary

    async def _safe_import(self, source: BatchImportSource):
        filename = source.filename or 'unknown'
        try:
            strategy = self._select_strategy(filename, source.strategy)
            result = await strategy.import_data(
                source.content,
                model=source.model,
                **source.options,
            )
            return {'filename': filename, 'result': result, 'error': None}
        except Exception as exc:  # noqa: BLE001
            error = ImportError(row=None, field=filename, message=str(exc), value=None)
            return {'filename': filename, 'result': None, 'error': error}
