#!/usr/bin/env python3
"""Benchmark CQRS query dispatch overhead (direct handler vs mediator)."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.system.application.behaviors import build_default_query_behaviors  # noqa: E402
from modules.system.application.handler_registry import HandlerRegistry  # noqa: E402
from modules.system.application.mediator import Mediator  # noqa: E402
from utils.log_util import logger  # noqa: E402


class _BenchmarkQuery:
    __slots__ = ('request_id', 'trace_id')

    def __init__(self, trace_id: str = 'bench-trace', request_id: str = 'bench-request') -> None:
        self.trace_id = trace_id
        self.request_id = request_id


class _BenchmarkQueryHandler:
    async def handle(self, request: _BenchmarkQuery) -> dict[str, str]:
        return {'trace_id': request.trace_id, 'request_id': request.request_id}


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = round(0.95 * (len(sorted_values) - 1))
    return sorted_values[index]


async def _measure_us(
    fn,
    iterations: int,
) -> list[float]:
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        await fn()
        samples.append((time.perf_counter() - started) * 1_000_000.0)
    return samples


async def _benchmark(iterations: int, warmup: int) -> dict[str, Any]:
    handler = _BenchmarkQueryHandler()
    registry = HandlerRegistry()
    registry.register_query(_BenchmarkQuery, handler)

    mediator_plain = Mediator(registry, query_behaviors=())
    mediator_with_pipeline = Mediator(
        registry,
        query_behaviors=build_default_query_behaviors(),
    )

    query = _BenchmarkQuery()

    for _ in range(warmup):
        await handler.handle(query)
        await mediator_plain.query(query)
        await mediator_with_pipeline.query(query)

    direct_samples = await _measure_us(lambda: handler.handle(query), iterations)
    mediator_plain_samples = await _measure_us(lambda: mediator_plain.query(query), iterations)
    mediator_pipeline_samples = await _measure_us(lambda: mediator_with_pipeline.query(query), iterations)

    direct_p95 = _p95(direct_samples)
    mediator_plain_p95 = _p95(mediator_plain_samples)
    mediator_pipeline_p95 = _p95(mediator_pipeline_samples)

    plain_overhead_p95 = mediator_plain_p95 - direct_p95
    pipeline_overhead_p95 = mediator_pipeline_p95 - direct_p95
    pipeline_extra_over_plain_p95 = mediator_pipeline_p95 - mediator_plain_p95

    return {
        'iterations': iterations,
        'warmup': warmup,
        'samples_us': {
            'direct': {
                'avg': round(statistics.mean(direct_samples), 3),
                'p95': round(direct_p95, 3),
                'max': round(max(direct_samples), 3),
            },
            'mediator_plain': {
                'avg': round(statistics.mean(mediator_plain_samples), 3),
                'p95': round(mediator_plain_p95, 3),
                'max': round(max(mediator_plain_samples), 3),
            },
            'mediator_with_pipeline': {
                'avg': round(statistics.mean(mediator_pipeline_samples), 3),
                'p95': round(mediator_pipeline_p95, 3),
                'max': round(max(mediator_pipeline_samples), 3),
            },
        },
        'overhead_p95_us': {
            'mediator_plain_vs_direct': round(plain_overhead_p95, 3),
            'mediator_pipeline_vs_direct': round(pipeline_overhead_p95, 3),
            'mediator_pipeline_vs_plain': round(pipeline_extra_over_plain_p95, 3),
        },
        'overhead_p95_pct': {
            'mediator_plain_vs_direct': round((plain_overhead_p95 / direct_p95 * 100.0) if direct_p95 else 0.0, 3),
            'mediator_pipeline_vs_direct': round(
                (pipeline_overhead_p95 / direct_p95 * 100.0) if direct_p95 else 0.0,
                3,
            ),
            'mediator_pipeline_vs_plain': round(
                (pipeline_extra_over_plain_p95 / mediator_plain_p95 * 100.0) if mediator_plain_p95 else 0.0,
                3,
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Benchmark CQRS query dispatch overhead.')
    parser.add_argument('--iterations', type=int, default=20000, help='Number of benchmark iterations.')
    parser.add_argument('--warmup', type=int, default=1000, help='Warmup iterations.')
    args = parser.parse_args()

    # Keep benchmark output stable and avoid log I/O skew.
    logger.remove()
    logger.add(sys.stderr, level='ERROR', serialize=False)

    result = asyncio.run(_benchmark(iterations=args.iterations, warmup=args.warmup))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
