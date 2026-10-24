import fnmatch
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from config.database import async_engine
from config.env import (
    AppConfig,
    AuditConfig,
    CacheConfig,
    DataBaseWorkflowConfig,
    DevManagedDataHotReconcileConfig,
)
from config.get_db import init_create_table
from container import (
    AppContainer,
    attach_container,
    build_container,
    initialize_container_runtime,
    shutdown_container_runtime,
    validate_container_bindings,
)
from events.runtime import EventSystemRuntime
from events.runtime_context import set_event_runtime
from exceptions.handle import handle_exception
from middlewares.handle import handle_middleware
from module_admin.service.simulation_runtime_state import init_simulation_runtime_state_store
from modules.system.application.services.capability_gate_service import invalidate_capability_gate_service
from modules.registry import (
    get_module_registry,
    initialize_module_extensions,
    log_loaded_modules,
    register_modules,
)
from modules.identity.application.services.security_token_service import SecurityTokenService
from modules.system.runtime import (
    DevManagedDataHotReconcileRuntime,
    DevMenuEventBroker,
    HotReconcileCallbackResult,
    is_dev_managed_data_hot_reconcile_enabled,
)
from resilience.runtime import build_resilience_runtime
from scripts.internal.db_workflow.managed_data_fast_reconcile_service import ManagedDataFastReconcileService
from sub_applications.handle import handle_sub_applications
from utils.audit_logger import init_audit_logger
from utils.common_util import worship
from utils.log_util import logger
from utils.otel_tracing import init_otel_tracing
from utils.prometheus_metrics import PrometheusMetricsRegistry, format_metric_line
from utils.query_monitor import (
    ConnectionPoolHealthChecker,
    ConnectionPoolMonitor,
    EnhancedQueryPerformanceMonitor,
)
from utils.response_util import ResponseUtil

# 初始化性能监控器（可选，生产环境可设置更高阈值或禁用）
# P1-008~012: 增强的性能监控
query_monitor = EnhancedQueryPerformanceMonitor(
    threshold_ms=200,
    log_all=False,
    n_plus_one_threshold=5  # P1-010: N+1 检测阈值
)
pool_monitor = ConnectionPoolMonitor()
pool_health_checker = ConnectionPoolHealthChecker(
    warning_threshold=0.8,
    critical_threshold=0.95
)

def _is_test_env() -> bool:
    return 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST') is not None


def _managed_data_hot_reconcile_change_count(report) -> int:
    return int(
        report.applied_operations
        + report.metadata_updated_objects
        + report.metadata_deactivated_objects
    )


def _log_managed_data_hot_reconcile_summary(report) -> None:
    logger.bind(
        event='dev_managed_data_hot_reconcile',
        trigger=report.trigger,
        duration_ms=report.duration_ms,
        success=report.success,
        change_count=_managed_data_hot_reconcile_change_count(report),
        error=report.error,
    ).log('INFO' if report.success else 'ERROR', 'dev_managed_data_hot_reconcile')


class DummyRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    async def setex(self, key, ttl, value):
        self._store[key] = value
        return True

    async def delete(self, *keys):
        if len(keys) == 1 and isinstance(keys[0], (list, tuple, set)):
            keys = tuple(keys[0])
        removed = 0
        for key in keys:
            if key in self._store:
                removed += 1
                self._store.pop(key, None)
        return removed

    async def keys(self, pattern='*'):
        return [key for key in self._store.keys() if fnmatch.fnmatch(key, pattern)]

    async def exists(self, key):
        return key in self._store

    async def rpush(self, key, *values):
        bucket = self._store.setdefault(key, [])
        if not isinstance(bucket, list):
            bucket = []
            self._store[key] = bucket
        bucket.extend(values)
        return len(bucket)

    async def lrange(self, key, start, end):
        bucket = self._store.get(key, [])
        if not isinstance(bucket, list):
            return []
        size = len(bucket)
        if size == 0:
            return []
        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)
        if start > end:
            return []
        return bucket[start : end + 1]

    async def llen(self, key):
        bucket = self._store.get(key, [])
        if not isinstance(bucket, list):
            return 0
        return len(bucket)

    async def ltrim(self, key, start, end):
        bucket = self._store.get(key, [])
        if not isinstance(bucket, list):
            return True
        size = len(bucket)
        if size == 0:
            return True
        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)
        if start > end:
            self._store[key] = []
            return True
        self._store[key] = bucket[start : end + 1]
        return True

    async def expire(self, key, ttl):
        return key in self._store

    async def ping(self):
        return True

    async def close(self):
        return True


