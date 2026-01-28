import argparse
import os
import sys
from dotenv import load_dotenv
from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings
from typing import Literal


class AppSettings(BaseSettings):
    """
    应用配置
    """

    app_env: str = 'dev'
    app_name: str = 'RuoYi-FasAPI'
    app_root_path: str = '/dev-api'
    app_host: str = '0.0.0.0'
    app_port: int = 9099
    app_version: str = '1.0.0'
    app_reload: bool = True
    app_ip_location_query: bool = True
    app_same_time_login: bool = True


class JwtSettings(BaseSettings):
    """
    Jwt配置
    """

    jwt_secret_key: str = 'b01c66dc2c58dc6a0aabfe2144256be36226de378bf87f72c0c795dda67f4d55'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 1440
    jwt_redis_expire_minutes: int = 30


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

    @lru_cache()
    def get_app_config(self):
        """
        获取应用配置
        """
        # 实例化应用配置模型
        return AppSettings()

    @lru_cache()
    def get_jwt_config(self):
        """
        获取Jwt配置
        """
        # 实例化Jwt配置模型
        return JwtSettings()

    @lru_cache()
    def get_sensitive_config(self):
        """
        获取敏感数据加密配置
        """
        return SensitiveDataSettings()

    @lru_cache()
    def get_database_config(self):
        """
        获取数据库配置
        """
        # 实例化数据库配置模型
        return DataBaseSettings()

    @lru_cache()
    def get_redis_config(self):
        """
        获取Redis配置
        """
        # 实例化Redis配置模型
        return RedisSettings()

    @lru_cache()
    def get_gen_config(self):
        """
        获取代码生成配置
        """
        # 实例化代码生成配置
        return GenSettings()

    @lru_cache()
    def get_upload_config(self):
        """
        获取数据库配置
        """
        # 实例上传配置
        return UploadSettings()

    @lru_cache()
    def get_query_cache_config(self):
        """
        获取查询缓存配置
        """
        return QueryCacheSettings()

    @lru_cache()
    def get_audit_config(self):
        """
        获取审计日志配置
        """
        return AuditSettings()

    @lru_cache()
    def get_error_handling_config(self):
        """
        获取错误处理配置
        """
        return ErrorHandlingSettings()

    @staticmethod
    def parse_cli_args():
        """
        解析命令行参数
        """
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
        load_dotenv(env_file)

        # 统一数据库默认配置，避免被历史 .env 文件中空密码覆盖
        # 当前项目约定：开发环境使用 root/admin1234 连接 ruoyi-fastapi 库
        os.environ['DB_TYPE'] = os.environ.get('DB_TYPE', 'mysql')
        os.environ['DB_HOST'] = os.environ.get('DB_HOST', '127.0.0.1')
        os.environ['DB_PORT'] = os.environ.get('DB_PORT', '3306')
        os.environ['DB_USERNAME'] = os.environ.get('DB_USERNAME', 'root')
        os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', 'root')
        os.environ['DB_DATABASE'] = os.environ.get('DB_DATABASE', 'ruoyi-fastapi')


# 实例化获取配置类
get_config = GetConfig()
# 应用配置
AppConfig = get_config.get_app_config()
# Jwt配置
JwtConfig = get_config.get_jwt_config()
# 敏感数据加密配置
SensitiveConfig = get_config.get_sensitive_config()
# 数据库配置
DataBaseConfig = get_config.get_database_config()
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
