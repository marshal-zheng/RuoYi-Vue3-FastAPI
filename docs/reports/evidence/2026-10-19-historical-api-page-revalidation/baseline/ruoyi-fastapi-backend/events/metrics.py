"""Event subsystem metrics and Prometheus renderer."""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from utils.prometheus_metrics import format_metric_line


class EventMetrics:
    """In-memory metrics for event dispatch and consumption."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._dispatch_success: dict[str, int] = defaultdict(int)
        self._dispatch_failure: dict[str, int] = defaultdict(int)
        self._retry_total: dict[str, int] = defaultdict(int)
        self._handler_success: dict[tuple[str, str], int] = defaultdict(int)
        self._handler_failure: dict[tuple[str, str], int] = defaultdict(int)

    def record_dispatch_success(self, event_type: str) -> None:
        with self._lock:
            self._dispatch_success[event_type] += 1

    def record_dispatch_failure(self, event_type: str) -> None:
        with self._lock:
            self._dispatch_failure[event_type] += 1

    def record_retry(self, event_type: str) -> None:
        with self._lock:
            self._retry_total[event_type] += 1

    def record_handler_success(self, event_type: str, handler_name: str) -> None:
        with self._lock:
            self._handler_success[(event_type, handler_name)] += 1

    def record_handler_failure(self, event_type: str, handler_name: str) -> None:
        with self._lock:
            self._handler_failure[(event_type, handler_name)] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                'dispatch_success': dict(self._dispatch_success),
                'dispatch_failure': dict(self._dispatch_failure),
                'retry_total': dict(self._retry_total),
                'handler_success': dict(self._handler_success),
                'handler_failure': dict(self._handler_failure),
            }

    def render_prometheus(self, *, backlog: int, lag_seconds: float) -> str:
        snapshot = self.snapshot()
        lines: list[str] = [
            '# HELP event_outbox_backlog Number of outbox events waiting for publish.',
            '# TYPE event_outbox_backlog gauge',
            format_metric_line('event_outbox_backlog', max(int(backlog), 0)),
            '# HELP event_outbox_lag_seconds Age of oldest pending/retry/manual event in seconds.',
            '# TYPE event_outbox_lag_seconds gauge',
            format_metric_line('event_outbox_lag_seconds', f'{max(float(lag_seconds), 0.0):.6f}'),
            '# HELP event_dispatch_success_total Total successfully dispatched events.',
            '# TYPE event_dispatch_success_total counter',
        ]

        for event_type, count in sorted(snapshot['dispatch_success'].items()):
            lines.append(format_metric_line('event_dispatch_success_total', count, labels={'event_type': event_type}))

        lines.extend(
            [
                '# HELP event_dispatch_failure_total Total failed dispatch events.',
                '# TYPE event_dispatch_failure_total counter',
            ]
        )
        for event_type, count in sorted(snapshot['dispatch_failure'].items()):
            lines.append(format_metric_line('event_dispatch_failure_total', count, labels={'event_type': event_type}))

        lines.extend(
            [
                '# HELP event_dispatch_retry_total Total dispatch retries.',
                '# TYPE event_dispatch_retry_total counter',
            ]
        )
        for event_type, count in sorted(snapshot['retry_total'].items()):
            lines.append(format_metric_line('event_dispatch_retry_total', count, labels={'event_type': event_type}))

        lines.extend(
            [
                '# HELP event_handler_success_total Total successful handler executions.',
                '# TYPE event_handler_success_total counter',
            ]
        )
        for (event_type, handler_name), count in sorted(snapshot['handler_success'].items()):
            lines.append(
                format_metric_line(
                    'event_handler_success_total',
                    count,
                    labels={'event_type': event_type, 'handler': handler_name},
                )
            )

        lines.extend(
            [
                '# HELP event_handler_failure_total Total failed handler executions.',
                '# TYPE event_handler_failure_total counter',
            ]
        )
        for (event_type, handler_name), count in sorted(snapshot['handler_failure'].items()):
            lines.append(
                format_metric_line(
                    'event_handler_failure_total',
                    count,
                    labels={'event_type': event_type, 'handler': handler_name},
                )
            )

        return '\n'.join(lines) + '\n'