# 生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'{AppConfig.app_name}开始启动')
    worship()
    # 仅初始化运行时数据库连接；非测试环境 schema 变更由 dev-sync/deploy 工作流负责。
    await init_create_table()
    init_otel_tracing(app=app, db_engine=async_engine)
    container = build_container()
    validate_container_bindings(container)
    attach_container(app, container)
    await initialize_module_extensions(container, MODULE_REGISTRY)
    
    # 初始化查询性能监控
    query_monitor.setup(async_engine)
    pool_monitor.setup(async_engine)
    logger.info('查询性能监控已启用')
    
    app.state.redis = await initialize_container_runtime(
        container,
        test_mode=_is_test_env(),
        test_redis_client=DummyRedis() if _is_test_env() else None,
    )
    app.state.security_token_service = SecurityTokenService(app.state.redis)

    app.state.sim_runtime_state = init_simulation_runtime_state_store(redis_client=app.state.redis)

    app.state.query_cache = container.query_cache
    if CacheConfig.query_cache_enabled:
        logger.info('查询缓存已启用')
    else:
        logger.info('查询缓存已禁用')

    app.state.resilience_runtime = build_resilience_runtime(redis_client=app.state.redis, db_engine=async_engine)

    app.state.event_runtime = EventSystemRuntime(
        container=container,
        poll_interval_seconds=1.0,
        max_batch_size=100,
        max_retry_count=6,
        backlog_alert_threshold=500,
    )
    await app.state.event_runtime.start()
    set_event_runtime(app.state.event_runtime)

    app.state.dev_menu_sync_runtime = None
    app.state.dev_managed_data_hot_reconcile_runtime = None
    app.state.dev_menu_event_broker = None
    app.state.dev_managed_data_hot_reconcile_event_broker = None
    if is_dev_managed_data_hot_reconcile_enabled():
        hot_reconcile_runtime: DevManagedDataHotReconcileRuntime | None = None
        event_broker = DevMenuEventBroker()

        async def _on_manifest_change(trigger, _snapshot, _diff):
            assert hot_reconcile_runtime is not None
            report = await ManagedDataFastReconcileService(redis_client=app.state.redis).reconcile(
                trigger=trigger,
                previous_compiled_checksum=hot_reconcile_runtime.state.last_applied_compiled_checksum,
            )
            _log_managed_data_hot_reconcile_summary(report)
            event_id = None
            if report.success and report.skipped_reason != 'compiled_checksum_unchanged':
                invalidate_capability_gate_service(app)
            if report.success and report.menu_reload_required:
                event_id = event_broker.publish_menu_changed(
                    trigger=report.trigger,
                    compiled_checksum=report.compiled_checksum or None,
                    synced_at=report.synced_at,
                )
            return HotReconcileCallbackResult(
                success=report.success,
                compiled_checksum=report.compiled_checksum or None,
                synced_at=report.synced_at,
                error=report.error,
                event_id=event_id,
            )

        hot_reconcile_runtime = DevManagedDataHotReconcileRuntime(on_manifest_change=_on_manifest_change)
        await hot_reconcile_runtime.start()
        app.state.dev_menu_sync_runtime = hot_reconcile_runtime
        app.state.dev_managed_data_hot_reconcile_runtime = hot_reconcile_runtime
        app.state.dev_menu_event_broker = event_broker
        app.state.dev_managed_data_hot_reconcile_event_broker = event_broker
        logger.info(
            '开发态受管数据热对齐运行时已启用（modules_root={}, watch_interval_ms={}, debounce_ms={}, '
            'retry_backoff_ms={}, retry_max_backoff_ms={}, sse_heartbeat_seconds={}）',
            hot_reconcile_runtime.modules_root,
            DevManagedDataHotReconcileConfig.dev_managed_data_watch_interval_ms,
            DevManagedDataHotReconcileConfig.dev_managed_data_debounce_ms,
            DevManagedDataHotReconcileConfig.dev_managed_data_retry_backoff_ms,
            DevManagedDataHotReconcileConfig.dev_managed_data_retry_max_backoff_ms,
            DevManagedDataHotReconcileConfig.dev_managed_data_sse_heartbeat_seconds,
        )
    else:
        logger.info(
            '开发态受管数据热对齐运行时未启用（APP_ENV={}, DB_WORKFLOW_MODE={}, enabled={}）',
            AppConfig.app_env,
            DataBaseWorkflowConfig.db_workflow_mode,
            DevManagedDataHotReconcileConfig.dev_managed_data_hot_reconcile_enabled,
        )

    # 初始化审计日志
    if AuditConfig.audit_enabled and not _is_test_env():
        init_audit_logger()
        logger.info('审计日志已启用')
    elif AuditConfig.audit_enabled and _is_test_env():
        logger.info('测试环境已禁用审计日志')
    
    # 将监控器挂载到 app.state 以便在其他地方访问
    app.state.query_monitor = query_monitor
    app.state.pool_monitor = pool_monitor
    app.state.pool_health_checker = pool_health_checker
    app.state.metrics_registry = PrometheusMetricsRegistry()
    
    log_loaded_modules(LOADED_MODULES)
    logger.info(f'{AppConfig.app_name}启动成功')
    yield
    
    # 打印查询统计信息（可选）
    logger.info('查询性能统计:')
    stats = query_monitor.get_stats()
    logger.info(f'  总查询数: {stats["total_queries"]}')
    logger.info(f'  慢查询数: {stats["slow_queries"]}')
    logger.info(f'  慢查询占比: {stats["slow_query_rate"]:.2f}%')
    
    app_container = getattr(app.state, 'container', None)
    event_runtime = getattr(app.state, 'event_runtime', None)
    hot_reconcile_runtime = getattr(app.state, 'dev_managed_data_hot_reconcile_runtime', None)
    dev_menu_event_broker = getattr(app.state, 'dev_menu_event_broker', None)
    if hot_reconcile_runtime is not None:
        await hot_reconcile_runtime.stop()
    if dev_menu_event_broker is not None:
        await dev_menu_event_broker.close()
    if event_runtime is not None:
        await event_runtime.stop()
        set_event_runtime(None)
    if isinstance(app_container, AppContainer):
        await shutdown_container_runtime(app_container)


