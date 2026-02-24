#!/usr/bin/env python3
"""Benchmark DI container bootstrap overhead (build + validate)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from container import build_container, validate_container_bindings
from utils.log_util import logger


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(round(0.95 * (len(sorted_values) - 1)))
    return sorted_values[index]


def main() -> int:
    parser = argparse.ArgumentParser(description='Benchmark DI container bootstrap overhead.')
    parser.add_argument('--iterations', type=int, default=40, help='Number of benchmark iterations.')
    parser.add_argument('--warmup', type=int, default=5, help='Warmup iterations.')
    args = parser.parse_args()

    # Keep benchmark output clean and avoid log noise skewing measurements.
    logger.remove()
    logger.add(sys.stderr, level='ERROR', serialize=False)

    for _ in range(args.warmup):
        container = build_container()
        validate_container_bindings(container)

    build_samples_ms: list[float] = []
    validate_samples_ms: list[float] = []
    total_samples_ms: list[float] = []

    for _ in range(args.iterations):
        started = time.perf_counter()
        container = build_container()
        build_done = time.perf_counter()
        validate_container_bindings(container)
        ended = time.perf_counter()

        build_samples_ms.append((build_done - started) * 1000.0)
        validate_samples_ms.append((ended - build_done) * 1000.0)
        total_samples_ms.append((ended - started) * 1000.0)

    result = {
        'iterations': args.iterations,
        'warmup': args.warmup,
        'build_ms': {
            'avg': round(statistics.mean(build_samples_ms), 3),
            'p95': round(_p95(build_samples_ms), 3),
            'max': round(max(build_samples_ms), 3),
        },
        'validate_ms': {
            'avg': round(statistics.mean(validate_samples_ms), 3),
            'p95': round(_p95(validate_samples_ms), 3),
            'max': round(max(validate_samples_ms), 3),
        },
        'total_ms': {
            'avg': round(statistics.mean(total_samples_ms), 3),
            'p95': round(_p95(total_samples_ms), 3),
            'max': round(max(total_samples_ms), 3),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
