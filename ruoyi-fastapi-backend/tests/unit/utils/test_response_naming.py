import json
from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from utils.response_util import ResponseUtil
from config.error_codes import ErrorCode, ErrorType


def _assert_no_snake_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            assert "_" not in key, f"snake_case key leaked: {key}"
            _assert_no_snake_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_snake_keys(item)


@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.url.path = "/api/system/user"
    return request


@pytest.fixture
def mock_request_id():
    with patch('utils.response_util.get_request_id', return_value='test-request-id-123'):
        yield


def test_success_response_no_snake_keys(mock_request_id):
    response = ResponseUtil.success(
        data={
            "user_id": 1,
            "user_name": "admin",
            "profile": {"created_at": "2025-01-01"},
            "roles": [{"role_id": 1, "role_name": "admin"}],
        },
        message="ok",
    )

    payload = json.loads(response.body.decode("utf-8"))
    _assert_no_snake_keys(payload)


def test_problem_details_no_snake_keys(mock_request, mock_request_id):
    response = ResponseUtil.problem_details(
        request=mock_request,
        error_code=ErrorCode.USER_ALREADY_EXISTS,
        user_message="用户名已存在",
        developer_message="user already exists",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_ALREADY_EXISTS",
        data={"user_id": 1, "user_name": "admin"},
    )

    payload = json.loads(response.body.decode("utf-8"))
    _assert_no_snake_keys(payload)