# 初始化FastAPI对象
app = FastAPI(
    title=AppConfig.app_name,
    description=f'{AppConfig.app_name}接口文档',
    version=AppConfig.app_version,
    lifespan=lifespan,
)

# 挂载子应用
handle_sub_applications(app)
# 加载中间件处理方法
handle_middleware(app)
# 加载全局异常处理方法
handle_exception(app)
MODULE_REGISTRY = get_module_registry()
LOADED_MODULES = register_modules(app, MODULE_REGISTRY)


# 健康检查
@app.get('/health', tags=['健康检查'])
async def health_check():
    app_container = getattr(app.state, 'container', None)
    provider_summary = {}
    if isinstance(app_container, AppContainer):
        provider_summary = app_container.provider_health_summary()
    return ResponseUtil.success(
        data={
            'status': 'ok',
            'app': AppConfig.app_name,
            'version': AppConfig.app_version,
            'providers': provider_summary,
        }
    )


@app.get('/ready', tags=['健康检查'])
async def readiness_check():
    app_container = getattr(app.state, 'container', None)
    container_ready = isinstance(app_container, AppContainer) and app_container.is_runtime_ready()
    is_ready = all(
        [
            getattr(app.state, 'redis', None) is not None,
            getattr(app.state, 'query_monitor', None) is not None,
            getattr(app.state, 'pool_monitor', None) is not None,
            container_ready,
        ]
    )
    if is_ready:
        return ResponseUtil.success(data={'status': 'ready', 'containerReady': container_ready})
    return ResponseUtil.error(msg='服务未就绪', data={'status': 'not_ready', 'containerReady': container_ready})


