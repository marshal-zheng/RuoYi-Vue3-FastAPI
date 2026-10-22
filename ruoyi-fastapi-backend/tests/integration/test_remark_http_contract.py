"""Remark admission and transactions through real HTTP, DI and repositories (isolated SQLite)."""

import pytest

from common.remark_document_v1 import plain_to_remark
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from module_generator.entity.do.gen_do import GenTableDO
from modules.identity.application.services.login_service import LoginService
from server import app

CASES = [
    (
        '/system/user',
        'userId',
        {'userName': 'remark_user', 'nickName': 'Remark', 'password': 'admin123', 'status': '0'},
    ),
    ('/system/role', 'roleId', {'roleName': 'Remark', 'roleKey': 'remark_role', 'roleSort': 1, 'status': '0'}),
    ('/system/post', 'postId', {'postName': 'Remark', 'postCode': 'remark_post', 'postSort': 1, 'status': '0'}),
    ('/system/dict/type', 'dictId', {'dictName': 'Remark', 'dictType': 'remark_type', 'status': '0'}),
    (
        '/system/dict/data',
        'dictCode',
        {'dictLabel': 'Remark', 'dictValue': 'a', 'dictType': 'remark_type', 'dictSort': 1, 'status': '0'},
    ),
    (
        '/system/config',
        'configId',
        {'configName': 'Remark', 'configKey': 'remark.config', 'configValue': 'keep', 'configType': 'N'},
    ),
]


def resource(payload):
    return payload.get('data', payload)


@pytest.mark.parametrize(('path', 'identity', 'fields'), CASES)
async def test_six_system_http_json_roundtrip_omission_clear_and_readonly(remark_http, path, identity, fields):
    client = remark_http
    if path.endswith('/data'):
        created_type = await client.post(
            '/system/dict/type', json={'dictName': 'Remark', 'dictType': 'remark_type', 'status': '0'}
        )
        assert created_type.status_code == 201, created_type.text
    doc = plain_to_remark('  中文😀\n\n=1+1  ', identity_key=f'{path}:integration:remark')
    created = await client.post(path, json={**fields, 'remark': doc})
    assert created.status_code == 201, created.text
    item = resource(created.json())
    pk = item[identity]
    assert item['remark'] == doc
    assert item['remarkText'] == '  中文😀\n\n=1+1  '
    before = await client.get(f'{path}/{pk}')
    assert before.status_code == 200, before.text
    assert resource(before.json())['remark'] == doc
    fields = {key: value for key, value in fields.items() if key != 'password'}
    update = await client.put(path, json={**fields, identity: pk})
    assert update.status_code == 200, update.text
    assert resource(update.json())['remark'] == doc
    invalid = await client.put(path, json={**fields, identity: pk, 'remark': 'not-a-document'})
    assert invalid.status_code == 422, invalid.text
    forged = await client.put(path, json={**fields, identity: pk, 'remarkText': 'forged'})
    assert forged.status_code == 422, forged.text
    still = resource((await client.get(f'{path}/{pk}')).json())
    assert still['remark'] == doc
    if path in {'/system/user', '/system/role'}:
        changed = await client.put(f'{path}/changeStatus', json={identity: pk, 'status': '1'})
        assert changed.status_code == 200, changed.text
        assert resource((await client.get(f'{path}/{pk}')).json())['remark'] == doc
    cleared = await client.put(path, json={**fields, identity: pk, 'remark': None})
    assert cleared.status_code == 200, cleared.text
    final = resource((await client.get(f'{path}/{pk}')).json())
    assert final['remark'] is None
    assert final['remarkText'] == ''


async def test_generator_configuration_json_roundtrip_and_readonly(remark_http):
    fields = {
        'tableId': 200,
        'tableName': 'test_note',
        'tableComment': 'Notes',
        'className': 'TestNote',
        'packageName': 'module_demo',
        'moduleName': 'demo',
        'businessName': 'note',
        'functionName': 'Notes',
        'functionAuthor': 'test',
        'tplCategory': 'crud',
        'tplWebType': 'element-plus',
        'columns': [],
    }
    async with app.state.container._session_factory() as session:
        session.add(GenTableDO(table_id=200, table_name='test_note', table_comment='Notes'))
        await session.commit()
    doc = plain_to_remark('generator\n😀', identity_key='gen_table:200:remark')
    response = await remark_http.put('/tool/gen', json={**fields, 'remark': doc})
    assert response.status_code == 200, response.text
    assert response.json()['info']['remark'] == doc
    assert response.json()['info']['remarkText'] == 'generator\n😀'
    omitted = await remark_http.put('/tool/gen', json=fields)
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()['info']['remark'] == doc
    forged = await remark_http.put('/tool/gen', json={**fields, 'remarkText': 'forged'})
    assert forged.status_code == 422, forged.text
    cleared = await remark_http.put('/tool/gen', json={**fields, 'remark': None})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()['info']['remark'] is None


async def test_user_detail_real_nested_roles_posts_keep_documents_and_server_text(remark_http):
    doc = plain_to_remark('nested 中文😀', identity_key='nested:integration:remark')
    role = await remark_http.post(
        '/system/role',
        json={'roleName': 'Nested', 'roleKey': 'nested', 'roleSort': 1, 'status': '0', 'remark': doc},
    )
    assert role.status_code == 201, role.text
    role_id = resource(role.json())['roleId']
    post = await remark_http.post(
        '/system/post',
        json={'postName': 'Nested', 'postCode': 'nested', 'postSort': 1, 'status': '0', 'remark': doc},
    )
    assert post.status_code == 201, post.text
    post_id = resource(post.json())['postId']
    user = await remark_http.post(
        '/system/user',
        json={
            'userName': 'nested_user',
            'nickName': 'Nested',
            'password': 'admin123',
            'roleIds': [role_id],
            'postIds': [post_id],
        },
    )
    assert user.status_code == 201, user.text
    user_id = resource(user.json())['userId']
    detail = await remark_http.get(f'/system/user/{user_id}')
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert payload['data']['role'][0]['remark'] == doc
    assert payload['data']['role'][0]['remarkText'] == 'nested 中文😀'
    for collection, key, identity in [('roles', 'roleId', role_id), ('posts', 'postId', post_id)]:
        option = next(item for item in payload[collection] if item[key] == identity)
        assert option['remark'] == doc
        assert option['remarkText'] == 'nested 中文😀'


async def test_current_identity_http_projects_nested_role_remark(remark_http):
    doc = plain_to_remark('identity role', identity_key='role:2:remark')

    async def actor():
        return CurrentUserModel(
            permissions=['*:*:*'],
            roles=['admin'],
            user=UserInfoModel(userId=1, role=[{'roleId': 2, 'remark': doc, 'remarkText': 'forged'}]),
        )

    app.dependency_overrides[LoginService.get_current_user] = actor
    response = await remark_http.get('/getInfo')
    assert response.status_code == 200, response.text
    nested = resource(response.json())['user']['role'][0]
    assert nested['remark'] == doc
    assert nested['remarkText'] == 'identity role'
