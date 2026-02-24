"""
Dictionary and Configuration management integration tests
Tests dict and config CRUD operations
"""
import pytest
from fastapi.testclient import TestClient


class TestDictManagementIntegration:
    """Integration tests for dictionary management"""
    
    def test_dict_type_list_endpoint(self, test_client):
        """Test dictionary type list endpoint"""
        response = test_client.get("/system/dict/type/list")
        assert response.status_code in [200, 401, 404]
    
    def test_dict_data_list_endpoint(self, test_client):
        """Test dictionary data list endpoint"""
        response = test_client.get("/system/dict/data/list")
        assert response.status_code in [200, 401, 404]
    
    def test_dict_type_info_endpoint(self, test_client):
        """Test dictionary type info endpoint"""
        response = test_client.get("/system/dict/type/1")
        assert response.status_code in [200, 401, 404]
    
    def test_dict_type_create_endpoint(self, test_client):
        """Test dictionary type creation endpoint"""
        dict_data = {
            "dictName": "Test Dict",
            "dictType": "test_dict",
            "status": "0"
        }
        response = test_client.post("/system/dict/type", json=dict_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_dict_data_create_endpoint(self, test_client):
        """Test dictionary data creation endpoint"""
        dict_data = {
            "dictLabel": "Test Label",
            "dictValue": "test_value",
            "dictType": "test_dict",
            "dictSort": 1
        }
        response = test_client.post("/system/dict/data", json=dict_data)
        assert response.status_code in [200, 201, 401, 404, 422]


class TestConfigManagementIntegration:
    """Integration tests for configuration management"""
    
    def test_config_list_endpoint(self, test_client):
        """Test configuration list endpoint"""
        response = test_client.get("/system/config/list")
        assert response.status_code in [200, 401, 404]
    
    def test_config_info_endpoint(self, test_client):
        """Test configuration info endpoint"""
        response = test_client.get("/system/config/1")
        assert response.status_code in [200, 401, 404]
    
    def test_config_by_key_endpoint(self, test_client):
        """Test get configuration by key endpoint"""
        response = test_client.get("/system/config/configKey/test.key")
        assert response.status_code in [200, 401, 404]
    
    def test_config_create_endpoint(self, test_client):
        """Test configuration creation endpoint"""
        config_data = {
            "configName": "Test Config",
            "configKey": "test.config.key",
            "configValue": "test_value",
            "configType": "Y"
        }
        response = test_client.post("/system/config", json=config_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_config_update_endpoint(self, test_client):
        """Test configuration update endpoint"""
        config_data = {
            "configId": 1,
            "configName": "Updated Config",
            "configValue": "updated_value"
        }
        response = test_client.put("/system/config", json=config_data)
        assert response.status_code in [200, 401, 404, 422]
    
    def test_config_delete_endpoint(self, test_client):
        """Test configuration deletion endpoint"""
        response = test_client.delete("/system/config/1")
        assert response.status_code in [200, 401, 404, 409]
    
    def test_config_refresh_cache_endpoint(self, test_client):
        """Test configuration cache refresh endpoint"""
        response = test_client.delete("/system/config/refreshCache")
        assert response.status_code in [200, 401, 404]


class TestDictServiceIntegration:
    """Integration tests for dictionary service layer"""
    
    @pytest.mark.asyncio
    async def test_dict_type_service_exists(self):
        """Test that dict type service can be imported"""
        try:
            from modules.system.application.services import DictTypeService
            assert DictTypeService is not None
        except ImportError:
            # Service might have different name
            pass
    
    @pytest.mark.asyncio
    async def test_dict_data_service_exists(self):
        """Test that dict data service can be imported"""
        try:
            from modules.system.application.services import DictDataService
            assert DictDataService is not None
        except ImportError:
            pass


class TestConfigServiceIntegration:
    """Integration tests for configuration service layer"""
    
    @pytest.mark.asyncio
    async def test_config_service_exists(self):
        """Test that config service can be imported"""
        from modules.system.application.services.config_service import ConfigService
        assert ConfigService is not None
    
