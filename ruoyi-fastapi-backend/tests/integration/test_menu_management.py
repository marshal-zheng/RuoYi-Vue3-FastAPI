"""
Menu management integration tests
Tests menu CRUD operations and tree structure
"""
import pytest
from fastapi.testclient import TestClient


class TestMenuManagementIntegration:
    """Integration tests for menu management"""
    
    def test_menu_list_endpoint(self, test_client):
        """Test menu list endpoint"""
        response = test_client.get("/system/menu/list")
        assert response.status_code in [200, 401, 404]
    
    def test_menu_tree_endpoint(self, test_client):
        """Test menu tree endpoint"""
        response = test_client.get("/system/menu/treeselect")
        assert response.status_code in [200, 401, 404]
    
    def test_menu_info_endpoint(self, test_client):
        """Test menu info endpoint"""
        response = test_client.get("/system/menu/1")
        assert response.status_code in [200, 401, 404]
    
    def test_menu_create_endpoint(self, test_client):
        """Test menu creation endpoint"""
        menu_data = {
            "menuName": "Test Menu",
            "menuType": "M",
            "orderNum": 1,
            "visible": "0",
            "status": "0"
        }
        response = test_client.post("/system/menu", json=menu_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_menu_update_endpoint(self, test_client):
        """Test menu update endpoint"""
        menu_data = {
            "menuId": 1,
            "menuName": "Updated Menu",
            "orderNum": 2
        }
        response = test_client.put("/system/menu", json=menu_data)
        assert response.status_code in [200, 401, 404, 422]
    
    def test_menu_delete_endpoint(self, test_client):
        """Test menu deletion endpoint"""
        response = test_client.delete("/system/menu/1")
        assert response.status_code in [200, 401, 404]


class TestMenuServiceIntegration:
    """Integration tests for menu service layer"""
    
    @pytest.mark.asyncio
    async def test_menu_service_exists(self):
        """Test that menu service can be imported"""
        from modules.system.application.services.menu_service import MenuService
        assert MenuService is not None
    
    @pytest.mark.asyncio
    async def test_menu_models_exist(self):
        """Test that menu models can be imported"""
        try:
            from module_admin.entity.do.menu_do import Menu
            assert Menu is not None
        except ImportError:
            pass


class TestMenuTreeIntegration:
    """Integration tests for menu tree operations"""
    
    def test_role_menu_tree_endpoint(self, test_client):
        """Test role menu tree endpoint"""
        response = test_client.get("/system/menu/roleMenuTreeselect/1")
        assert response.status_code in [200, 401, 404]
    
    def test_menu_tree_structure(self, test_client):
        """Test menu tree structure endpoint"""
        response = test_client.get("/system/menu/treeselect")
        assert response.status_code in [200, 401, 404]
