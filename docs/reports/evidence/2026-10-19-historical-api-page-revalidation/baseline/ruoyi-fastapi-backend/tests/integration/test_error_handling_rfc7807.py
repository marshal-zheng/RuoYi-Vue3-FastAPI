"""
集成测试：RFC 9457 Problem Details 错误处理系统

测试全局异常处理器、HTTP 状态码与追踪头契约。
"""
import pytest
import uuid
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestRFC7807ErrorHandling:
    """测试 RFC 7807 错误响应格式"""
    
    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self, async_client: AsyncClient):
        """测试校验错误返回 422 状态码和 RFC 7807 格式"""
        # 发送无效数据（不需要认证的接口）
        response = await async_client.post(
            "/login",
            json={"username": ""}  # 用户名为空，触发校验错误
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # 验证 RFC 9457 字段
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 422
        assert "detail" in data
        assert "instance" in data
        assert "errorCode" in data
        assert "requestId" in data
        assert "errors" in data  # 校验错误应包含字段级错误
        
        # 验证 Content-Type
        assert response.headers.get("Content-Type") == "application/problem+json"
        
        # 验证 X-Request-Id 响应头
        assert "X-Request-Id" in response.headers
        assert response.headers["X-Request-Id"] == data["requestId"]
    
    @pytest.mark.asyncio
    async def test_authentication_error_returns_401(self, async_client: AsyncClient):
        """测试认证错误返回 401 状态码"""
        # 显式携带非法 token，触发认证错误
        response = await async_client.get(
            "/system/user/list",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401
        data = response.json()
        
        # 验证 RFC 7807 格式
        assert data["status"] == 401
        assert data["errorCode"] == 20001  # UNAUTHORIZED
        assert "requestId" in data
        assert "X-Request-Id" in response.headers
    
    @pytest.mark.asyncio
    async def test_authorization_error_returns_403(self, async_client: AsyncClient):
        """测试权限错误返回 403 状态码"""
        response = await async_client.put(
            "/system/role/changeStatus",
            json={"roleId": 1, "status": "0"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == 403
        assert data["errorCode"] in (20004, 30009)
        assert "requestId" in data
    
    @pytest.mark.asyncio
    async def test_resource_not_found_returns_404(self, async_client: AsyncClient):
        """测试资源不存在返回 404 状态码"""
        response = await async_client.get("/this-endpoint-does-not-exist")

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == 404
        assert "requestId" in data
    
    @pytest.mark.asyncio
    async def test_resource_conflict_returns_409(self, async_client: AsyncClient):
        """测试资源冲突返回 409 状态码"""
        suffix = uuid.uuid4().hex[:8]
        role_data = {
            "roleName": f"Conflict Role {suffix}",
            "roleKey": f"conflict_role_{suffix}",
            "roleSort": 1,
            "status": "0",
        }

        first_response = await async_client.post("/system/role", json=role_data)
        assert first_response.status_code in (200, 201, 409)

        second_response = await async_client.post("/system/role", json=role_data)
        assert second_response.status_code == 409
        data = second_response.json()
        assert data["status"] == 409
        assert "requestId" in data
    
    @pytest.mark.asyncio
    async def test_system_error_returns_500(self, async_client: AsyncClient):
        """测试系统错误返回 500 状态码"""
        # 模拟系统错误
        with patch(
            'modules.system.api.user_controller.UserService.get_user_list_services',
            new_callable=AsyncMock,
        ) as mock_service:
            mock_service.side_effect = Exception("Database connection failed")
            
            response = await async_client.get("/system/user/list")
            
            assert response.status_code == 500
            data = response.json()
            
            assert data["status"] == 500
            assert data["errorCode"] == 50000  # SYSTEM_ERROR
            assert "requestId" in data
            
            # 验证用户消息通用化（不暴露技术细节）
            assert "系统繁忙" in data["title"] or "系统错误" in data["title"]
            assert "Database connection failed" not in data["title"]
            assert "Database connection failed" not in data["detail"]


class TestDualLayerMessage:
    """测试错误响应不泄露未审计开发者信息"""
    
    @pytest.mark.asyncio
    async def test_dev_environment_still_hides_developer_message(self, async_client: AsyncClient):
        """测试开发环境也不返回 developerMessage"""
        with patch('config.env.ErrorHandlingConfig.include_developer_message', True):
            # 触发一个业务错误 - 使用不存在的用户登录
            response = await async_client.post(
                "/login",
                json={"username": "nonexistent", "password": "wrong"}
            )
            
            data = response.json()
            
            if response.status_code >= 400:
                assert "developerMessage" not in data
                assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_no_developer_message_in_prod_environment(self, async_client: AsyncClient):
        """测试生产环境不包含 developerMessage"""
        with patch('config.env.ErrorHandlingConfig.include_developer_message', False):
            # 触发一个业务错误
            response = await async_client.post(
                "/login",
                json={"username": "nonexistent", "password": "wrong"}
            )
            
            if response.status_code >= 400:
                data = response.json()
                
                # 生产环境不应包含 developerMessage
                assert "developerMessage" not in data
                
                # 但应包含用户友好的消息
                assert "title" in data
                assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_system_error_hides_technical_details(self, async_client: AsyncClient):
        """测试系统错误不向用户暴露技术细节"""
        with patch('config.env.ErrorHandlingConfig.include_developer_message', False):
            # 模拟数据库错误
            with patch(
                'modules.system.api.user_controller.UserService.get_user_list_services',
                new_callable=AsyncMock,
            ) as mock_service:
                mock_service.side_effect = Exception("SQL syntax error: SELECT * FROM users WHERE id='; DROP TABLE users;--")
                
                response = await async_client.get("/system/user/list")
                
                assert response.status_code == 500
                data = response.json()
                
                # 用户消息应该通用化
                user_message = data["title"]
                assert "SQL" not in user_message
                assert "DROP TABLE" not in user_message
                assert "系统繁忙" in user_message or "系统错误" in user_message


class TestRequestIdTracking:
    """测试 RequestId 追踪"""
    
    @pytest.mark.asyncio
    async def test_request_id_in_success_response(self, async_client: AsyncClient):
        """测试成功响应只在响应头返回追踪标识，不污染响应体"""
        response = await async_client.get("/captchaImage")

        assert response.status_code == 200
        data = response.json()
        assert "requestId" not in data
        assert "X-Request-Id" in response.headers
    
    @pytest.mark.asyncio
    async def test_request_id_in_error_response(self, async_client: AsyncClient):
        """测试错误响应包含 requestId"""
        response = await async_client.get(
            "/system/user/list",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401
        data = response.json()
        
        # 验证响应体包含 requestId
        assert "requestId" in data
        assert len(data["requestId"]) > 0
        
        # 验证响应头包含 X-Request-Id
        assert "X-Request-Id" in response.headers
        assert response.headers["X-Request-Id"] == data["requestId"]
    
    @pytest.mark.asyncio
    async def test_request_id_consistency(self, async_client: AsyncClient):
        """测试同一请求的 requestId 一致性"""
        response = await async_client.get(
            "/system/user/list", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        
        data = response.json()
        request_id_body = data["requestId"]
        request_id_header = response.headers["X-Request-Id"]
        
        # 响应体和响应头的 requestId 应该一致
        assert request_id_body == request_id_header
        assert response.headers.get_list("X-Request-Id") == [request_id_body]
    
    @pytest.mark.asyncio
    async def test_different_requests_have_different_request_ids(self, async_client: AsyncClient):
        """测试不同请求有不同的 requestId"""
        response1 = await async_client.get("/system/user/list")
        response2 = await async_client.get("/system/role/list")
        
        request_id1 = response1.headers["X-Request-Id"]
        request_id2 = response2.headers["X-Request-Id"]
        
        # 不同请求应该有不同的 requestId
        assert request_id1 != request_id2


class TestHTTPStatusCodes:
    """测试 HTTP 状态码正确性"""
    
    @pytest.mark.asyncio
    async def test_success_returns_2xx(self, async_client: AsyncClient):
        """测试成功操作返回 2xx 状态码"""
        response = await async_client.get("/captchaImage")
        assert 200 <= response.status_code < 300
    
    @pytest.mark.asyncio
    async def test_client_errors_return_4xx(self, async_client: AsyncClient):
        """测试客户端错误返回 4xx 状态码"""
        # 401 未认证
        response = await async_client.get(
            "/system/user/list",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        
        # 422 校验错误
        response = await async_client.post(
            "/login",
            json={"username": ""}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_server_errors_return_5xx(self, async_client: AsyncClient):
        """测试服务器错误返回 5xx 状态码"""
        with patch(
            'modules.system.api.user_controller.UserService.get_user_list_services',
            new_callable=AsyncMock,
        ) as mock_service:
            mock_service.side_effect = Exception("Internal server error")
            
            response = await async_client.get("/system/user/list")
            
            assert 500 <= response.status_code < 600
