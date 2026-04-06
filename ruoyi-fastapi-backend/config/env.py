import argparse
import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """
    应用配置
    """

    app_env: str = 'dev'
    app_name: str = 'RuoYi-FasAPI'
    app_root_path: str = '/api'
    app_host: str = '0.0.0.0'
    app_port: int = 9099
    app_version: str = '1.0.0'
    app_reload: bool = True
    app_access_log: bool = False
    app_ip_location_query: bool = True
    app_same_time_login: bool = True


class DevMenuSyncSettings(BaseSettings):
    """
    开发态菜单热同步配置
    """

    dev_menu_sync: bool = False
    dev_menu_sync_poll_interval_seconds: float = 0.5
    dev_menu_sync_debounce_seconds: float = 0.2
    dev_menu_sync_auto_startup: bool = True


class JwtSettings(BaseSettings):
    """
    Jwt配置
    """

    jwt_secret_key: str = 'b01c66dc2c58dc6a0aabfe2144256be36226de378bf87f72c0c795dda67f4d55'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 1440
    jwt_redis_expire_minutes: int = 30


class SecuritySettings(BaseSettings):
    """
    安全硬切配置（JWT/CSRF/CSP/Origin）
    """

    security_hard_cut_mode: bool = True

    security_jwt_sign_algorithm: str = 'RS256'
    security_jwt_allowed_algorithms: str = 'RS256,EdDSA'
    security_jwt_issuer: str = 'ruoyi-fastapi'
    security_jwt_audience_api: str = 'ruoyi-api'
    security_jwt_audience_embed: str = 'ruoyi-embed'
    security_jwt_audience_ws: str = 'ruoyi-ws'
    security_jwt_private_key_pem: str = ''
    security_jwt_public_key_pem: str = ''
    security_jwt_max_expire_seconds: int = 600
    security_jwt_clock_skew_seconds: int = 60
    security_key_rotation_grace_seconds: int = 900
    security_refresh_expire_seconds: int = 604800
    security_access_cookie_name: str = 'ruoyi_at'
    security_refresh_cookie_name: str = 'ruoyi_rt'
    security_cookie_samesite: str = 'lax'

    security_m2m_expire_seconds: int = 600
    security_embed_access_expire_seconds: int = 300
    security_embed_grant_ttl_seconds: int = 60
    security_ws_ticket_ttl_seconds: int = 30

    security_allowed_origins: str = (
        'http://localhost,http://127.0.0.1,http://localhost:80,http://127.0.0.1:80,'
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3100,http://127.0.0.1:3100'
    )
    security_cors_allow_credentials: bool = False

    security_csrf_enabled: bool = True
    security_csrf_protected_paths: str = '/auth/refresh,/auth/logout,/auth/embed,/auth/ws-ticket'
    security_csrf_header_name: str = 'X-CSRF-Token'
    security_csrf_cookie_name: str = 'csrf_token'
    security_csrf_token_ttl_seconds: int = 604800

    security_csp_enabled: bool = True
    security_csp_script_src: str = "'self'"
    security_csp_style_src: str = "'self' 'unsafe-inline'"
    security_csp_img_src: str = "'self' data:"
    security_csp_connect_src: str = "'self'"
    security_frame_ancestors: str = "'self'"
    security_hsts_enabled: bool = True
    security_hsts_max_age: int = 31536000
    security_event_alert_threshold: int = 20


class SensitiveDataSettings(BaseSettings):
    """
    敏感数据加密配置
    """

    sensitive_data_enabled: bool = True
    sensitive_data_key: str = ''
    sensitive_data_prefix: str = 'enc:v1:'
    sensitive_data_deterministic: bool = False


