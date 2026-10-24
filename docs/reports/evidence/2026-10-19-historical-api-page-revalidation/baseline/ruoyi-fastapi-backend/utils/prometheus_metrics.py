"""
Minimal Prometheus text-format metrics registry.

This module keeps request counters/histograms in-memory and renders
Prometheus-compatible exposition text without extra dependencies.
"""
import threading
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple


_DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)


def _escape_label(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def format_metric_line(name: str, value, labels: Optional[Dict[str, str]] = None) -> str:
    if labels:
        label_str = ",".join(f'{label}="{_escape_label(label_value)}"' for label, label_value in sorted(labels.items()))
        return f"{name}{{{label_str}}} {value}"
    return f"{name} {value}"


class PrometheusMetricsRegistry:
    def __init__(self, buckets: Optional[Iterable[float]] = None) -> None:
        bucket_values = tuple(sorted(float(item) for item in (buckets or _DEFAULT_BUCKETS)))
        self._buckets = bucket_values
        self._lock = threading.Lock()

        self._http_requests_total = defaultdict(int)  # (method, path, status_code) -> count
        self._http_errors_total = defaultdict(int)  # (method, path, status_code) -> count
        self._http_duration_sum = defaultdict(float)  # (method, path) -> sum seconds
        self._http_duration_count = defaultdict(int)  # (method, path) -> count
        self._http_duration_buckets = defaultdict(
            lambda: [0 for _ in range(len(self._buckets))]
        )  # (method, path) -> cumulative bucket counts

    def observe_http_request(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        method_value = str(method or "UNKNOWN").upper()
        path_value = str(path or "/")
        status_value = str(int(status_code))

        key = (method_value, path_value, status_value)
        duration_key = (method_value, path_value)
        duration_value = max(0.0, float(duration_seconds))

        with self._lock:
            self._http_requests_total[key] += 1
            if int(status_code) >= 400:
                self._http_errors_total[key] += 1

            self._http_duration_sum[duration_key] += duration_value
            self._http_duration_count[duration_key] += 1
            cumulative_buckets = self._http_duration_buckets[duration_key]
            for idx, bucket in enumerate(self._buckets):
                if duration_value <= bucket:
                    cumulative_buckets[idx] += 1

    def render_http_metrics(self) -> str:
        with self._lock:
            http_requests_total = dict(self._http_requests_total)
            http_errors_total = dict(self._http_errors_total)
            http_duration_sum = dict(self._http_duration_sum)
            http_duration_count = dict(self._http_duration_count)
            http_duration_buckets = {
                key: list(value) for key, value in self._http_duration_buckets.items()
            }

        lines: List[str] = []
        lines.append("# HELP http_requests_total Total number of HTTP requests.")
        lines.append("# TYPE http_requests_total counter")
        for (method, path, status_code), count in sorted(http_requests_total.items()):
            lines.append(
                format_metric_line(
                    "http_requests_total",
                    count,
                    labels={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                    },
                )
            )

        lines.append("# HELP http_request_errors_total Total number of HTTP error responses.")
        lines.append("# TYPE http_request_errors_total counter")
        for (method, path, status_code), count in sorted(http_errors_total.items()):
            lines.append(
                format_metric_line(
                    "http_request_errors_total",
                    count,
                    labels={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                    },
                )
            )

        lines.append("# HELP http_request_duration_seconds HTTP request duration in seconds.")
        lines.append("# TYPE http_request_duration_seconds histogram")
        for (method, path), count in sorted(http_duration_count.items()):
            cumulative_buckets = http_duration_buckets.get((method, path), [0 for _ in range(len(self._buckets))])
            for idx, bucket in enumerate(self._buckets):
                lines.append(
                    format_metric_line(
                        "http_request_duration_seconds_bucket",
                        cumulative_buckets[idx],
                        labels={
                            "method": method,
                            "path": path,
                            "le": str(bucket),
                        },
                    )
                )
            lines.append(
                format_metric_line(
                    "http_request_duration_seconds_bucket",
                    count,
                    labels={
                        "method": method,
                        "path": path,
                        "le": "+Inf",
                    },
                )
            )
            lines.append(
                format_metric_line(
                    "http_request_duration_seconds_sum",
                    f"{http_duration_sum.get((method, path), 0.0):.6f}",
                    labels={
                        "method": method,
                        "path": path,
                    },
                )
            )
            lines.append(
                format_metric_line(
                    "http_request_duration_seconds_count",
                    count,
                    labels={
                        "method": method,
                        "path": path,
                    },
                )
            )

        return "\n".join(lines) + "\n"

