from contextlib import asynccontextmanager
import os
import sys
from fastapi import FastAPI
from config.env import AppConfig, CacheConfig, AuditConfig
from config.get_db import init_create_table
from config.get_redis import RedisUtil
from config.get_scheduler import SchedulerUtil
from config.database import async_engine
from exceptions.handle import handle_exception
from middlewares.handle import handle_middleware
from utils.query_monitor import (
    QueryPerformanceMonitor,
    ConnectionPoolMonitor,
    EnhancedQueryPerformanceMonitor,
    ConnectionPoolHealthChecker,
)
from utils.query_cache import init_query_cache
from utils.count_cache import init_count_cache
from utils.audit_logger import init_audit_logger
from module_admin.controller.cache_controller import cacheController
from module_admin.controller.audit_controller import auditController
from module_admin.controller.captcha_controller import captchaController
from module_admin.controller.common_controller import commonController
from module_admin.controller.config_controller import configController
from module_admin.controller.dept_controller import deptController
from module_admin.controller.dict_controller import dictController
from module_admin.controller.log_controller import logController
from module_admin.controller.login_controller import loginController
from module_admin.controller.job_controller import jobController
from module_admin.controller.menu_controller import menuController
from module_admin.controller.notice_controller import noticeController
from module_admin.controller.online_controller import onlineController
from module_admin.controller.post_controller import postController
from module_admin.controller.project_controller import projectController
from module_admin.controller.project_version_controller import projectVersionController
from module_admin.controller.protocol_controller import protocolController
from module_admin.controller.simulation_controller import simulationController
from module_admin.controller.device_category_controller import deviceCategoryController
from module_admin.controller.device_controller import deviceController
from module_admin.controller.role_controller import roleController
from module_admin.controller.server_controller import serverController
from module_admin.controller.user_controller import userController
from module_generator.controller.gen_controller import genController
from sub_applications.handle import handle_sub_applications
from utils.common_util import worship
from utils.log_util import logger
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


class DummyRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ex=None):
        self._store[key] = value
        return True

    async def setex(self, key, ttl, value):
        self._store[key] = value
        return True

    async def delete(self, key):
        self._store.pop(key, None)
        return True

    async def exists(self, key):
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
    await init_create_table()
    
    # 初始化查询性能监控
    query_monitor.setup(async_engine)
    pool_monitor.setup(async_engine)
    logger.info('查询性能监控已启用')
    
    if _is_test_env():
        app.state.redis = DummyRedis()
    else:
        app.state.redis = await RedisUtil.create_redis_pool()
        await RedisUtil.init_sys_dict(app.state.redis)
        await RedisUtil.init_sys_config(app.state.redis)
        await SchedulerUtil.init_system_scheduler()

    # 初始化查询缓存（使用 Redis 连接，默认 TTL 5 分钟）
    query_cache = init_query_cache(
        redis_client=app.state.redis if CacheConfig.query_cache_enabled else None,
        default_ttl=CacheConfig.query_cache_default_ttl,
        key_prefix='query_cache',
        is_async=True
    )
    app.state.query_cache = query_cache
    if CacheConfig.query_cache_enabled:
        logger.info('查询缓存已启用')
    else:
        logger.info('查询缓存已禁用')

    # 初始化 COUNT 缓存（独立于查询缓存，用于缓存分页总数）
    count_cache = init_count_cache(
        redis_client=app.state.redis if CacheConfig.count_cache_enabled else None,
        default_ttl=CacheConfig.count_cache_default_ttl,
        key_prefix=CacheConfig.count_cache_key_prefix,
        enabled=CacheConfig.count_cache_enabled
    )
    app.state.count_cache = count_cache
    if CacheConfig.count_cache_enabled:
        logger.info('COUNT 缓存已启用')
    else:
        logger.info('COUNT 缓存已禁用')

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
    
    logger.info(f'{AppConfig.app_name}启动成功')
    yield
    
    # 打印查询统计信息（可选）
    logger.info('查询性能统计:')
    stats = query_monitor.get_stats()
    logger.info(f'  总查询数: {stats["total_queries"]}')
    logger.info(f'  慢查询数: {stats["slow_queries"]}')
    logger.info(f'  慢查询占比: {stats["slow_query_rate"]:.2f}%')
    
    if _is_test_env():
        if getattr(app.state, 'redis', None) is not None:
            await app.state.redis.close()
    else:
        await RedisUtil.close_redis_pool(app)
        await SchedulerUtil.close_system_scheduler()


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


# 健康检查
@app.get('/health', tags=['健康检查'])
async def health_check():
    return ResponseUtil.success(data={'status': 'ok', 'app': AppConfig.app_name, 'version': AppConfig.app_version})


@app.get('/ready', tags=['健康检查'])
async def readiness_check():
    is_ready = all(
        [
            getattr(app.state, 'redis', None) is not None,
            getattr(app.state, 'query_monitor', None) is not None,
            getattr(app.state, 'pool_monitor', None) is not None,
        ]
    )
    if is_ready:
        return ResponseUtil.success(data={'status': 'ready'})
    return ResponseUtil.error(msg='服务未就绪', data={'status': 'not_ready'})


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


# 加载路由列表
controller_list = [
    {'router': loginController, 'tags': ['登录模块']},
    {'router': captchaController, 'tags': ['验证码模块']},
    {'router': userController, 'tags': ['系统管理-用户管理']},
    {'router': roleController, 'tags': ['系统管理-角色管理']},
    {'router': menuController, 'tags': ['系统管理-菜单管理']},
    {'router': deptController, 'tags': ['系统管理-部门管理']},
    {'router': postController, 'tags': ['系统管理-岗位管理']},
    {'router': dictController, 'tags': ['系统管理-字典管理']},
    {'router': configController, 'tags': ['系统管理-参数管理']},
    {'router': noticeController, 'tags': ['系统管理-通知公告管理']},
    {'router': logController, 'tags': ['系统管理-日志管理']},
    {'router': projectController, 'tags': ['工程管理']},
    {'router': projectVersionController, 'tags': ['工程管理-版本管理']},
    {'router': protocolController, 'tags': ['协议管理']},
    {'router': simulationController, 'tags': ['仿真管理']},
    {'router': deviceCategoryController, 'tags': ['设备中心-分类管理']},
    {'router': deviceController, 'tags': ['设备中心-设备管理']},
    {'router': onlineController, 'tags': ['系统监控-在线用户']},
    {'router': jobController, 'tags': ['系统监控-定时任务']},
    {'router': serverController, 'tags': ['系统监控-菜单管理']},
    {'router': cacheController, 'tags': ['系统监控-缓存监控']},
    {'router': auditController, 'tags': ['系统监控-审计日志']},
    {'router': commonController, 'tags': ['通用模块']},
    {'router': genController, 'tags': ['代码生成']},
]

for controller in controller_list:
    app.include_router(router=controller.get('router'), tags=controller.get('tags'))