class DataBaseSettings(BaseSettings):
    """
    数据库配置
    
    Google 工程标准：
    - 连接池大小基于 CPU 核心数计算
    - 启用连接健康检查
    - 合理的超时和回收配置
    """

    db_type: Literal['mysql', 'postgresql'] = 'mysql'
    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_username: str = 'root'
    db_password: str = 'admin1234'
    db_database: str = 'ruoyi-fastapi'
    db_echo: bool = True

    # 连接池配置 - 遵循 Google 最佳实践
    # 公式: pool_size = (CPU 核心数 × 2) + 有效磁盘数
    # 对于 4 核 CPU: (4 × 2) + 1 = 9，向上取整到 10
    db_pool_size: int = 10  # 🔧 核心连接数（从 50 降低到 10）
    db_max_overflow: int = 20  # 🔧 峰值时额外连接（从 10 增加到 20）
    db_pool_recycle: int = 3600  # 连接回收时间（1小时）
    db_pool_timeout: int = 30  # 获取连接超时（30秒）

    # 查询超时配置
    db_statement_timeout: int = 30000  # SQL 语句超时（30秒，毫秒）
    db_lock_timeout: int = 10000  # 锁等待超时（10秒，毫秒）

    @computed_field
    @property
    def sqlglot_parse_dialect(self) -> str:
        if self.db_type == 'postgresql':
            return 'postgres'
        return self.db_type


class DataBaseWorkflowSettings(BaseSettings):
    """
    数据库工作流配置
    """

    db_workflow_mode: Literal['migration', 'development'] = 'migration'
    db_dev_sync_engine: str = 'atlas'
    db_workflow_managed_scope: tuple[str, ...] = (
        'schema',
        'menus',
        'role_menus',
        'dict_types',
        'dict_data',
        'configs',
        'release_visibility',
    )
    db_workflow_status_command: str = 'python scripts/db.py status'
    db_workflow_dev_sync_command: str = 'python scripts/db.py dev-sync'
    db_workflow_finalize_command: str = 'python scripts/db.py finalize --message "<描述>"'
    db_workflow_deploy_command: str = 'python scripts/db.py deploy --revision head'
    db_workflow_verify_command: str = 'python scripts/db.py verify --ci'


@dataclass(frozen=True)
class DataBaseWorkflowStatus:
    """
    数据库工作流状态快照，供启动脚本、CLI 和运行时日志复用
    """

    workflow_mode: Literal['migration', 'development']
    db_dev_sync_engine: str
    db_target: str
    startup_action: Literal['dev-sync', 'deploy']
    deploy_path: str
    workflow_stage: str = 'deployment'
    allowed_actions: tuple[str, ...] = ('status', 'finalize', 'deploy', 'verify')
    managed_scope: tuple[str, ...] = (
        'schema',
        'menus',
        'role_menus',
        'dict_types',
        'dict_data',
        'configs',
        'release_visibility',
    )
    status_path: str = 'python scripts/db.py status'
    dev_sync_path: str = 'python scripts/db.py dev-sync'
    finalize_path: str = 'python scripts/db.py finalize --message "<描述>"'
    verify_path: str = 'python scripts/db.py verify --ci'
    schema_drift: str = 'unknown'
    managed_data_drift: str = 'unknown'
    visibility_drift: str = 'unknown'
    pending_release_bundle: str = 'unknown'
    last_successful_action: str = 'unknown'


def format_database_target(database_config: DataBaseSettings | None = None) -> str:
    """
    生成脱敏后的数据库目标摘要
    """
    database_config = database_config or DataBaseConfig
    return (
        f'{database_config.db_type}://'
        f'{database_config.db_host}:{database_config.db_port}/'
        f'{database_config.db_database}'
    )


def get_database_workflow_status(
    database_config: DataBaseSettings | None = None,
    workflow_config: DataBaseWorkflowSettings | None = None,
) -> DataBaseWorkflowStatus:
    """
    统一读取数据库工作流状态，避免不同入口重复拼装模式信息
    """
    database_config = database_config or DataBaseConfig
    workflow_config = workflow_config or DataBaseWorkflowConfig

    startup_action: Literal['dev-sync', 'deploy'] = 'deploy'
    workflow_stage = 'deployment'
    allowed_actions: tuple[str, ...] = ('status', 'finalize', 'deploy', 'verify')
    if workflow_config.db_workflow_mode == 'development':
        workflow_stage = 'development'
        startup_action = 'dev-sync'
        allowed_actions = ('status', 'dev-sync', 'finalize', 'verify')

    return DataBaseWorkflowStatus(
        workflow_mode=workflow_config.db_workflow_mode,
        db_dev_sync_engine=workflow_config.db_dev_sync_engine,
        db_target=format_database_target(database_config),
        startup_action=startup_action,
        deploy_path=workflow_config.db_workflow_deploy_command,
        workflow_stage=workflow_stage,
        allowed_actions=allowed_actions,
        managed_scope=workflow_config.db_workflow_managed_scope,
        status_path=workflow_config.db_workflow_status_command,
        dev_sync_path=workflow_config.db_workflow_dev_sync_command,
        finalize_path=workflow_config.db_workflow_finalize_command,
        verify_path=workflow_config.db_workflow_verify_command,
    )


