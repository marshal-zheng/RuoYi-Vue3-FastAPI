"""HTTP auth, contract privacy and SSE transport checks without a database or model."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware

from config.env import RemarkAISettings
from exceptions.exception import AuthException
from exceptions.handle import handle_exception
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.api import remark_ai_controller as controller
from modules.system.application.services.remark_ai_service import RemarkAIService
from tests.unit.services.test_remark_ai import chunk, provider_service, request, text_root
from utils.log_util import logger


@pytest.fixture
def http_context():
    app = FastAPI()
    handle_exception(app)
    app.add_middleware(GZipMiddleware, minimum_size=1)
    app.include_router(controller.remark_ai_router)
    actor = CurrentUserModel(permissions=['system:post:add'], roles=[], user=UserInfoModel(userId=2, userName='editor'))

    async def get_user():
        return actor

    app.dependency_overrides[controller.get_current_user] = get_user
    service, stream, requests = provider_service(
        [
            chunk(json.dumps(text_root())),
            chunk(finish='stop'),
            b'data: [DONE]\n\n',
        ]
    )
    app.dependency_overrides[controller.provide_remark_ai_service] = lambda: service
    with TestClient(app) as client:
        yield client, app, actor, stream, requests


def test_status_discloses_only_availability(http_context):
    client, _, _, _, requests = http_context
    response = client.get('/system/remark/ai/status')
    assert response.status_code == 200
    assert response.json() == {'available': True}
    assert not requests


def test_success_has_sse_events_and_does_not_gzip_buffer(http_context):
    client, _, _, stream, requests = http_context
    response = client.post('/system/remark/ai/generate', json=request().model_dump(mode='json'))
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert response.headers['content-encoding'] == 'identity'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-accel-buffering'] == 'no'
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[0]['type'] == 'delta'
    assert events[-1]['type'] == 'result'
    assert len(requests) == 1
    assert stream.closed


def test_unconfigured_service_returns_problem_before_stream_starts(http_context):
    client, app, _, _, requests = http_context
    unconfigured = RemarkAIService(RemarkAISettings(deepseek_api_key=''))
    app.dependency_overrides[controller.provide_remark_ai_service] = lambda: unconfigured
    assert client.get('/system/remark/ai/status').json() == {'available': False}
    response = client.post('/system/remark/ai/generate', json=request().model_dump(mode='json'))
    assert response.status_code == 503
    assert response.headers['content-type'].startswith('application/problem+json')
    assert '尚未配置' in response.json()['detail']
    assert not requests


def test_scene_permissions_are_checked_before_provider_call(http_context):
    client, _, _, _, requests = http_context
    response = client.post('/system/remark/ai/generate', json=request(scene='user', context={}).model_dump(mode='json'))
    assert response.status_code == 403
    assert not requests


def test_authentication_is_required(http_context):
    client, app, _, _, requests = http_context

    async def unauthorized():
        raise AuthException()

    app.dependency_overrides[controller.get_current_user] = unauthorized
    assert client.get('/system/remark/ai/status').status_code == 401
    assert client.post('/system/remark/ai/generate', json=request().model_dump(mode='json')).status_code == 401
    assert not requests


def test_context_rejection_and_validation_logs_never_echo_private_values(http_context):
    client, _, _, _, requests = http_context
    logs = []
    sink = logger.add(lambda message: logs.append(str(message)))
    try:
        body = request().model_dump(mode='json')
        body['context'] = {'password': 'PRIVATE-CONTEXT-SECRET'}
        body['instruction'] = 'PRIVATE-PROMPT-SECRET'
        response = client.post('/system/remark/ai/generate', json=body)
    finally:
        logger.remove(sink)
    assert response.status_code == 422
    assert 'PRIVATE-' not in response.text
    assert 'PRIVATE-' not in '\n'.join(logs)
    assert not requests