@app.get('/health/db', tags=['健康检查'])
async def database_health_check():
    """
    P1-011: 数据库健康检查端点
    
    检查数据库连接池状态
    """
    health_checker = getattr(app.state, 'pool_health_checker', None)
    if not health_checker:
        return ResponseUtil.error(msg='健康检查器未初始化')
    
    health = health_checker.check_health(async_engine)
    
    if health['status'] == 'critical':
        return ResponseUtil.error(msg=health['message'], data=health)
    elif health['status'] == 'warning':
        return ResponseUtil.success(message=health['message'], data=health)
    else:
        return ResponseUtil.success(data=health)


@app.get('/health/deep', tags=['健康检查'])
async def deep_health_check():
    runtime = getattr(app.state, 'resilience_runtime', None)
    if runtime is None:
        return ResponseUtil.success(
            http_status=503,
            data={'status': 'unhealthy', 'detail': 'resilience_runtime_not_initialized'},
        )

    http_status, payload = await runtime.deep_health_checker.run()
    return ResponseUtil.success(http_status=http_status, data=payload)


@app.get('/health/events', tags=['健康检查'])
async def event_health_check():
    event_runtime = getattr(app.state, 'event_runtime', None)
    if event_runtime is None:
        return ResponseUtil.success(
            http_status=503,
            data={'status': 'unhealthy', 'detail': 'event_runtime_not_initialized'},
        )
    payload = await event_runtime.health()
    status = 'healthy' if payload.get('running') else 'degraded'
    return ResponseUtil.success(data={'status': status, **payload})


@app.get('/health/query-stats', tags=['健康检查'])
async def query_stats():
    """
    P1-008~010: 查询性能统计端点
    
    返回查询性能统计、慢查询和 N+1 检测结果
    """
    monitor = getattr(app.state, 'query_monitor', None)
    if not monitor:
        return ResponseUtil.error(msg='性能监控器未初始化')
    
    stats = monitor.get_stats()
    return ResponseUtil.success(data={
        'total_queries': stats['total_queries'],
        'slow_queries': stats['slow_queries'],
        'slow_query_rate': f"{stats['slow_query_rate']:.2f}%",
        'avg_time_ms': f"{stats['avg_time']:.2f}",
        'max_time_ms': f"{stats['max_time']:.2f}",
        'n_plus_one_detected': stats.get('n_plus_one_detected', 0),
        'n_plus_one_patterns': stats.get('n_plus_one_patterns', []),
        'recent_slow_queries': stats.get('recent_slow_queries', [])
    })


