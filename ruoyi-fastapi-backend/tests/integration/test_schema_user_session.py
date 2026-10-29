"""Schema consumer contract through the real HTTP/DI/CQRS/repository stack.

The existing integration lifespan owns a disposable SQLite database and Redis
fixture. Authentication is injected; no developer or production user data is used.
"""

import pytest

from common.remark_document_v1 import plain_to_remark
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.application.services.login_service import LoginService
from modules.identity.ports import get_current_user
from server import app


@pytest.fixture
async def schema_user_http(remark_http):
    # Mirror the real admin identity's role list so GetDataScope evaluates the
    # actual all-data rule; the shared remark fixture supplies no role entities.
    async def actor():
        return CurrentUserModel(
            permissions=['*:*:*'],
            roles=['admin'],
            user=UserInfoModel(
                userId=1,
                userName='admin',
                nickName='admin',
                role=[RoleModel(roleId=1, roleKey='admin', roleName='Admin', dataScope='1')],
            ),
        )

    previous = {key: app.dependency_overrides[key] for key in (get_current_user, LoginService.get_current_user)}
    for key in previous:
        app.dependency_overrides[key] = actor
    try:
        yield remark_http
    finally:
        app.dependency_overrides.update(previous)


async def test_user_session_nested_write_read_reconcile_and_field_errors(schema_user_http):
    client = schema_user_http
    role = await client.post(
        '/system/role', json={'roleName': 'Schema', 'roleKey': 'schema', 'roleSort': 1, 'status': '0'}
    )
    assert role.status_code == 201, role.text
    role_id = role.json()['roleId']
    post = await client.post(
        '/system/post', json={'postName': 'Schema', 'postCode': 'schema', 'postSort': 1, 'status': '0'}
    )
    assert post.status_code == 201, post.text
    post_id = post.json()['postId']
    document = plain_to_remark('Schema 用户备注', identity_key='schema:integration:remark')
    fields = {
        'userName': 'schema_user',
        'nickName': 'Schema User',
        'password': 'admin123',
        'status': '0',
        'sex': '0',
        'email': 'schema@example.com',
        'phonenumber': '13800138099',
        'roleIds': [role_id],
        'postIds': [post_id],
        'remark': document,
    }
    created = await client.post('/system/user', json=fields)
    assert created.status_code == 201, created.text
    detail = created.json()
    user_id = detail['data']['userId']
    assert created.headers['location'].endswith(f'/system/user/{user_id}')
    assert detail['roleIds'] == [role_id] and detail['postIds'] == [post_id]
    assert detail['data']['remark'] == document
    assert 'password' not in detail['data']
    read = await client.get(f'/system/user/{user_id}')
    assert read.status_code == 200 and read.json() == detail

    # Unknown create results recover identity through the real list DTO, then
    # verify the captured account name against an independent detail read.
    listed = await client.get('/system/user/list', params={'userName': 'schema_user', 'page': 1, 'pageSize': 100})
    assert listed.status_code == 200, listed.text
    matches = [user for user in listed.json()['items'] if user['userName'] == fields['userName']]
    assert len(matches) == 1 and matches[0]['userId'] == user_id
    recovered = await client.get(f'/system/user/{matches[0]["userId"]}')
    assert recovered.status_code == 200
    assert recovered.json()['data']['userName'] == fields['userName']

    duplicate = await client.post('/system/user', json=fields)
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()['errorCode'] == 30006

    editable = {key: value for key, value in fields.items() if key != 'password'}
    update = await client.put('/system/user', json={**editable, 'userId': user_id, 'nickName': 'Updated'})
    assert update.status_code == 200, update.text
    # A lost write response is reconciled with a fresh authoritative GET, not a resend.
    reconciled = await client.get(f'/system/user/{user_id}')
    assert reconciled.status_code == 200 and reconciled.json() == update.json()
    assert reconciled.json()['data']['nickName'] == 'Updated'

    forged = await client.put('/system/user', json={**editable, 'userId': user_id, 'remarkText': 'forged'})
    assert forged.status_code == 422, forged.text
    unchanged = await client.get(f'/system/user/{user_id}')
    assert unchanged.json() == reconciled.json()


async def test_user_session_permissions_reject_writes_before_mutation(remark_http):
    client = remark_http
    created = await client.post(
        '/system/user', json={'userName': 'schema_denied', 'nickName': 'Kept', 'password': 'admin123'}
    )
    assert created.status_code == 201, created.text
    user_id = created.json()['data']['userId']

    async def denied_actor():
        return CurrentUserModel(
            permissions=[], roles=[], user=UserInfoModel(userId=1, userName='admin', nickName='admin')
        )

    previous = {key: app.dependency_overrides[key] for key in (get_current_user, LoginService.get_current_user)}
    for key in previous:
        app.dependency_overrides[key] = denied_actor
    try:
        denied = await client.put(
            '/system/user', json={'userId': user_id, 'userName': 'schema_denied', 'nickName': 'Forbidden'}
        )
        assert denied.status_code == 403, denied.text
        denied_create = await client.post(
            '/system/user', json={'userName': 'never_created', 'nickName': 'Forbidden', 'password': 'admin123'}
        )
        assert denied_create.status_code == 403, denied_create.text
        denied_read = await client.get(f'/system/user/{user_id}')
        assert denied_read.status_code == 403, denied_read.text
    finally:
        app.dependency_overrides.update(previous)
    authoritative = await client.get(f'/system/user/{user_id}')
    assert authoritative.status_code == 200
    assert authoritative.json()['data']['nickName'] == 'Kept'
