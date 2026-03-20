import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType, RedisInitKeyConfig
from config.env import SecurityConfig
from config.get_db import get_db
from container.dependencies import service_provider
from exceptions.exception import AuthException
from module_admin.annotation.log_annotation import Log
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.login_vo import Token, UserLogin, UserRegister
from module_admin.entity.vo.user_vo import CurrentUserModel, EditUserModel
from modules.identity.application.services import SecurityTokenService
from modules.identity.application.services.login_service import (
    CustomOAuth2PasswordRequestForm,
    LoginService,
    oauth2_scheme,
)
from ports import IUserService
from utils.log_util import logger
from utils.response_util import ResponseUtil

loginController = APIRouter()


def _resolve_security_service(request: Request) -> SecurityTokenService:
    service = getattr(request.app.state, 'security_token_service', None)
    if service is None:
        service = SecurityTokenService(getattr(request.app.state, 'redis', None))
        request.app.state.security_token_service = service
    return service


def _normalize_samesite() -> str:
    candidate = str(SecurityConfig.security_cookie_samesite or 'lax').strip().lower()
    return candidate if candidate in {'lax', 'strict', 'none'} else 'lax'


def _is_secure_request(request: Request) -> bool:
    return request.url.scheme == 'https'


def _set_auth_cookies(
    response: Response,
    *,
    request: Request,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    csrf_ttl: int,
) -> None:
    secure = _is_secure_request(request)
    samesite = _normalize_samesite()
    response.set_cookie(
        SecurityConfig.security_access_cookie_name,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max(1, int(SecurityConfig.security_jwt_max_expire_seconds)),
        path='/',
    )
    response.set_cookie(
        SecurityConfig.security_refresh_cookie_name,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max(1, int(SecurityConfig.security_refresh_expire_seconds)),
        path='/',
    )
    response.set_cookie(
        SecurityConfig.security_csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=secure,
        samesite=samesite,
        max_age=max(1, int(csrf_ttl)),
        path='/',
    )


def _clear_auth_cookies(response: Response, *, request: Request) -> None:
    secure = _is_secure_request(request)
    samesite = _normalize_samesite()
    response.delete_cookie(SecurityConfig.security_access_cookie_name, path='/', secure=secure, samesite=samesite)
    response.delete_cookie(SecurityConfig.security_refresh_cookie_name, path='/', secure=secure, samesite=samesite)
    response.delete_cookie(SecurityConfig.security_csrf_cookie_name, path='/', secure=secure, samesite=samesite)


def _extract_user_id(payload: dict[str, Any]) -> str:
    user_id = payload.get('user_id')
    if user_id is not None and str(user_id).isdigit():
        return str(user_id)
    subject = str(payload.get('sub') or '')
    if subject.startswith('user:') and subject.split(':', 1)[1].isdigit():
        return subject.split(':', 1)[1]
    raise AuthException(user_message='登录状态已失效，请重新登录', developer_message='Missing user_id in refresh token')


def _build_user_claims(
    *,
    user_id: str,
    user_name: str,
    dept_name: str | None,
    session_id: str,
    login_info: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        'user_id': user_id,
        'user_name': user_name,
        'dept_name': dept_name,
        'session_id': session_id,
        'login_info': login_info or {},
    }


@loginController.post('/login', response_model=Token)
@Log(title='用户登录', business_type=BusinessType.OTHER, log_type='login')
async def login(
    request: Request,
    form_data: CustomOAuth2PasswordRequestForm = Depends(),
    query_db: AsyncSession = Depends(get_db),
    login_service: LoginService = Depends(service_provider('login_service')),
    user_service: IUserService = Depends(service_provider('user_service')),
):
    captcha_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled') == 'true'
        else False
    )
    user = UserLogin(
        userName=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        loginInfo=form_data.login_info,
        captchaEnabled=captcha_enabled,
    )
    result = await login_service.authenticate_user(request, user)
    security_service = _resolve_security_service(request)

    user_id = str(result[0].user_id)
    user_name = result[0].user_name
    dept_name = result[1].dept_name if result[1] else None
    session_id = uuid.uuid4().hex
    claims = _build_user_claims(
        user_id=user_id,
        user_name=user_name,
        dept_name=dept_name,
        session_id=session_id,
        login_info=user.login_info,
    )

    access_token = await security_service.issue_access_token(
        subject=f'user:{user_id}',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=SecurityConfig.security_jwt_max_expire_seconds,
        token_use='user_access',
        claims=claims,
    )
    refresh_token = await security_service.issue_access_token(
        subject=f'user:{user_id}',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=SecurityConfig.security_refresh_expire_seconds,
        token_use='user_refresh',
        max_expire_seconds=SecurityConfig.security_refresh_expire_seconds,
        claims=claims,
    )
    await security_service.register_user_session(
        session_id=session_id,
        token=access_token,
        user_id=user_id,
        user_name=user_name,
        dept_name=dept_name,
        login_info=user.login_info,
        expires_at=int(datetime.now(UTC).timestamp()) + int(SecurityConfig.security_jwt_max_expire_seconds),
    )
    csrf_token, csrf_ttl = await security_service.issue_csrf_token(user_id)

    await user_service.edit_user_services(query_db, EditUserModel(userId=result[0].user_id, loginDate=datetime.now(), type='status'))
    logger.info('登录成功')

    request_from_swagger = request.headers.get('referer').endswith('docs') if request.headers.get('referer') else False
    request_from_redoc = request.headers.get('referer').endswith('redoc') if request.headers.get('referer') else False
    if request_from_swagger or request_from_redoc:
        return {'access_token': access_token, 'token_type': 'Bearer'}

    response = ResponseUtil.success(
        message='登录成功',
        dict_content={
            'token': access_token,
            'expiresIn': SecurityConfig.security_jwt_max_expire_seconds,
            'refreshExpiresIn': SecurityConfig.security_refresh_expire_seconds,
            'csrfToken': csrf_token,
        },
    )
    _set_auth_cookies(
        response,
        request=request,
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        csrf_ttl=csrf_ttl,
    )
    return response


