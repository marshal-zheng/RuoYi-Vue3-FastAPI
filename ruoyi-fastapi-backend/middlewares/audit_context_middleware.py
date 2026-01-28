"""
审计上下文中间件
为每个请求注入审计上下文，并在响应后写入读审计日志
"""
import jwt
from jwt.exceptions import InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.database import AsyncSessionLocal
from config.env import AuditConfig, JwtConfig
from utils.audit_context import set_audit_context, pop_read_audits
from utils.log_util import logger
from middlewares.trace_middleware import TraceCtx
from module_admin.entity.do.audit_log_do import SysAuditLog


class AuditContextMiddleware(BaseHTTPMiddleware):
    """审计上下文中间件"""

    async def dispatch(self, request: Request, call_next):
        context = self._build_context(request)
        set_audit_context(context)

        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            if AuditConfig.audit_enabled and AuditConfig.audit_read_enabled:
                await self._flush_read_audits()

    @staticmethod
    def _build_context(request: Request):
        token = request.headers.get('Authorization', '')
        if token.lower().startswith('bearer '):
            token = token[7:].strip()

        user_id = None
        user_name = None
        if token:
            try:
                payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
                user_id = payload.get('user_id')
                user_name = payload.get('user_name')
            except InvalidTokenError:
                pass
            except Exception:
                pass

        client_ip = request.headers.get('X-Forwarded-For') or (request.client.host if request.client else '')

        trace_id = TraceCtx.get_id()
        if not trace_id:
            trace_id = TraceCtx.set_id()

        return {
            'user_id': user_id,
            'user_name': user_name,
            'ip': client_ip,
            'method': request.method,
            'path': request.url.path,
            'user_agent': request.headers.get('User-Agent', ''),
            'request_id': trace_id,
            'trace_id': trace_id,
        }

    @staticmethod
    async def _flush_read_audits():
        entries = pop_read_audits()
        if not entries:
            return

        async with AsyncSessionLocal() as session:
            try:
                session.add_all([SysAuditLog(**entry) for entry in entries])
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.warning(f'读审计日志写入失败: {exc}')
