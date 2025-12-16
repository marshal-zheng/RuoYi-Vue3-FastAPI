"""
通用批量动作执行器

提供可插拔的批量执行能力，适用于批量删除等幂等型后台操作。
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple


Handler = Callable[..., Awaitable[Any]]


@dataclass
class BatchActionTask:
    """
    批量任务描述
    """

    id: Any
    handler: Handler
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    timeout: Optional[float] = None  # 秒
    max_retries: int = 0
    retry_backoff_base: float = 0.5  # 秒，指数回退基础
    dedup_key: Optional[str] = None  # 用于幂等去重


@dataclass
class BatchActionResult:
    """
    单个任务执行结果
    """

    id: Any
    success: bool
    data: Any = None
    error: Optional[str] = None
    attempts: int = 1


@dataclass
class BatchActionSummary:
    """
    批量任务汇总
    """

    success: List[BatchActionResult]
    failed: List[BatchActionResult]

    def as_dict(self) -> Dict[str, Any]:
        return {
            'success': [r.__dict__ for r in self.success],
            'failed': [r.__dict__ for r in self.failed],
        }


class BatchActionExecutor:
    """
    批量执行器：并发执行任务，保证失败不影响其他任务

    - 时间复杂度 O(n)，空间 O(n) 保存结果
    - 可配置并发度，防止对数据库或外部接口的瞬时压力
    """

    def __init__(self, concurrency: int = 4, enable_dedup: bool = True):
        if concurrency <= 0:
            raise ValueError('concurrency must be greater than 0')
        self._semaphore = asyncio.Semaphore(concurrency)
        self._enable_dedup = enable_dedup

    async def run(self, tasks: List[BatchActionTask]) -> BatchActionSummary:
        if not tasks:
            raise ValueError('tasks 不能为空')

        dedup_seen: set[str] = set()

        async def _execute(task: BatchActionTask) -> BatchActionResult:
            async with self._semaphore:
                # 幂等去重：同 dedup_key 只执行一次，其他视为成功跳过
                if self._enable_dedup and task.dedup_key:
                    if task.dedup_key in dedup_seen:
                        return BatchActionResult(id=task.id, success=True, data='SKIPPED_DUP', attempts=0)
                    dedup_seen.add(task.dedup_key)

                attempt = 0
                while True:
                    attempt += 1
                    try:
                        coro = task.handler(*task.args, **task.kwargs)
                        if task.timeout and task.timeout > 0:
                            data = await asyncio.wait_for(coro, timeout=task.timeout)
                        else:
                            data = await coro
                        return BatchActionResult(id=task.id, success=True, data=data, attempts=attempt)
                    except Exception as exc:  # noqa: BLE001
                        if attempt > task.max_retries:
                            return BatchActionResult(
                                id=task.id,
                                success=False,
                                error=str(exc),
                                attempts=attempt,
                            )
                        # 指数退避 + 抖动
                        backoff = task.retry_backoff_base * (2 ** (attempt - 1))
                        backoff = backoff * (0.8 + 0.4 * random.random())
                        await asyncio.sleep(backoff)

        results = await asyncio.gather(*(_execute(t) for t in tasks))
        success = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        return BatchActionSummary(success=success, failed=failed)