@app.get('/metrics', tags=['健康检查'], include_in_schema=False)
async def prometheus_metrics():
    """
    Prometheus 指标导出端点。

    输出请求计数/耗时指标，以及数据库/Redis 依赖健康指标。
    """
    metrics_registry = getattr(app.state, 'metrics_registry', None)
    request_metrics = ''
    if isinstance(metrics_registry, PrometheusMetricsRegistry):
        request_metrics = metrics_registry.render_http_metrics()

    lines = [request_metrics.rstrip('\n')] if request_metrics else []

    # 数据库依赖指标
    lines.extend(
        [
            '# HELP db_pool_size Database connection pool configured size.',
            '# TYPE db_pool_size gauge',
            '# HELP db_pool_checked_out Database connection pool checked out count.',
            '# TYPE db_pool_checked_out gauge',
            '# HELP db_pool_overflow Database connection pool overflow count.',
            '# TYPE db_pool_overflow gauge',
        ]
    )

    db_pool_size = 0
    db_pool_checked_out = 0
    db_pool_overflow = 0
    pool = getattr(async_engine, 'pool', None)
    if pool is not None:
        try:
            db_pool_size = int(pool.size())
            db_pool_checked_out = int(pool.checkedout())
            db_pool_overflow = int(pool.overflow())
        except Exception:
            pass

    lines.append(format_metric_line('db_pool_size', db_pool_size))
    lines.append(format_metric_line('db_pool_checked_out', db_pool_checked_out))
    lines.append(format_metric_line('db_pool_overflow', db_pool_overflow))

    # 数据库查询指标（来自查询监控器）
    lines.extend(
        [
            '# HELP db_queries_total Total database queries observed by monitor.',
            '# TYPE db_queries_total counter',
            '# HELP db_slow_queries_total Total slow database queries observed by monitor.',
            '# TYPE db_slow_queries_total counter',
            '# HELP db_query_avg_duration_ms Average database query duration in milliseconds.',
            '# TYPE db_query_avg_duration_ms gauge',
        ]
    )
    monitor = getattr(app.state, 'query_monitor', None)
    db_queries_total = 0
    db_slow_queries_total = 0
    db_query_avg_duration_ms = 0.0
    if monitor is not None:
        try:
            stats = monitor.get_stats()
            db_queries_total = int(stats.get('total_queries', 0))
            db_slow_queries_total = int(stats.get('slow_queries', 0))
            db_query_avg_duration_ms = float(stats.get('avg_time', 0.0))
        except Exception:
            pass
    lines.append(format_metric_line('db_queries_total', db_queries_total))
    lines.append(format_metric_line('db_slow_queries_total', db_slow_queries_total))
    lines.append(format_metric_line('db_query_avg_duration_ms', f'{db_query_avg_duration_ms:.6f}'))

    # Redis 依赖指标
    lines.extend(
        [
            '# HELP redis_up Redis health status (1=up, 0=down).',
            '# TYPE redis_up gauge',
        ]
    )
    redis_up = 0
    redis_client = getattr(app.state, 'redis', None)
    if redis_client is not None:
        try:
            pong = await redis_client.ping()
            redis_up = 1 if pong else 0
        except Exception:
            redis_up = 0
    lines.append(format_metric_line('redis_up', redis_up))

    # 弹性指标
    lines.extend(
        [
            '# HELP retry_attempt_total Total retry attempts triggered by resilience layer.',
            '# TYPE retry_attempt_total counter',
            '# HELP bulkhead_rejected_total Total requests rejected by bulkhead.',
            '# TYPE bulkhead_rejected_total counter',
            '# HELP saga_failed_total Total failed saga instances.',
            '# TYPE saga_failed_total counter',
            '# HELP circuit_breaker_state Circuit breaker state (OPEN=1, CLOSED/HALF_OPEN=0).',
            '# TYPE circuit_breaker_state gauge',
        ]
    )
    retry_attempt_total = 0
    bulkhead_rejected_total = 0
    saga_failed_total = 0
    runtime = getattr(app.state, 'resilience_runtime', None)
    if runtime is not None:
        resilience_counters = await runtime.metrics.snapshot()
        retry_attempt_total = int(resilience_counters.get('retry_attempt_total', 0))
        bulkhead_rejected_total = int(resilience_counters.get('bulkhead_rejected_total', 0))
        saga_instances = await runtime.saga_engine.list_instances(limit=500)
        saga_failed_total = sum(
            1
            for item in saga_instances
            if str(item.get('status')) in ('FAILED', 'FAILED_NEEDS_MANUAL_INTERVENTION')
        )
        circuit_states = await runtime.circuit_registry.list_snapshots()
        for item in circuit_states:
            state = str(item.get('state', 'CLOSED'))
            value = 1 if state == 'OPEN' else 0
            lines.append(
                format_metric_line(
                    'circuit_breaker_state',
                    value,
                    labels={
                        'name': str(item.get('name', 'unknown')),
                        'state': state,
                    },
                )
            )

    lines.append(format_metric_line('retry_attempt_total', retry_attempt_total))
    lines.append(format_metric_line('bulkhead_rejected_total', bulkhead_rejected_total))
    lines.append(format_metric_line('saga_failed_total', saga_failed_total))

    event_runtime = getattr(app.state, 'event_runtime', None)
    if event_runtime is not None:
        event_metrics_text = await event_runtime.render_metrics()
        lines.append(event_metrics_text.rstrip('\n'))

    body = '\n'.join(item for item in lines if item != '') + '\n'
    return Response(
        content=body,
        media_type='text/plain; version=0.0.4; charset=utf-8',
    )
