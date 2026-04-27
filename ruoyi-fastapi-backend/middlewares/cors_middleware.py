from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.env import SecurityConfig


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in (raw or '').split(',') if item.strip()]


def add_cors_middleware(app: FastAPI):
    """
    添加跨域中间件

    :param app: FastAPI对象
    :return:
    """
    # 前端页面url（硬切后统一由安全配置控制）
    origins = _parse_csv(SecurityConfig.security_allowed_origins)

    # 后台api允许跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=SecurityConfig.security_cors_allow_credentials,
        allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        allow_headers=['Authorization', 'Content-Type', 'X-CSRF-Token', 'X-Requested-With'],
        expose_headers=[
            'X-Request-Id',
            'X-Trace-Id',
            'Location',
            'Retry-After',
            'RateLimit-Limit',
            'RateLimit-Remaining',
            'RateLimit-Reset',
        ],
    )