@loginController.post('/auth/refresh')
async def refresh_session(request: Request):
    security_service = _resolve_security_service(request)
    refresh_token = (request.cookies.get(SecurityConfig.security_refresh_cookie_name) or '').strip()
    if not refresh_token:
        raise AuthException(user_message='登录状态已过期，请重新登录', developer_message='Missing refresh token cookie')

    payload = await security_service.verify_access_token(
        refresh_token,
        audience=SecurityConfig.security_jwt_audience_api,
        enforce_replay=True,
        expected_use='user_refresh',
        enforce_session=False,
        max_lifetime_seconds=SecurityConfig.security_refresh_expire_seconds,
    )
    user_id = _extract_user_id(payload)
    user_name = str(payload.get('user_name') or '')
    dept_name = payload.get('dept_name')
    session_id = str(payload.get('session_id') or payload.get('sessionId') or '')
    if not session_id:
        raise AuthException(user_message='登录状态已失效，请重新登录', developer_message='Missing session_id in refresh token')

    login_info = payload.get('login_info')
    if not isinstance(login_info, dict):
        login_info = {}
    claims = _build_user_claims(
        user_id=user_id,
        user_name=user_name,
        dept_name=str(dept_name) if dept_name is not None else None,
        session_id=session_id,
        login_info=login_info,
    )
    access_token = await security_service.issue_access_token(
        subject=f'user:{user_id}',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=SecurityConfig.security_jwt_max_expire_seconds,
        token_use='user_access',
        claims=claims,
    )
    new_refresh_token = await security_service.issue_access_token(
        subject=f'user:{user_id}',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=SecurityConfig.security_refresh_expire_seconds,
        token_use='user_refresh',
        max_expire_seconds=SecurityConfig.security_refresh_expire_seconds,
        claims=claims,
    )
    await security_service.register_user_session(
        session_id=session_id,
        token=access_token,
        user_id=user_id,
        user_name=user_name,
        dept_name=str(dept_name) if dept_name is not None else None,
        login_info=login_info,
        expires_at=int(datetime.now(UTC).timestamp()) + int(SecurityConfig.security_jwt_max_expire_seconds),
    )
    csrf_token, csrf_ttl = await security_service.issue_csrf_token(user_id)

    response = ResponseUtil.success(
        message='刷新成功',
        dict_content={
            'token': access_token,
            'expiresIn': SecurityConfig.security_jwt_max_expire_seconds,
            'refreshExpiresIn': SecurityConfig.security_refresh_expire_seconds,
            'csrfToken': csrf_token,
        },
    )
    _set_auth_cookies(
        response,
        request=request,
        access_token=access_token,
        refresh_token=new_refresh_token,
        csrf_token=csrf_token,
        csrf_ttl=csrf_ttl,
    )
    return response


@loginController.get('/getInfo', response_model=CurrentUserModel)
async def get_login_user_info(
    request: Request, current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    logger.info('获取成功')
    return ResponseUtil.success(model_content=current_user)


@loginController.get('/getRouters')
async def get_login_user_routers(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    login_service: LoginService = Depends(service_provider('login_service')),
):
    logger.info('获取成功')
    user_routers = await login_service.get_current_user_routers(current_user.user.user_id)
    return ResponseUtil.success(data=user_routers)


@loginController.post('/register', response_model=CrudResponseModel)
async def register_user(
    request: Request,
    user_register: UserRegister,
    login_service: LoginService = Depends(service_provider('login_service')),
    user_service: IUserService = Depends(service_provider('user_service')),
):
    user_register_result = await login_service.register_user_services(request, user_register, user_service)
    logger.info(user_register_result.message)
    return ResponseUtil.success(data=user_register_result, message=user_register_result.message)


@loginController.post('/auth/logout')
async def logout(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    login_service: LoginService = Depends(service_provider('login_service')),
):
    _ = login_service
    session_id = ''
    security_service = _resolve_security_service(request)
    access_token = (token or request.cookies.get(SecurityConfig.security_access_cookie_name, '') or '').strip()
    try:
        if access_token:
            payload = await security_service.verify_access_token(
                access_token,
                audience=SecurityConfig.security_jwt_audience_api,
                enforce_replay=False,
                enforce_session=False,
                max_lifetime_seconds=SecurityConfig.security_jwt_max_expire_seconds,
            )
            session_id = str(payload.get('session_id') or payload.get('sessionId') or '')
        if not session_id:
            refresh_token = (request.cookies.get(SecurityConfig.security_refresh_cookie_name, '') or '').strip()
            if refresh_token:
                payload = await security_service.verify_access_token(
                    refresh_token,
                    audience=SecurityConfig.security_jwt_audience_api,
                    enforce_replay=False,
                    expected_use='user_refresh',
                    enforce_session=False,
                    max_lifetime_seconds=SecurityConfig.security_refresh_expire_seconds,
                )
                session_id = str(payload.get('session_id') or payload.get('sessionId') or '')
        if session_id:
            await security_service.revoke_user_session(session_id)
    except Exception:
        logger.warning('登出时token校验失败，执行无状态退出')
    else:
        logger.info('退出成功')

    response = ResponseUtil.success(message='退出成功')
    _clear_auth_cookies(response, request=request)
    return response
