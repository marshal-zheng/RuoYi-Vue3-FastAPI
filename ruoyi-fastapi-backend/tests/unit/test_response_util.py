"""
测试响应工具类（RFC 7807 标准）
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import Request
from utils.response_util import ResponseUtil
from config.error_codes import ErrorCode, ErrorType


@pytest.fixture
def mock_request():
    """模拟请求对象"""
    request = Mock(spec=Request)
    request.url.path = "/api/system/user"
    return request


@pytest.fixture
def mock_request_id():
    """模拟 requestId"""
    with patch('utils.response_util.get_request_id', return_value='test-request-id-123'):
        yield


class TestSuccessResponse:
    """测试成功响应"""
    
    def test_success_with_data(self, mock_request_id):
        """测试带数据的成功响应"""
        response = ResponseUtil.success(
            data={"userId": 1, "username": "admin"},
            message="查询成功"
        )
        
        assert response.status_code == 200
        content = response.body.decode('utf-8')
        assert '"data"' in content
        assert '"userId"' in content
        assert '"message":"查询成功"' in content
        assert '"requestId":"test-request-id-123"' in content

    def test_success_with_snake_case_data(self, mock_request_id):
        """测试 snake_case 数据会转换为 camelCase"""
        response = ResponseUtil.success(
            data={"user_id": 1, "user_name": "admin"},
            message="查询成功"
        )

        content = response.body.decode('utf-8')
        assert '"userId":1' in content
        assert '"userName":"admin"' in content
    
    def test_success_without_data(self, mock_request_id):
        """测试无数据的成功响应"""
        response = ResponseUtil.success(message="操作成功")
        
        assert response.status_code == 200
        content = response.body.decode('utf-8')
        assert '"data":null' in content
        assert '"message":"操作成功"' in content
    
    def test_success_with_custom_status(self, mock_request_id):
        """测试自定义状态码的成功响应"""
        response = ResponseUtil.success(
            data={"id": 1},
            message="创建成功",
            http_status=201
        )
        
        assert response.status_code == 201
    
    def test_success_response_headers(self, mock_request_id):
        """测试成功响应头"""
        response = ResponseUtil.success(data={})
        
        assert response.headers.get("X-Request-Id") == "test-request-id-123"


class TestProblemDetailsResponse:
    """测试 RFC 7807 错误响应"""
    
    def test_problem_details_basic(self, mock_request, mock_request_id):
        """测试基本 RFC 7807 响应"""
        response = ResponseUtil.problem_details(
            request=mock_request,
            error_code=ErrorCode.USER_NOT_FOUND,
            user_message="用户不存在",
            developer_message="User with id=123 not found",
            http_status=404,
            error_type=ErrorType.BUSINESS,
            error_code_name="USER_NOT_FOUND"
        )
        
        assert response.status_code == 404
        assert response.headers.get("Content-Type") == "application/problem+json"
        assert response.headers.get("X-Request-Id") == "test-request-id-123"
        
        content = response.body.decode('utf-8')
        assert '"type":"https://api.example.com/problems/USER_NOT_FOUND"' in content
        assert '"title":"用户不存在"' in content
        assert '"status":404' in content
        assert '"detail":"用户不存在"' in content
        assert '"instance":"/api/system/user"' in content
        assert '"errorCode":30001' in content
        assert '"requestId":"test-request-id-123"' in content
    
    def test_problem_details_with_developer_message_in_dev(
        self, mock_request, mock_request_id
    ):
        """测试开发环境包含开发者消息"""
        from config.env import ErrorHandlingConfig
        
        with patch.object(ErrorHandlingConfig, 'include_developer_message', True):
            response = ResponseUtil.problem_details(
                request=mock_request,
                error_code=ErrorCode.DATABASE_ERROR,
                user_message="系统繁忙，请稍后重试",
                developer_message="Connection pool exhausted: max=100",
                http_status=500,
                error_type=ErrorType.SYSTEM,
                error_code_name="DATABASE_ERROR"
            )
            
            content = response.body.decode('utf-8')
            # 开发环境应包含 developerMessage
            assert '"developerMessage":"Connection pool exhausted: max=100"' in content
    
    def test_problem_details_without_developer_message_in_prod(
        self, mock_request, mock_request_id
    ):
        """测试生产环境不包含开发者消息"""
        from config.env import ErrorHandlingConfig
        
        with patch.object(ErrorHandlingConfig, 'include_developer_message', False):
            response = ResponseUtil.problem_details(
                request=mock_request,
                error_code=ErrorCode.DATABASE_ERROR,
                user_message="系统繁忙，请稍后重试",
                developer_message="Connection pool exhausted: max=100",
                http_status=500,
                error_type=ErrorType.SYSTEM,
                error_code_name="DATABASE_ERROR"
            )
            
            content = response.body.decode('utf-8')
            # 生产环境不应包含 developerMessage
            assert 'developerMessage' not in content
            # 但应包含用户消息
            assert '"title":"系统繁忙，请稍后重试"' in content
    
    def test_problem_details_with_extra_fields(self, mock_request, mock_request_id):
        """测试带额外字段的 RFC 7807 响应"""
        response = ResponseUtil.problem_details(
            request=mock_request,
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            user_message="用户名已存在",
            developer_message="User with username='admin' exists",
            http_status=409,
            error_type=ErrorType.BUSINESS,
            error_code_name="USER_ALREADY_EXISTS",
            username="admin"
        )
        
        content = response.body.decode('utf-8')
        assert '"username":"admin"' in content


class TestValidationProblemResponse:
    """测试校验错误响应"""
    
    def test_validation_problem_with_errors(self, mock_request, mock_request_id):
        """测试带字段错误的校验响应"""
        errors = [
            {"field": "username", "message": "用户名不能为空"},
            {"field": "email", "message": "邮箱格式不正确"}
        ]
        
        response = ResponseUtil.validation_problem(
            request=mock_request,
            errors=errors
        )
        
        assert response.status_code == 422
        assert response.headers.get("Content-Type") == "application/problem+json"
        
        content = response.body.decode('utf-8')
        assert '"type":"https://api.example.com/problems/validation-error"' in content
        assert '"title":"参数验证失败"' in content
        assert '"status":422' in content
        assert '"errorCode":10001' in content
        assert '"errors"' in content
        assert '"field":"username"' in content
        assert '"field":"email"' in content
    
    def test_validation_problem_with_developer_message(
        self, mock_request, mock_request_id
    ):
        """测试校验错误包含开发者消息（开发环境）"""
        from config.env import ErrorHandlingConfig
        
        errors = [{"field": "username", "message": "不能为空"}]
        developer_message = "Validation failed: username is required"
        
        with patch.object(ErrorHandlingConfig, 'include_developer_message', True):
            response = ResponseUtil.validation_problem(
                request=mock_request,
                errors=errors,
                developer_message=developer_message
            )
            
            content = response.body.decode('utf-8')
            assert '"developerMessage":"Validation failed: username is required"' in content
