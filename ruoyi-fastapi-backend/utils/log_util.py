import os
import sys
import time
from typing import Any, Dict

from loguru import logger as _logger

from config.env import LogConfig
from middlewares.trace_middleware import TraceCtx


class LoggerInitializer:
    def __init__(self):
        self.log_path = os.path.join(os.getcwd(), 'logs')
        self.__ensure_log_directory_exists()
        self.log_path_error = os.path.join(self.log_path, f'{time.strftime("%Y-%m-%d")}_error.log')

    def __ensure_log_directory_exists(self):
        """
        确保日志目录存在，如果不存在则创建
        """
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)

    @staticmethod
    def __patch_record(log_record: Dict[str, Any]):
        """
        自定义日志补丁，注入 request_id / trace_id
        """
        trace_id = LoggerInitializer._resolve_trace_id() or ''
        extra = log_record.get('extra', {})
        extra.setdefault('trace_id', trace_id)
        extra.setdefault('request_id', TraceCtx.get_request_id() or trace_id)
        log_record['extra'] = extra

    @staticmethod
    def _resolve_trace_id() -> str:
        """Prefer OpenTelemetry trace id when current span is available."""
        try:
            from opentelemetry import trace as otel_trace

            span = otel_trace.get_current_span()
            context = span.get_span_context() if span is not None else None
            if context is not None and getattr(context, 'is_valid', False):
                trace_id = format(int(context.trace_id), '032x')
                if trace_id and trace_id != '0' * 32:
                    return trace_id
        except Exception:
            pass
        return TraceCtx.get_trace_id() or TraceCtx.get_request_id() or ''

    def init_log(self):
        """
        初始化日志配置
        """
        _logger.remove()
        _logger.configure(patcher=self.__patch_record)

        if LogConfig.log_json_enabled:
            # 结构化日志：stdout 与文件均输出 JSON，便于采集和查询。
            _logger.add(
                sys.stderr,
                level=LogConfig.log_level,
                serialize=True,
                enqueue=True,
            )
            _logger.add(
                self.log_path_error,
                level=LogConfig.log_error_file_level,
                serialize=True,
                rotation=LogConfig.log_error_rotation,
                encoding='utf-8',
                enqueue=True,
                compression=LogConfig.log_error_compression,
            )
            return _logger

        # 兼容模式：保留可读文本日志格式。
        format_str = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
            '<cyan>{extra[trace_id]}</cyan> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        )
        _logger.add(sys.stderr, level=LogConfig.log_level, format=format_str, enqueue=True)
        _logger.add(
            self.log_path_error,
            level=LogConfig.log_error_file_level,
            format=format_str,
            rotation=LogConfig.log_error_rotation,
            encoding='utf-8',
            enqueue=True,
            compression=LogConfig.log_error_compression,
        )

        return _logger


# 初始化日志处理器
log_initializer = LoggerInitializer()
logger = log_initializer.init_log()
