"""Integration acceptance tests for system CQRS controller cutover."""

from __future__ import annotations

import uuid

import pytest

from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.application.services.login_service import LoginService
from modules.system.application.behaviors.command_behaviors import CommandEventCollectionBehavior
from modules.system.application.behaviors.query_behaviors import QueryPerformanceBehavior
from server import app


def _build_admin_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['*:*:*'],
        roles=['admin'],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='admin',
            deptId=1,
            status='0',
            delFlag='0',
        ),
    )


def _new_config_payload() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:8]
    return {
        'configName': f'CQRS Config {suffix}',
        'configKey': f'cqrs.cutover.{suffix}',
        'configValue': f'value-{suffix}',
        'configType': 'N',
        'remark': 'cqrs cutover integration test',
    }


@pytest.fixture(scope='function')
def authorized_test_client(test_client):
    async def override_get_current_user() -> CurrentUserModel:
        return _build_admin_user()

    app.dependency_overrides[LoginService.get_current_user] = override_get_current_user
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(LoginService.get_current_user, None)


@pytest.mark.parametrize(
    ('path', 'response_shape'),
    (
        ('/system/config/list', 'page'),
        ('/system/dict/type/list', 'page'),
        ('/system/dept/list', 'collection'),
        ('/system/menu/list', 'collection'),
        ('/system/post/list', 'page'),
        ('/system/notice/list', 'page'),
        ('/system/role/list', 'page'),
        ('/system/user/list', 'page'),
    ),
)
def test_system_read_endpoints_return_success_contract(authorized_test_client, path: str, response_shape: str):
    response = authorized_test_client.get(path)
    assert response.status_code == 200

    payload = response.json()
    request_id = response.headers.get('X-Request-Id') or response.headers.get('request-id')
    assert request_id
    assert response.headers.get_list('X-Request-Id') == [request_id]
    assert payload == ({'items': []} if response_shape == 'collection' else {
        'items': [], 'total': 0, 'page': 1, 'pageSize': 10,
    })


def test_query_pipeline_emits_observation(authorized_test_client, monkeypatch):
    observations: list[dict[str, object]] = []

    def _capture(self, observation: dict[str, object]) -> None:
        observations.append(observation)

    monkeypatch.setattr(QueryPerformanceBehavior, '_record_observation', _capture)

    response = authorized_test_client.get('/system/config/list')
    assert response.status_code == 200

    assert observations
    latest = observations[-1]
    assert latest.get('query_type') == 'GetConfigListQuery'
    assert latest.get('success') is True


def test_command_pipeline_executes_on_config_write(authorized_test_client, monkeypatch):
    seen_commands: list[str] = []
    original_handle = CommandEventCollectionBehavior.handle

    async def _capture(self, request, next_handler):
        seen_commands.append(type(request).__name__)
        return await original_handle(self, request, next_handler)

    monkeypatch.setattr(CommandEventCollectionBehavior, 'handle', _capture)

    payload = _new_config_payload()
    response = authorized_test_client.post('/system/config', json=payload)
    assert response.status_code == 201
    assert response.json()['configId']
    assert response.headers['X-Request-Id']
    assert 'AddConfigCommand' in seen_commands


def test_config_command_and_query_roundtrip_contract(authorized_test_client):
    payload = _new_config_payload()

    create_response = authorized_test_client.post('/system/config', json=payload)
    assert create_response.status_code == 201
    create_payload = create_response.json()
    assert create_payload['configKey'] == payload['configKey']
    assert create_payload['configValue'] == payload['configValue']
    assert create_response.headers['Location'].endswith(f"/system/config/{create_payload['configId']}")
    assert create_response.headers['X-Request-Id']

    query_response = authorized_test_client.get(f"/system/config/configKey/{payload['configKey']}")
    assert query_response.status_code == 200
    query_payload = query_response.json()
    assert query_payload == {'configKey': payload['configKey'], 'configValue': payload['configValue']}
    assert query_response.headers['X-Request-Id']

    duplicate_response = authorized_test_client.post('/system/config', json=payload)
    assert duplicate_response.status_code == 409
    duplicate_payload = duplicate_response.json()
    assert duplicate_payload['status'] == 409
    assert 'requestId' in duplicate_payload
