#!/usr/bin/env python3
"""Benchmark DI container resolution overhead against direct provider calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from container import build_container, validate_container_bindings

DEFAULT_SERVICES = (
    'common_service',
    'config_service',
    'dept_service',
    'dict_data_service',
    'dict_type_service',
    'user_service',
    'menu_service',
    'role_service',
    'job_service',
    'audit_log_service',
)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(round(0.95 * (len(sorted_values) - 1)))
    return sorted_values[index]


def _measure_us(fn: Callable[[], object], iterations: int) -> list[float]:
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - started) * 1_000_000.0)
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description='Benchmark DI resolution overhead.')
    parser.add_argument('--iterations', type=int, default=20000, help='Number of iterations per service.')
    parser.add_argument('--warmup', type=int, default=1000, help='Warmup iterations.')
    parser.add_argument(
        '--services',
        nargs='*',
        default=list(DEFAULT_SERVICES),
        help='Service provider names to benchmark.',
    )
    args = parser.parse_args()

    container = build_container()
    validate_container_bindings(container)

    benchmark_session = object()

    for _ in range(args.warmup):
        container.resolve_service(args.services[0], benchmark_session)

    result: dict[str, object] = {
        'iterations': args.iterations,
        'warmup': args.warmup,
        'services': {},
    }
    service_overhead_pct: list[float] = []
    service_overhead_us: list[float] = []

    for service_name in args.services:
        provider = container._service_factories[service_name]  # noqa: SLF001

        direct_samples = _measure_us(lambda: provider(benchmark_session), args.iterations)
        resolve_samples = _measure_us(
            lambda: container.resolve_service(service_name, benchmark_session),
            args.iterations,
        )

        direct_p95 = _p95(direct_samples)
        resolve_p95 = _p95(resolve_samples)
        overhead_us = resolve_p95 - direct_p95
        overhead_pct = (overhead_us / direct_p95 * 100.0) if direct_p95 else 0.0

        service_overhead_pct.append(overhead_pct)
        service_overhead_us.append(overhead_us)

        result['services'][service_name] = {
            'direct_p95_us': round(direct_p95, 3),
            'resolve_p95_us': round(resolve_p95, 3),
            'overhead_p95_us': round(overhead_us, 3),
            'overhead_p95_pct': round(overhead_pct, 3),
        }

    result['summary'] = {
        'avg_overhead_p95_us': round(statistics.mean(service_overhead_us), 3),
        'max_overhead_p95_us': round(max(service_overhead_us), 3),
        'avg_overhead_p95_pct': round(statistics.mean(service_overhead_pct), 3),
        'max_overhead_p95_pct': round(max(service_overhead_pct), 3),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

