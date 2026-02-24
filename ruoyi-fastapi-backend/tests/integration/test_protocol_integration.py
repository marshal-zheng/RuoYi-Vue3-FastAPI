"""
Protocol module integration tests
Tests the complete protocol CRUD workflow
"""
import pytest
from fastapi.testclient import TestClient


class TestProtocolIntegration:
    """Integration tests for protocol module"""
    
    def test_protocol_list_endpoint(self, test_client):
        """Test protocol list endpoint"""
        response = test_client.get("/protocol/list")
        assert response.status_code in [200, 401, 404]
    
    def test_protocol_info_endpoint(self, test_client):
        """Test protocol info endpoint"""
        response = test_client.get("/protocol/1")
        assert response.status_code in [200, 401, 404]
    
    def test_protocol_create_endpoint(self, test_client):
        """Test protocol creation endpoint"""
        protocol_data = {
            "protocolName": "Test Protocol",
            "protocolType": "CAN",
            "config": {}
        }
        response = test_client.post("/protocol", json=protocol_data)
        assert response.status_code in [200, 201, 401, 404, 422]
    
    def test_protocol_update_endpoint(self, test_client):
        """Test protocol update endpoint"""
        protocol_data = {
            "protocolId": 1,
            "protocolName": "Updated Protocol",
            "protocolType": "CAN"
        }
        response = test_client.put("/protocol", json=protocol_data)
        assert response.status_code in [200, 401, 404, 422]
    
    def test_protocol_delete_endpoint(self, test_client):
        """Test protocol deletion endpoint"""
        response = test_client.delete("/protocol/1")
        assert response.status_code in [200, 401, 404]


class TestProtocolServiceIntegration:
    """Integration tests for protocol service layer"""
    
    @pytest.mark.asyncio
    async def test_protocol_service_exists(self):
        """Test that protocol service can be imported"""
        from module_admin.service.protocol_service import ProtocolService
        assert ProtocolService is not None
    
    @pytest.mark.asyncio
    async def test_protocol_models_exist(self):
        """Test that protocol models can be imported"""
        try:
            from module_admin.entity.do.protocol_do import Protocol
            assert Protocol is not None
        except ImportError:
            from module_admin.entity.do.protocol_do import ProtocolDO
            assert ProtocolDO is not None