class RedisSettings(BaseSettings):
    """
    Redis配置
    """

    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    redis_username: str = ''
    redis_password: str = ''
    redis_database: int = 2


class QueryCacheSettings(BaseSettings):
    """
    查询缓存配置
    """

    query_cache_enabled: bool = True
    query_cache_default_ttl: int = 300
    query_cache_lock_enabled: bool = True

    # COUNT 缓存配置（独立于查询缓存）
    count_cache_enabled: bool = True
    count_cache_default_ttl: int = 600  # COUNT 缓存时间较长，因为数据量变化频率低
    count_cache_key_prefix: str = "count_cache"


class AuditSettings(BaseSettings):
    """
    审计日志配置
    """

    audit_enabled: bool = True
    audit_write_enabled: bool = True
    audit_read_enabled: bool = True
    # 仅审计指定表（逗号分隔，留空表示不限制）
    audit_tables: str = 'sys_role,sys_dept,sys_menu,sys_job'
    # 脱敏字段（逗号分隔）
    audit_mask_fields: str = 'password,secret,token'
    # 审计字段最大长度（超出截断）
    audit_max_value_length: int = 2000
    # 读审计采样率（0~1）
    audit_read_sample_rate: float = 1.0


class ErrorHandlingSettings(BaseSettings):
    """
    错误处理配置（双层消息设计）
    """

    # 是否在响应中包含开发者消息（开发环境=true，生产环境=false）
    include_developer_message: bool = False
    # 错误日志级别
    error_log_level: str = "ERROR"
    # 默认语言
    default_language: str = "zh"


class LogSettings(BaseSettings):
    """
    日志配置
    """

    log_json_enabled: bool = True
    log_level: str = "INFO"
    request_logging_enabled: bool = False
    log_error_file_level: str = "ERROR"
    log_error_rotation: str = '50MB'
    log_error_compression: str = 'zip'


class IdempotencySettings(BaseSettings):
    """
    幂等中间件配置
    """

    idempotency_enabled: bool = True
    idempotency_ttl_seconds: int = 600
    idempotency_lock_ttl_seconds: int = 30
    idempotency_wait_timeout_ms: int = 2000
    # 逗号分隔：POST,PUT,...
    idempotency_methods: str = 'POST,PUT'
    # 逗号分隔：以 path prefix 方式匹配，'/' 表示全部路径
    idempotency_path_prefixes: str = '/'
    # 逗号分隔：优先排除的 path prefix
    idempotency_exclude_paths: str = '/health,/ready,/metrics,/docs,/redoc,/openapi.json'
    # 防止缓存超大响应体导致内存放大
    idempotency_max_response_body_bytes: int = 2 * 1024 * 1024
    # 防止读取超大请求体导致内存放大
    idempotency_max_request_body_bytes: int = 2 * 1024 * 1024


class RateLimitSettings(BaseSettings):
    """
    接口限流配置
    """

    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    # 逗号分隔：无需限流的 path prefix
    rate_limit_exclude_paths: str = '/health,/ready,/docs,/redoc,/openapi.json,/metrics'
    # 逗号分隔：认证类接口 path prefix（命中后归类为 auth tier）
    rate_limit_auth_paths: str = '/login,/captchaImage,/register'
    # 逗号分隔：写接口方法
    rate_limit_write_methods: str = 'POST,PUT,PATCH,DELETE'
    # 逗号分隔：可信代理 IP/CIDR（仅命中后才解析 X-Forwarded-For）
    rate_limit_trusted_proxies: str = '127.0.0.1,::1'

    # auth tier
    rate_limit_auth_ip: int = 20
    rate_limit_auth_user: int = 40
    # write tier
    rate_limit_write_ip: int = 120
    rate_limit_write_user: int = 240
    # read tier
    rate_limit_read_ip: int = 600
    rate_limit_read_user: int = 1200


