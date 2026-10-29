"""HTTP contract of the file asset API and its middlewares (ASGI app on SQLite + fake storage)."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from config.get_db import get_db
from exceptions.exception import AuthException
from exceptions.handle import handle_exception
from middlewares.csrf_guard_middleware import CsrfGuardASGIMiddleware
from middlewares.rate_limit_middleware import RateLimitASGIMiddleware
from middlewares.upload_limit_middleware import UploadLimitASGIMiddleware
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.file_assets.api.file_asset_controller import fileAssetController
from modules.file_assets.api.http import content_disposition, etag_matches
from modules.file_assets.application import composition
from modules.file_assets.application.runtime import OwnershipState
from modules.file_assets.domain.models import Actor, OwnerRef
from modules.file_assets.infrastructure.models import FileAssetDO
from modules.file_assets.tests.conftest import png_bytes
from modules.identity.ports import get_current_user

pytestmark = pytest.mark.usefixtures('seeded')


def _user(user_id: int, permissions: list[str]) -> CurrentUserModel:
    return CurrentUserModel(
        permissions=permissions, roles=[], user=UserInfoModel(userId=user_id, userName=f'u{user_id}', nickName='u')
    )


@pytest.fixture
def principal():
    return {'user': _user(2, ['system:notice:add', 'system:notice:edit', 'system:notice:list'])}


@pytest.fixture
def app(runtime, session_factory, principal):
    services = composition.configure_file_assets(session_factory, runtime=runtime)
    app = FastAPI()
    handle_exception(app)
    app.include_router(fileAssetController)
    app.add_middleware(UploadLimitASGIMiddleware, limits={'/file-assets/uploads': 2048}, receive_timeout_seconds=0.5)

    async def current_user():
        user = principal['user']
        if user is None:
            raise AuthException(data='', user_message='用户token不合法')
        return user

    async def db():
        async with session_factory() as session:
            yield session
            if session.in_transaction():
                await session.commit()

    app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_db] = db
    app.state.services = services
    yield app
    composition._services = None


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
        yield client


async def _upload(client, data=None, *, purpose='notice.image', owner_id=None, name='a.png'):
    form = {'purpose': purpose} | ({'ownerId': owner_id} if owner_id else {})
    return await client.post(
        '/file-assets/uploads', data=form, files={'file': (name, data or png_bytes(), 'image/png')}
    )


async def test_upload_metadata_content_and_revalidation(client):
    response = await _upload(client, owner_id='10')
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {'assetId', 'name', 'mediaType', 'size', 'contentUrl'}
    batch = await client.post('/file-assets/metadata:batch', json={'assetIds': [body['assetId'], 'nope']})
    assert batch.json() == {'items': [body], 'unavailableIds': ['nope']}
    content = await client.get(body['contentUrl'])
    assert content.status_code == 200 and content.content.startswith(b'\x89PNG')
    headers = content.headers
    assert headers['content-type'] == 'image/png' and headers['cache-control'] == 'private, no-cache'
    assert headers['content-disposition'].startswith('inline;')
    assert headers['x-content-type-options'] == 'nosniff'
    assert headers['content-security-policy'] == "default-src 'none'; sandbox"
    assert headers['referrer-policy'] == 'no-referrer'
    assert int(headers['content-length']) == body['size']
    revalidated = await client.get(body['contentUrl'], headers={'If-None-Match': f'"x", W/{headers["etag"]}'})
    assert revalidated.status_code == 304 and revalidated.content == b''
    forced = await client.get(body['contentUrl'] + '?download=true')
    assert forced.headers['content-disposition'].startswith('attachment;')


async def test_304_never_touches_storage(client, storage):
    body = (await _upload(client, owner_id='10')).json()
    etag = (await client.get(body['contentUrl'])).headers['etag']
    storage.calls.clear()
    assert (await client.get(body['contentUrl'], headers={'If-None-Match': etag})).status_code == 304
    assert storage.calls == []


async def test_unauthorized_rejection_happens_before_rows_and_objects(
    client, principal, session_factory, storage, runtime
):
    principal['user'] = None
    response = await _upload(client)
    assert response.status_code == 401
    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(FileAssetDO)) == 0
    assert storage.objects == {} and runtime.metrics.in_use['upload'] == 0


async def test_invisible_and_unknown_assets_are_indistinguishable(client, principal):
    body = (await _upload(client, owner_id='10')).json()
    principal['user'] = _user(3, [])
    for url in (body['contentUrl'], f'/file-assets/{body["assetId"]}', '/file-assets/not-a-uuid/content'):
        response = await client.get(url)
        assert response.status_code == 404
        assert response.json()['type'].endswith('/file-asset-not-found')


async def test_discard_semantics(client, session_factory, bindings, principal):
    body = (await _upload(client, owner_id='10')).json()
    assert (await client.delete(f'/file-assets/{body["assetId"]}')).status_code == 204
    assert (await client.delete(f'/file-assets/{body["assetId"]}')).status_code == 204
    bound = (await _upload(client, owner_id='10')).json()

    async with session_factory() as session:
        await bindings.replace_field_assets(
            session,
            Actor.from_current_user(principal['user']),
            OwnerRef.of('system.notice', 10),
            'noticeContent',
            [bound['assetId']],
            creating=False,
        )
        await session.commit()
    conflict = await client.delete(f'/file-assets/{bound["assetId"]}')
    assert conflict.status_code == 409 and conflict.json()['reasonCode'] == 'ASSET_BOUND'
    principal['user'] = _user(1, ['*:*:*'])
    assert (await client.delete(f'/file-assets/{body["assetId"]}')).status_code == 404


async def test_problem_details_carry_reason_codes(client):
    response = await _upload(client, purpose='user.avatar')
    assert response.status_code == 422 and response.json()['reasonCode'] == 'PURPOSE_ENTRY_MISMATCH'
    response = await client.post(
        '/file-assets/uploads', data={'purpose': 'notice.image'}, files={'file': ('a.svg', b'<svg/>', 'image/svg+xml')}
    )
    assert response.status_code == 415 and response.json()['type'].endswith('/file-asset-unsupported-type')
    two = await client.post(
        '/file-assets/uploads',
        data={'purpose': 'notice.image'},
        files=[('file', ('a.png', b'1', 'image/png')), ('file', ('b.png', b'2', 'image/png'))],
    )
    assert two.status_code == 422 and two.json()['reasonCode'] == 'TOO_MANY_FILES'
    extra = await client.post(
        '/file-assets/uploads',
        data={'purpose': 'notice.image', 'bucket': 'x'},
        files={'file': ('a.png', b'1', 'image/png')},
    )
    assert extra.status_code == 422 and extra.json()['reasonCode'] == 'UNKNOWN_FIELD'


async def test_unavailable_storage_answers_503_even_for_revalidation(client, runtime):
    body = (await _upload(client, owner_id='10')).json()
    etag = (await client.get(body['contentUrl'])).headers['etag']
    runtime.ownership.state = OwnershipState.INVALID
    for request in (
        client.get(body['contentUrl'], headers={'If-None-Match': etag}),
        client.post('/file-assets/metadata:batch', json={'assetIds': [body['assetId']]}),
        _upload(client),
    ):
        response = await request
        assert response.status_code == 503 and response.json()['reasonCode'] == 'OWNERSHIP_INVALID'
        assert response.headers['retry-after'] == '30'


async def test_missing_object_is_503_not_404(client, storage):
    body = (await _upload(client, owner_id='10')).json()
    storage.objects.clear()
    response = await client.get(body['contentUrl'])
    assert response.status_code == 503 and response.json()['reasonCode'] == 'OBJECT_MISSING'


async def test_download_capacity_exhaustion(client, runtime):
    body = (await _upload(client, owner_id='10')).json()
    held = [await runtime.download_slots.acquire() for _ in range(runtime.download_slots.capacity)]
    response = await client.get(body['contentUrl'])
    assert response.status_code == 503 and response.json()['reasonCode'] == 'CAPACITY_EXHAUSTED'
    for slot in held:
        slot.release()
    assert (await client.get(body['contentUrl'])).status_code == 200
    assert runtime.metrics.in_use['download'] == 0


# ------------------------------------------------------------- upload limits ---


async def _raw_app_calls(limit_app_hits):
    async def app(scope, receive, send):
        limit_app_hits.append(scope['path'])
        while True:
            message = await receive()
            if not message.get('more_body'):
                break
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})

    return app


async def test_declared_content_length_over_cap_is_rejected_before_the_app():
    hits: list[str] = []
    app = UploadLimitASGIMiddleware(
        await _raw_app_calls(hits), limits={'/file-assets/uploads': 100}, receive_timeout_seconds=5
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://t') as client:
        response = await client.post('/file-assets/uploads', content=b'x' * 101)
    assert response.status_code == 413 and response.json()['reasonCode'] == 'REQUEST_TOO_LARGE' and hits == []


async def test_streamed_body_without_length_is_counted(app, client):
    async def body():
        # Well-formed multipart sent chunked (no Content-Length): the cap counts received bytes.
        yield b'--x\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nnotice.image\r\n'
        yield b'--x\r\nContent-Disposition: form-data; name="file"; filename="a.png"\r\n\r\n'
        for _ in range(10):
            yield b'x' * 1024

    response = await client.post(
        '/file-assets/uploads', content=body(), headers={'content-type': 'multipart/form-data; boundary=x'}
    )
    assert response.status_code == 413


async def test_slow_body_hits_the_receive_deadline(client):
    async def body():
        yield b'--x\r\n'
        await asyncio.sleep(1)
        yield b'more'

    response = await client.post(
        '/file-assets/uploads', content=body(), headers={'content-type': 'multipart/form-data; boundary=x'}
    )
    assert response.status_code == 408 and response.json()['reasonCode'] == 'RECEIVE_TIMEOUT'


async def test_limits_match_route_paths_under_root_path():
    hits: list[str] = []
    app = UploadLimitASGIMiddleware(
        await _raw_app_calls(hits), limits={'/file-assets/uploads': 10}, receive_timeout_seconds=5
    )
    scope_root = {'root_path': '/dev-api'}

    async def wrapped(scope, receive, send):
        scope = dict(scope, path='/dev-api' + scope['path'], **scope_root)
        await app(scope, receive, send)

    async with AsyncClient(transport=ASGITransport(app=wrapped), base_url='http://t') as client:
        response = await client.post('/file-assets/uploads', content=b'x' * 11)
    assert response.status_code == 413


# ----------------------------------------------------------------------- CSRF ---


class _Security:
    async def verify_access_token(self, token, **kwargs):
        if token == 'expired':
            raise ValueError('expired')
        return {'sub': f'user:{token}'}

    async def validate_csrf_token(self, subject, token):
        return token == f'csrf-{subject.split(":")[-1]}'


def _csrf_app(root_path: str = ''):
    inner = FastAPI()
    inner.state.security_token_service = _Security()

    @inner.post('/file-assets/uploads')
    async def upload_route():
        return {'ok': True}

    @inner.get('/file-assets/{asset_id}/content')
    async def content_route(asset_id: str):
        return {'ok': asset_id}

    guard = CsrfGuardASGIMiddleware(
        inner,
        enabled=True,
        allowed_origins=['http://localhost'],
        protected_paths=['/auth/refresh'],
        csrf_header_name='X-CSRF-Token',
        csrf_cookie_name='csrf_token',
        protected_write_paths=['/file-assets', '/system/notice'],
        access_cookie_name='ruoyi_at',
    )

    async def app(scope, receive, send):
        if scope['type'] == 'http' and root_path:
            scope = dict(scope, path=root_path + scope['path'], root_path=root_path)
        scope = dict(scope, app=inner)
        await guard(scope, receive, send)

    return app


@pytest.mark.parametrize('root_path', ['', '/dev-api'])
async def test_csrf_write_paths(root_path):
    async with AsyncClient(transport=ASGITransport(app=_csrf_app(root_path)), base_url='http://t') as client:
        # <img> GET with cookies and no Origin/Referer passes.
        assert (await client.get('/file-assets/abc/content', headers={'Cookie': 'ruoyi_at=7'})).status_code == 200
        # Cookie-only write without a CSRF token is refused.
        cookie_only = {'Cookie': 'ruoyi_at=7; csrf_token=csrf-7', 'Origin': 'http://localhost'}
        assert (await client.post('/file-assets/uploads', headers=cookie_only)).status_code == 403
        # Cookie-only write bound to the cookie's subject passes.
        assert (
            await client.post('/file-assets/uploads', headers={**cookie_only, 'X-CSRF-Token': 'csrf-7'})
        ).status_code == 200
        # A token of another subject is refused even with matching cookie/header values.
        stolen = {'Cookie': 'ruoyi_at=7; csrf_token=csrf-8', 'Origin': 'http://localhost', 'X-CSRF-Token': 'csrf-8'}
        assert (await client.post('/file-assets/uploads', headers=stolen)).status_code == 403
        # Bearer plus cookies: bound to the bearer subject.
        mixed = {'Authorization': 'Bearer 8', **stolen}
        assert (await client.post('/file-assets/uploads', headers=mixed)).status_code == 200
        # Foreign origin is refused.
        evil = {**cookie_only, 'X-CSRF-Token': 'csrf-7', 'Origin': 'http://evil.example'}
        assert (await client.post('/file-assets/uploads', headers=evil)).status_code == 403
        # Bearer without cookies (machine clients) keeps the existing exemption.
        assert (await client.post('/file-assets/uploads', headers={'Authorization': 'Bearer 9'})).status_code == 200
        # An unusable access cookie is left to authentication (401 there), not answered by CSRF.
        expired = {'Cookie': 'ruoyi_at=expired; csrf_token=t', 'Origin': 'http://localhost', 'X-CSRF-Token': 't'}
        assert (await client.post('/file-assets/uploads', headers=expired)).status_code == 200


# ----------------------------------------------------------------- rate limit ---


async def test_upload_tier_is_stricter_and_identifiable():
    inner = FastAPI()

    class _Tokens:
        async def extract_user_context_from_token(self, token):
            return {'userId': token}

    inner.state.security_token_service = _Tokens()

    @inner.post('/file-assets/uploads')
    async def upload_route():
        return {'ok': True}

    @inner.post('/system/notice')
    async def write_route():
        return {'ok': True}

    limiter = RateLimitASGIMiddleware(
        inner, upload_paths=['/file-assets/uploads'], upload_ip_limit=100, upload_user_limit=3, write_user_limit=100
    )

    async def app(scope, receive, send):
        await limiter(dict(scope, app=inner), receive, send)

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://t') as client:
        headers = {'Authorization': 'Bearer 5'}
        statuses = [(await client.post('/file-assets/uploads', headers=headers)).status_code for _ in range(4)]
        assert statuses == [200, 200, 200, 429]
        limited = await client.post('/file-assets/uploads', headers=headers)
        assert limited.json()['tier'] == 'upload' and limited.json()['errorCode'] == 42901
        assert (await client.post('/system/notice', headers=headers)).status_code == 200


# ------------------------------------------------------------------- helpers ---


def test_etag_weak_comparison():
    assert etag_matches('W/"abc", "x"', 'abc') and etag_matches('*', 'abc') and not etag_matches('"abd"', 'abc')
    assert not etag_matches(None, 'abc') and not etag_matches('"abc"', '')


def test_content_disposition_never_echoes_header_characters():
    value = content_disposition(False, '季度"报表\r\n.pdf')
    assert '\r' not in value and '\n' not in value and value.count('"') == 2
    assert value.startswith('attachment; filename="download.pdf"; filename*=UTF-8\'\'')
