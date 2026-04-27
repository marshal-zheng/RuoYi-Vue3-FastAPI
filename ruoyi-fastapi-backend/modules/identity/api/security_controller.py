from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.env import SecurityConfig
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.application.services import LoginService, SecurityTokenService
from utils.response_util import ResponseUtil

securityController = APIRouter()


class M2MClientRegisterModel(BaseModel):
    client_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    integration_id: str = Field(min_length=1)
    jwk: dict
    enabled: bool = True


class EmbedPolicyModel(BaseModel):
    tenant_id: str = Field(min_length=1)
    integration_id: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    path_pattern: str = Field(default='/')
    enabled: bool = True


class EmbedGrantRequestModel(BaseModel):
    tenant_id: str = Field(min_length=1)
    integration_id: str = Field(min_length=1)
    path: str = Field(default='/')
    subject: str = Field(min_length=1)


class EmbedExchangeRequestModel(BaseModel):
    embed_grant: str = Field(min_length=1)


class WSTicketRequestModel(BaseModel):
    session_id: str = Field(min_length=1)


class KeyRotateRequestModel(BaseModel):
    algorithm: str | None = None


class KeyRevokeRequestModel(BaseModel):
    kid: str = Field(min_length=1)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    if request.client:
        return request.client.host
    return ''


def _resolve_security_service(request: Request) -> SecurityTokenService:
    service = getattr(request.app.state, 'security_token_service', None)
    if service is None:
        service = SecurityTokenService(getattr(request.app.state, 'redis', None))
        request.app.state.security_token_service = service
    return service


@securityController.get('/.well-known/jwks.json')
async def jwks(request: Request):
    service = _resolve_security_service(request)
    return JSONResponse(content=service.get_jwks())


@securityController.post(
    '/auth/m2m/clients',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('system:user:add'))],
)
async def register_m2m_client(
    request: Request,
    payload: M2MClientRegisterModel,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    service = _resolve_security_service(request)
    kid = await service.register_client_jwk(
        client_id=payload.client_id,
        tenant_id=payload.tenant_id,
        integration_id=payload.integration_id,
        jwk=payload.jwk,
        enabled=payload.enabled,
    )
    return ResponseUtil.ok_resource(
        {
            'clientId': payload.client_id,
            'tenantId': payload.tenant_id,
            'integrationId': payload.integration_id,
            'kid': kid,
            'operator': current_user.user.user_name if current_user.user else 'system',
        }
    )


@securityController.post('/auth/m2m/token')
async def issue_m2m_token(
    request: Request,
    grant_type: str = Form(default='client_credentials'),
    client_assertion_type: str = Form(default='urn:ietf:params:oauth:client-assertion-type:jwt-bearer'),
    client_assertion: str = Form(default=''),
    client_secret: str = Form(default=''),
    scope: str = Form(default=''),
):
    service = _resolve_security_service(request)
    if request.headers.get('Authorization') or request.headers.get('X-API-Key') or client_secret:
        return JSONResponse(status_code=400, content={'error': 'invalid_client'})
    if grant_type != 'client_credentials':
        return JSONResponse(status_code=400, content={'error': 'unsupported_grant_type'})
    if client_assertion_type != 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer':
        return JSONResponse(status_code=400, content={'error': 'invalid_client_assertion_type'})
    if not client_assertion:
        return JSONResponse(status_code=400, content={'error': 'invalid_client_assertion'})

    audience = [request.url.path, str(request.url)]
    client_id, _, record = await service.verify_private_key_jwt(assertion=client_assertion, audience=audience)

    expires_in = SecurityConfig.security_m2m_expire_seconds
    access_token = await service.issue_access_token(
        subject=f'client:{client_id}',
        audience=SecurityConfig.security_jwt_audience_api,
        expires_seconds=expires_in,
        token_use='m2m_access',
        claims={
            'scope': scope,
            'tenant_id': record.get('tenantId'),
            'integration_id': record.get('integrationId'),
            'client_id': client_id,
        },
    )

    return JSONResponse(
        content={
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }
    )


@securityController.post(
    '/auth/embed/policies',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('system:role:edit'))],
)
async def upsert_embed_policy(
    request: Request,
    payload: EmbedPolicyModel,
):
    service = _resolve_security_service(request)
    service.ensure_origin_allowed(payload.origin)
    await service.upsert_embed_policy(
        tenant_id=payload.tenant_id,
        integration_id=payload.integration_id,
        origin=payload.origin,
        path_pattern=payload.path_pattern,
        enabled=payload.enabled,
    )
    return ResponseUtil.ok_resource(payload.model_dump())