class OTelSettings(BaseSettings):
    """
    OpenTelemetry 配置
    """

    otel_enabled: bool = False
    otel_service_name: str = 'ruoyi-fastapi-backend'
    otel_service_namespace: str = 'ruoyi-fastapi'
    otel_traces_sample_ratio: float = 1.0
    # 例如: http://127.0.0.1:4318/v1/traces
    otel_otlp_endpoint: str = ''
    otel_otlp_headers: str = ''
    otel_exporter_timeout_ms: int = 10000
    otel_console_exporter: bool = False
    # 逗号分隔，传递给 FastAPIInstrumentor excluded_urls
    otel_excluded_urls: str = '/health,/ready,/metrics,/docs,/redoc,/openapi.json'


class GenSettings:
    """
    代码生成配置
    """

    author = 'insistence'
    package_name = 'module_admin.system'
    auto_remove_pre = False
    table_prefix = 'sys_'
    allow_overwrite = False

    GEN_PATH = 'vf_admin/gen_path'

    def __init__(self):
        if not os.path.exists(self.GEN_PATH):
            os.makedirs(self.GEN_PATH)


class UploadSettings:
    """
    上传配置
    """

    UPLOAD_PREFIX = '/profile'
    UPLOAD_PATH = 'vf_admin/upload_path'
    UPLOAD_MACHINE = 'A'
    DEFAULT_ALLOWED_EXTENSION = [
        # 图片
        'bmp',
        'gif',
        'jpg',
        'jpeg',
        'png',
        # word excel powerpoint
        'doc',
        'docx',
        'xls',
        'xlsx',
        'ppt',
        'pptx',
        'html',
        'htm',
        'txt',
        # 压缩文件
        'rar',
        'zip',
        'gz',
        'bz2',
        # 视频格式
        'mp4',
        'avi',
        'rmvb',
        # pdf
        'pdf',
    ]
    DOWNLOAD_PATH = 'vf_admin/download_path'

    def __init__(self):
        if not os.path.exists(self.UPLOAD_PATH):
            os.makedirs(self.UPLOAD_PATH)
        if not os.path.exists(self.DOWNLOAD_PATH):
            os.makedirs(self.DOWNLOAD_PATH)


class CachePathConfig:
    """
    缓存目录配置
    """

    PATH = os.path.join(os.path.abspath(os.getcwd()), 'caches')
    PATHSTR = 'caches'


