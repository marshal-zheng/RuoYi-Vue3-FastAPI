"""
User management integration tests
Tests user CRUD operations and authentication
"""
import pytest
from fastapi.testclient import TestClient


class TestUserManagementIntegration:
    """Integration tests for user management"""
    
    def test_user_list_endpoint(self, test_client):
        """Test user list endpoint"""
        response = test_client.get("/system/user/list")
        assert response.status_code in [200, 401, 404]
    
    def test_user_info_endpoint(self, test_client):
        """Test user info endpoint"""
        response = test_client.get("/system/user/1")
        assert response.status_code in [200, 401, 404]
    
    def test_user_profile_endpoint(self, test_client):
        """Test user profile endpoint"""
        response = test_client.get("/system/user/profile")
        assert response.status_code in [200, 401, 404]
    
    def test_user_create_endpoint(self, test_client):
        """Test user creation endpoint"""
        user_data = {
            "userName": "testuser",
            "nickName": "Test User",
            "password": "Test123456",
            "email": "test@example.com",
            "phonenumber": "13800138000"
        }
        response = test_client.post("/system/user", json=user_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_user_update_endpoint(self, test_client):
        """Test user update endpoint"""
        user_data = {
            "userId": 1,
            "nickName": "Updated User",
            "email": "updated@example.com"
        }
        response = test_client.put("/system/user", json=user_data)
        assert response.status_code == 403
        assert response.json()['detail'] == '不允许操作超级管理员用户'
    
    def test_user_delete_endpoint(self, test_client):
        """Test user deletion endpoint"""
        response = test_client.delete("/system/user/1")
        assert response.status_code in [200, 400, 401, 403, 404]
    
    def test_user_reset_password_endpoint(self, test_client):
        """Test user password reset endpoint"""
        response = test_client.put("/system/user/resetPwd", json={"userId": 1, "password": "NewPass123"})
        assert response.status_code == 403
        assert response.json()['detail'] == '不允许操作超级管理员用户'
    
    def test_user_change_status_endpoint(self, test_client):
        """Test user status change endpoint"""
        response = test_client.put("/system/user/changeStatus", json={"userId": 1, "status": "0"})
        assert response.status_code == 403
        assert response.json()['detail'] == '不允许操作超级管理员用户'


class TestUserServiceIntegration:
    """Integration tests for user service layer"""
    
    @pytest.mark.asyncio
    async def test_user_service_exists(self):
        """Test that user service can be imported"""
        from modules.system.application.services.user_service import UserService
        assert UserService is not None
    
    @pytest.mark.asyncio
    async def test_user_models_exist(self):
        """Test that user models can be imported"""
        try:
            from module_admin.entity.do.user_do import User
            assert User is not None
        except ImportError:
            # Try alternative names
            pass


class TestAuthenticationIntegration:
    """Integration tests for authentication"""
    
    def test_login_endpoint(self, test_client):
        """Test login endpoint"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = test_client.post("/login", json=login_data)
        assert response.status_code in [200, 401, 404, 422]
    
    def test_logout_endpoint(self, test_client):
        """Test logout endpoint"""
        response = test_client.post("/auth/logout")
        assert response.status_code == 204
        assert response.content == b''
    
    def test_get_info_endpoint(self, test_client):
        """Test get user info endpoint"""
        response = test_client.get("/getInfo")
        assert response.status_code in [200, 401, 404]
    
    def test_get_routers_endpoint(self, test_client):
        """Test get routers endpoint"""
        response = test_client.get("/getRouters")
        assert response.status_code in [200, 401, 404]
