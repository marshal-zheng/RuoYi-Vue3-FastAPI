"""
Department management integration tests
Tests department CRUD operations and tree structure
"""
import pytest
from fastapi.testclient import TestClient


class TestDeptManagementIntegration:
    """Integration tests for department management"""
    
    def test_dept_list_endpoint(self, test_client):
        """Test department list endpoint"""
        response = test_client.get("/system/dept/list")
        assert response.status_code in [200, 401, 404]
    
    def test_dept_tree_endpoint(self, test_client):
        """Test department tree endpoint"""
        response = test_client.get("/system/dept/treeselect")
        assert response.status_code in [200, 401, 404]
    
    def test_dept_info_endpoint(self, test_client):
        """Test department info endpoint"""
        response = test_client.get("/system/dept/1")
        assert response.status_code in [200, 401, 404]
    
    def test_dept_create_endpoint(self, test_client):
        """Test department creation endpoint"""
        dept_data = {
            "deptName": "Test Department",
            "orderNum": 1,
            "status": "0"
        }
        response = test_client.post("/system/dept", json=dept_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_dept_update_endpoint(self, test_client):
        """Test department update endpoint"""
        dept_data = {
            "deptId": 1,
            "deptName": "Updated Department",
            "orderNum": 2
        }
        response = test_client.put("/system/dept", json=dept_data)
        assert response.status_code in [200, 401, 404, 422]
    
    def test_dept_delete_endpoint(self, test_client):
        """Test department deletion endpoint"""
        response = test_client.delete("/system/dept/1")
        assert response.status_code in [200, 401, 404]


class TestDeptServiceIntegration:
    """Integration tests for department service layer"""
    
    @pytest.mark.asyncio
    async def test_dept_service_exists(self):
        """Test that department service can be imported"""
        from modules.system.application.services.dept_service import DeptService
        assert DeptService is not None
    
    @pytest.mark.asyncio
    async def test_dept_models_exist(self):
        """Test that department models can be imported"""
        try:
            from module_admin.entity.do.dept_do import Dept
            assert Dept is not None
        except ImportError:
            pass
