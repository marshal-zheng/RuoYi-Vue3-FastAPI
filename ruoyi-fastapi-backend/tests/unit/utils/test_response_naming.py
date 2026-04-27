import json
from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from utils.response_util import ResponseUtil


def _assert_no_snake_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            assert '_' not in key, f'snake_case key leaked: {key}'
            _assert_no_snake_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_snake_keys(item)


@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.url.path = '/api/system/user'
    return request


@pytest.fixture
def trace_context():
    with (
        patch('utils.response_util.get_request_id', return_value='req-123'),
        patch('utils.response_util.get_trace_id', return_value='trace-456'),
        patch('config.env.ErrorHandlingConfig.problem_type_base_url', 'http://localhost/problems'),
    ):
        yield


def test_success_response_no_snake_keys(trace_context):
    response = ResponseUtil.ok_resource(
        {
            'user_id': 1,
            'user_name': 'admin',
            'profile': {'created_at': '2025-01-01'},
            'roles': [{'role_id': 1, 'role_name': 'admin'}],
        }
    )

    payload = json.loads(response.body.decode('utf-8'))
    _assert_no_snake_keys(payload)


def test_problem_details_no_snake_keys(mock_request, trace_context):
    response = ResponseUtil.problem_details(
        request=mock_request,
        http_status=409,
        title='用户名已存在',
        detail='该用户名已被使用，请更换后重试',
        type_slug='user-already-exists',
        error_code=30006,
        errors=[{'field': 'userName', 'message': '已存在', 'code': 'value_error'}],
    )

    payload = json.loads(response.body.decode('utf-8'))
    _assert_no_snake_keys(payload)
