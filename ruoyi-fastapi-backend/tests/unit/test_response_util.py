import json
from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from utils.response_util import ResponseUtil


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


def _payload(response):
    return json.loads(response.body.decode('utf-8'))


class TestSuccessResponses:
    def test_ok_resource_strips_legacy_message_and_request_id(self, trace_context):
        response = ResponseUtil.ok_resource({'user_id': 1, 'user_name': 'admin'})

        assert response.status_code == 200
        assert response.headers['X-Request-Id'] == 'req-123'
        assert response.headers['X-Trace-Id'] == 'trace-456'

        payload = _payload(response)
        assert payload == {'userId': 1, 'userName': 'admin'}
        assert 'message' not in payload
        assert 'requestId' not in payload

    def test_ok_collection_uses_items(self, trace_context):
        response = ResponseUtil.ok_collection(items=[{'role_id': 1}])

        assert response.status_code == 200
        assert _payload(response) == {'items': [{'roleId': 1}]}

    def test_ok_page_uses_page_contract(self, trace_context):
        response = ResponseUtil.ok_page(items=[{'user_id': 1}], total=12, page=2, page_size=20)

        assert response.status_code == 200
        assert _payload(response) == {'items': [{'userId': 1}], 'total': 12, 'page': 2, 'pageSize': 20}

    def test_ok_cursor_uses_next_cursor(self, trace_context):
        response = ResponseUtil.ok_cursor(items=[{'id': 1}], page_size=50, next_cursor='cursor-1')

        assert response.status_code == 200
        assert _payload(response) == {'items': [{'id': 1}], 'pageSize': 50, 'nextCursor': 'cursor-1'}

    def test_created_resource_sets_absolute_location(self, trace_context):
        response = ResponseUtil.created_resource({'id': 10}, location='https://api.example.com/system/user/10')

        assert response.status_code == 201
        assert response.headers['Location'] == 'https://api.example.com/system/user/10'
        assert _payload(response) == {'id': 10}

    def test_created_resource_requires_absolute_location(self, trace_context):
        with pytest.raises(ValueError):
            ResponseUtil.created_resource({'id': 10}, location='/system/user/10')

    def test_accepted_job_sets_absolute_location(self, trace_context):
        response = ResponseUtil.accepted_job(
            {'jobId': 'job-1', 'status': 'accepted'},
            location='https://api.example.com/jobs/job-1',
        )

        assert response.status_code == 202
        assert response.headers['Location'] == 'https://api.example.com/jobs/job-1'
        assert _payload(response) == {'jobId': 'job-1', 'status': 'accepted'}

    def test_batch_result_whitelists_item_error_fields(self, trace_context):
        response = ResponseUtil.batch_result(
            results=[
                {
                    'itemId': 1,
                    'success': False,
                    'error': {
                        'errorCode': 40901,
                        'title': '冲突',
                        'detail': '已存在',
                        'status': 409,
                        'type': 'ignored',
                    },
                }
            ],
            summary={'total': 1, 'succeeded': 0, 'failed': 1},
        )

        assert response.status_code == 200
        assert _payload(response) == {
            'results': [{'itemId': 1, 'success': False, 'error': {'errorCode': 40901, 'title': '冲突', 'detail': '已存在'}}],
            'summary': {'total': 1, 'succeeded': 0, 'failed': 1},
        }

    def test_no_content_returns_empty_body(self, trace_context):
        response = ResponseUtil.no_content()

        assert response.status_code == 204
        assert response.body == b''
        assert response.headers['X-Request-Id'] == 'req-123'


class TestProblemDetailsResponses:
    def test_problem_details_uses_rfc9457_shape(self, mock_request, trace_context):
        response = ResponseUtil.problem_details(
            request=mock_request,
            http_status=404,
            title='用户不存在',
            detail='未找到该用户',
            type_slug='user-not-found',
            error_code=30001,
        )

        assert response.status_code == 404
        assert response.headers['Content-Type'] == 'application/problem+json'
        assert response.headers['X-Request-Id'] == 'req-123'
        assert response.headers['X-Trace-Id'] == 'trace-456'
        assert _payload(response) == {
            'type': 'http://localhost/problems/user-not-found',
            'title': '用户不存在',
            'status': 404,
            'detail': '未找到该用户',
            'instance': '/api/system/user',
            'errorCode': 30001,
            'requestId': 'req-123',
            'traceId': 'trace-456',
        }

    def test_problem_details_falls_back_to_about_blank(self, mock_request, trace_context):
        response = ResponseUtil.problem_details(
            request=mock_request,
            http_status=500,
            title='系统繁忙，请稍后重试',
            detail='系统繁忙，请稍后重试',
            type_slug=None,
            error_code=50000,
        )

        assert _payload(response)['type'] == 'about:blank'

    def test_validation_problem_preserves_validation_codes(self, mock_request, trace_context):
        response = ResponseUtil.validation_problem(
            request=mock_request,
            errors=[
                {'field': 'userName', 'message': '用户名不能为空', 'code': 'missing'},
                {'field': 'password', 'message': '长度不足', 'code': 'string_too_short'},
            ],
        )

        assert response.status_code == 422
        assert _payload(response) == {
            'type': 'http://localhost/problems/validation-error',
            'title': '参数验证失败',
            'status': 422,
            'detail': '请检查输入字段',
            'instance': '/api/system/user',
            'errorCode': 10001,
            'requestId': 'req-123',
            'traceId': 'trace-456',
            'errors': [
                {'field': 'userName', 'message': '用户名不能为空', 'code': 'missing'},
                {'field': 'password', 'message': '长度不足', 'code': 'string_too_short'},
            ],
        }
