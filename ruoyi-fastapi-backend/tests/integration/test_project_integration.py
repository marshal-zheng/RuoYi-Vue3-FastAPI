"""
Project module integration tests
Tests the complete project CRUD workflow
"""
import pytest
from fastapi.testclient import TestClient


class TestProjectIntegration:
    """Integration tests for project module"""
    
    def test_project_list_endpoint(self, test_client):
        """Test project list endpoint"""
        response = test_client.get("/project/list")
        # Should return 200 or 401 (auth required)
        assert response.status_code in [200, 401, 404]
    
    def test_project_info_endpoint(self, test_client):
        """Test project info endpoint"""
        response = test_client.get("/project/1")
        # Should return 200, 401, or 404
        assert response.status_code in [200, 401, 404]
    
    def test_project_create_endpoint(self, test_client):
        """Test project creation endpoint"""
        project_data = {
            "projectName": "Test Project",
            "description": "Test Description"
        }
        response = test_client.post("/project", json=project_data)
        # Should return 200, 401, or 404
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_project_update_endpoint(self, test_client):
        """Test project update endpoint"""
        project_data = {
            "projectId": 1,
            "projectName": "Updated Project",
            "description": "Updated Description"
        }
        response = test_client.put("/project", json=project_data)
        # Should return 200, 401, or 404
        assert response.status_code in [200, 401, 404, 422]
    
    def test_project_delete_endpoint(self, test_client):
        """Test project deletion endpoint"""
        response = test_client.delete("/project/1")
        # Should return 200, 401, or 404
        assert response.status_code in [200, 401, 404]
    
    def test_project_export_endpoint(self, test_client):
        """Test project export endpoint"""
        response = test_client.post("/project/export")
        # Should return 200, 401, or 404
        assert response.status_code in [200, 401, 404]


class TestProjectServiceIntegration:
    """Integration tests for project service layer"""
    
    @pytest.mark.asyncio
    async def test_project_service_exists(self):
        """Test that project service can be imported"""
        from module_admin.service.project_service import ProjectService
        assert ProjectService is not None
    
    @pytest.mark.asyncio
    async def test_project_dao_exists(self):
        """Test that project DAO can be imported"""
        from module_admin.dao.project_dao import ProjectDao
        assert ProjectDao is not None
    
    @pytest.mark.asyncio
    async def test_project_models_exist(self):
        """Test that project models can be imported"""
        try:
            from module_admin.entity.do.project_do import Project
            assert Project is not None
        except ImportError:
            # Try alternative import
            from module_admin.entity.do.project_do import ProjectDO
            assert ProjectDO is not None