@securityController.post('/auth/embed/grants')
async def issue_embed_grant(
    request: Request,
    payload: EmbedGrantRequestModel,
):
    service = _resolve_security_service(request)
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.lower().startswith('bearer '):
        return JSONResponse(status_code=401, content={'error': 'invalid_token'})
    bearer_token = auth_header.split(' ', 1)[1].strip()
    token_payload = await service.verify_access_token(
        bearer_token,
        audience=SecurityConfig.security_jwt_audience_api,
        enforce_replay=False,
    )
    token_use = str(token_payload.get('token_use') or '')
    if token_use not in {'m2m_access', 'user_access'}:
        return JSONResponse(status_code=403, content={'error': 'insufficient_token_scope'})

    origin = service.extract_origin(origin=request.headers.get('Origin'), referer=request.headers.get('Referer'))
    service.ensure_origin_allowed(origin)

    grant, ttl = await service.issue_embed_grant(
        tenant_id=payload.tenant_id,
        integration_id=payload.integration_id,
        origin=str(origin),
        path=payload.path,
        subject=payload.subject,
        request_id=request.headers.get('X-Request-Id', ''),
        source_ip=_client_ip(request),
    )
    return ResponseUtil.ok_resource({'embedGrant': grant, 'expiresIn': ttl, 'tokenType': 'Bearer'})


@securityController.post('/auth/embed/exchange')
async def exchange_embed_grant(
    request: Request,
    payload: EmbedExchangeRequestModel,
):
    service = _resolve_security_service(request)
    origin = service.extract_origin(origin=request.headers.get('Origin'), referer=request.headers.get('Referer'))
    service.ensure_origin_allowed(origin)

    access_token, expires_in, claims = await service.exchange_embed_grant(
        embed_grant=payload.embed_grant,
        origin=str(origin),
        request_id=request.headers.get('X-Request-Id', ''),
        source_ip=_client_ip(request),
    )
    return ResponseUtil.ok_resource(
        {
            'accessToken': access_token,
            'tokenType': 'Bearer',
            'expiresIn': expires_in,
            'subject': claims.get('sub'),
        }
    )


@securityController.post('/auth/ws-ticket', dependencies=[Depends(LoginService.get_current_user)])
async def issue_ws_ticket(
    request: Request,
    payload: WSTicketRequestModel,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    service = _resolve_security_service(request)
    origin = service.extract_origin(origin=request.headers.get('Origin'), referer=request.headers.get('Referer'))
    service.ensure_origin_allowed(origin)

    ticket, ttl = await service.issue_ws_ticket(
        subject=str(current_user.user.user_id if current_user.user else ''),
        origin=str(origin),
        session_id=payload.session_id,
    )
    return ResponseUtil.ok_resource({'wsTicket': ticket, 'expiresIn': ttl})


@securityController.post('/auth/csrf-token', dependencies=[Depends(LoginService.get_current_user)])
async def issue_csrf_token(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    service = _resolve_security_service(request)
    subject = str(current_user.user.user_id if current_user.user else '')
    token, ttl = await service.issue_csrf_token(subject)

    response = ResponseUtil.ok_resource({'csrfToken': token, 'expiresIn': ttl})
    expires = datetime.now(UTC) + timedelta(seconds=ttl)
    response.set_cookie(
        SecurityConfig.security_csrf_cookie_name,
        token,
        httponly=False,
        secure=request.url.scheme == 'https',
        samesite='strict',
        expires=expires,
        path='/',
    )
    return response


@securityController.get(
    '/auth/keys',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('system:role:query'))],
)
async def list_signing_keys(
    request: Request,
):
    service = _resolve_security_service(request)
    return ResponseUtil.ok_resource({'keys': service.list_signing_keys()})


@securityController.post(
    '/auth/keys/rotate',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('system:role:edit'))],
)
async def rotate_signing_keys(
    request: Request,
    payload: KeyRotateRequestModel,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    service = _resolve_security_service(request)
    result = await service.rotate_signing_key(
        algorithm=payload.algorithm,
        operator=current_user.user.user_name if current_user.user else 'system',
    )
    return ResponseUtil.ok_resource(result)


@securityController.post(
    '/auth/keys/revoke',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('system:role:edit'))],
)
async def revoke_signing_keys(
    request: Request,
    payload: KeyRevokeRequestModel,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    service = _resolve_security_service(request)
    await service.revoke_signing_key(
        kid=payload.kid,
        operator=current_user.user.user_name if current_user.user else 'system',
    )
    return ResponseUtil.no_content()


@securityController.get(
    '/auth/security/report',
    dependencies=[Depends(LoginService.get_current_user), Depends(CheckUserInterfaceAuth('monitor:online:query'))],
)
async def get_security_report(
    request: Request,
):
    service = _resolve_security_service(request)
    report = await service.get_security_event_report(limit=200)
    return ResponseUtil.ok_resource(report)
