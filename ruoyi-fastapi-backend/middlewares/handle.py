from fastapi import FastAPI
from config.env import LogConfig
from middlewares.rate_limit_middleware import add_rate_limit_middleware
from middlewares.idempotency_middleware import add_idempotency_middleware
from middlewares.prometheus_middleware import add_prometheus_metrics_middleware
from middlewares.request_logging_middleware import add_request_logging_middleware
from middlewares.cors_middleware import add_cors_middleware
from middlewares.gzip_middleware import add_gzip_middleware
from middlewares.audit_context_middleware import AuditContextMiddleware
from middlewares.trace_middleware import add_trace_middleware
from resilience.degradation import add_degradation_header_middleware


def handle_middleware(app: FastAPI):
    """
    全局中间件处理
    """
    # 加载限流中间件（最内层，避免高频请求穿透到业务层）
    add_rate_limit_middleware(app)
    # 加载幂等中间件（需在 CORS/Gzip 内侧，确保回放响应也经过外层通用中间件）
    add_idempotency_middleware(app)
    # 加载跨域中间件
    add_cors_middleware(app)
    # 加载gzip压缩中间件
    add_gzip_middleware(app)
    # 加载审计上下文中间件（需在trace中间件之前）
    app.add_middleware(AuditContextMiddleware)
    # 加载trace中间件
    add_trace_middleware(app)
    # 加载降级标识中间件（在响应头附加 X-Degraded-Services）
    add_degradation_header_middleware(app)
    # 加载 Prometheus 请求指标中间件（跳过 /metrics 避免自采集噪音）
    add_prometheus_metrics_middleware(app, exclude_paths=('/metrics',))
    # 加载请求日志中间件（放在最外层，记录最终响应状态与整体耗时）
    if LogConfig.request_logging_enabled:
        add_request_logging_middleware(app)