class GetConfig:
    """
    获取配置
    """

    def __init__(self):
        self.parse_cli_args()

    @lru_cache
    def get_app_config(self):
        """
        获取应用配置
        """
        # 实例化应用配置模型
        return AppSettings()

    @lru_cache
    def get_jwt_config(self):
        """
        获取Jwt配置
        """
        # 实例化Jwt配置模型
        return JwtSettings()

    @lru_cache
    def get_sensitive_config(self):
        """
        获取敏感数据加密配置
        """
        return SensitiveDataSettings()

    @lru_cache
    def get_security_config(self):
        """
        获取安全硬切配置
        """
        return SecuritySettings()

    @lru_cache
    def get_database_config(self):
        """
        获取数据库配置
        """
        # 实例化数据库配置模型
        return DataBaseSettings()

    @lru_cache
    def get_database_workflow_config(self):
        """
        获取数据库工作流配置
        """
        return DataBaseWorkflowSettings()

    @lru_cache
    def get_redis_config(self):
        """
        获取Redis配置
        """
        # 实例化Redis配置模型
        return RedisSettings()

    @lru_cache
    def get_gen_config(self):
        """
        获取代码生成配置
        """
        # 实例化代码生成配置
        return GenSettings()

    @lru_cache
    def get_upload_config(self):
        """
        获取数据库配置
        """
        # 实例上传配置
        return UploadSettings()

    @lru_cache
    def get_query_cache_config(self):
        """
        获取查询缓存配置
        """
        return QueryCacheSettings()

    @lru_cache
    def get_audit_config(self):
        """
        获取审计日志配置
        """
        return AuditSettings()

    @lru_cache
    def get_error_handling_config(self):
        """
        获取错误处理配置
        """
        return ErrorHandlingSettings()

    @lru_cache
    def get_log_config(self):
        """
        获取日志配置
        """
        return LogSettings()

    @lru_cache
    def get_idempotency_config(self):
        """
        获取幂等配置
        """
        return IdempotencySettings()

    @lru_cache
    def get_rate_limit_config(self):
        """
        获取限流配置
        """
        return RateLimitSettings()

    @lru_cache
    def get_dev_menu_sync_config(self):
        """
        获取开发态菜单热同步配置
        """
        return DevMenuSyncSettings()

    @lru_cache
    def get_otel_config(self):
        """
        获取 OpenTelemetry 配置
        """
        return OTelSettings()

    @staticmethod
    def parse_cli_args():
        """
        解析命令行参数
        """
        backend_root = Path(__file__).resolve().parents[1]
        if 'uvicorn' in sys.argv[0]:
            # 使用uvicorn启动时，命令行参数需要按照uvicorn的文档进行配置，无法自定义参数
            pass
        else:
            # 使用argparse定义命令行参数
            parser = argparse.ArgumentParser(description='命令行参数')
            parser.add_argument('--env', type=str, default='', help='运行环境')
            # 解析命令行参数 (使用parse_known_args以兼容pytest等工具)
            args, unknown = parser.parse_known_args()
            # 设置环境变量，如果未设置命令行参数，默认APP_ENV为dev
            os.environ['APP_ENV'] = args.env if args.env else 'dev'
        # 读取运行环境
        run_env = os.environ.get('APP_ENV', '')
        # 运行环境未指定时默认加载.env.dev
        env_file = '.env.dev'
        # 运行环境不为空时按命令行参数加载对应.env文件
        if run_env != '':
            env_file = f'.env.{run_env}'
        # 加载配置
        load_dotenv(backend_root / env_file)

        # 统一数据库默认配置，避免被历史 .env 文件中空密码覆盖
        # 当前项目约定：开发环境使用 root/admin1234 连接 ruoyi-fastapi 库
        os.environ['DB_TYPE'] = os.environ.get('DB_TYPE', 'mysql')
        os.environ['DB_HOST'] = os.environ.get('DB_HOST', '127.0.0.1')
        os.environ['DB_PORT'] = os.environ.get('DB_PORT', '3306')
        os.environ['DB_USERNAME'] = os.environ.get('DB_USERNAME', 'root')
        os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', 'root')
        os.environ['DB_DATABASE'] = os.environ.get('DB_DATABASE', 'ruoyi-fastapi')
        os.environ['DB_WORKFLOW_MODE'] = os.environ.get('DB_WORKFLOW_MODE') or 'migration'
        os.environ['DB_DEV_SYNC_ENGINE'] = os.environ.get('DB_DEV_SYNC_ENGINE') or 'atlas'


# 实例化获取配置类
get_config = GetConfig()
# 应用配置
AppConfig = get_config.get_app_config()
# Jwt配置
JwtConfig = get_config.get_jwt_config()
# 敏感数据加密配置
SensitiveConfig = get_config.get_sensitive_config()
# 安全硬切配置
SecurityConfig = get_config.get_security_config()
# 数据库配置
DataBaseConfig = get_config.get_database_config()
# 数据库工作流配置
DataBaseWorkflowConfig = get_config.get_database_workflow_config()
# Redis配置
RedisConfig = get_config.get_redis_config()
# 代码生成配置
GenConfig = get_config.get_gen_config()
# 上传配置
UploadConfig = get_config.get_upload_config()
# 查询缓存配置
CacheConfig = get_config.get_query_cache_config()
# 审计日志配置
AuditConfig = get_config.get_audit_config()
# 错误处理配置
ErrorHandlingConfig = get_config.get_error_handling_config()
# 日志配置
LogConfig = get_config.get_log_config()
# 幂等配置
IdempotencyConfig = get_config.get_idempotency_config()
# 限流配置
RateLimitConfig = get_config.get_rate_limit_config()
# 开发态菜单热同步配置
DevMenuSyncConfig = get_config.get_dev_menu_sync_config()
# OpenTelemetry 配置
OTelConfig = get_config.get_otel_config()
