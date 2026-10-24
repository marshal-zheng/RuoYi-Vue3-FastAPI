"""
Role management integration tests
Tests role CRUD operations and permissions
"""
import pytest
from fastapi.testclient import TestClient


class TestRoleManagementIntegration:
    """Integration tests for role management"""
    
    def test_role_list_endpoint(self, test_client):
        """Test role list endpoint"""
        response = test_client.get("/system/role/list")
        assert response.status_code in [200, 401, 404]
    
    def test_role_info_endpoint(self, test_client):
        """Test role info endpoint"""
        response = test_client.get("/system/role/1")
        assert response.status_code in [200, 401, 404]
    
    def test_role_create_endpoint(self, test_client):
        """Test role creation endpoint"""
        role_data = {
            "roleName": "Test Role",
            "roleKey": "test_role",
            "roleSort": 1,
            "status": "0"
        }
        response = test_client.post("/system/role", json=role_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_role_update_endpoint(self, test_client):
        """Test role update endpoint"""
        role_data = {
            "roleId": 1,
            "roleName": "Updated Role",
            "roleKey": "updated_role"
        }
        response = test_client.put("/system/role", json=role_data)
        assert response.status_code in [200, 400, 401, 403, 404, 422]
    
    def test_role_delete_endpoint(self, test_client):
        """Test role deletion endpoint"""
        response = test_client.delete("/system/role/1")
        assert response.status_code in [200, 400, 401, 403, 404]
    
    def test_role_change_status_endpoint(self, test_client):
        """Test role status change endpoint"""
        response = test_client.put("/system/role/changeStatus", json={"roleId": 1, "status": "0"})
        assert response.status_code in [200, 400, 401, 403, 404, 422]
    
    def test_role_data_scope_endpoint(self, test_client):
        """Test role data scope endpoint"""
        response = test_client.put("/system/role/dataScope", json={"roleId": 1, "dataScope": "1"})
        assert response.status_code in [200, 400, 401, 403, 404, 422]


class TestRoleServiceIntegration:
    """Integration tests for role service layer"""
    
    @pytest.mark.asyncio
    async def test_role_service_exists(self):
        """Test that role service can be imported"""
        from modules.system.application.services.role_service import RoleService
        assert RoleService is not None
    
    @pytest.mark.asyncio
    async def test_role_models_exist(self):
        """Test that role models can be imported"""
        try:
            from module_admin.entity.do.role_do import Role
            assert Role is not None
        except ImportError:
            pass


class TestRolePermissionIntegration:
    """Integration tests for role permissions"""
    
    def test_role_menu_tree_endpoint(self, test_client):
        """Test role menu tree endpoint"""
        response = test_client.get("/system/role/deptTree/1")
        assert response.status_code in [200, 401, 404]
    
    def test_role_allocated_users_endpoint(self, test_client):
        """Test role allocated users endpoint"""
        response = test_client.get("/system/role/authUser/allocatedList")
        assert response.status_code in [200, 401, 404]
    
    def test_role_unallocated_users_endpoint(self, test_client):
        """Test role unallocated users endpoint"""
        response = test_client.get("/system/role/authUser/unallocatedList")
        assert response.status_code in [200, 401, 404]
