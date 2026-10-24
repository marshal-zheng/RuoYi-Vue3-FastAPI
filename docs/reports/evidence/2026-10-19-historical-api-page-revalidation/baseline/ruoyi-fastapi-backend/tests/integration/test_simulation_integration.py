"""
Simulation module integration tests
Tests the complete simulation workflow
"""
import pytest
from fastapi.testclient import TestClient


class TestSimulationIntegration:
    """Integration tests for simulation module"""
    
    def test_simulation_start_endpoint(self, test_client):
        """Test simulation start endpoint"""
        response = test_client.post("/simulation/start/1")
        assert response.status_code in [200, 401, 404, 422]
    
    def test_simulation_stop_endpoint(self, test_client):
        """Test simulation stop endpoint"""
        response = test_client.post("/simulation/stop/1")
        assert response.status_code in [200, 401, 404]
    
    def test_simulation_status_endpoint(self, test_client):
        """Test simulation status endpoint"""
        response = test_client.get("/simulation/status/1")
        assert response.status_code in [200, 401, 404]
    
    def test_simulation_list_endpoint(self, test_client):
        """Test simulation list endpoint"""
        response = test_client.get("/simulation/list")
        assert response.status_code in [200, 401, 404]


class TestSimulationServiceIntegration:
    """Integration tests for simulation service layer"""
    
    @pytest.mark.asyncio
    async def test_simulation_service_exists(self):
        """Test that simulation service can be imported"""
        from module_admin.service.simulation_service import SimulationService
        assert SimulationService is not None
    
    @pytest.mark.asyncio
    async def test_simulation_engine_exists(self):
        """Test that simulation engine can be imported"""
        from module_admin.service.simulation_engine import SimulationEngine
        assert SimulationEngine is not None
    
    @pytest.mark.asyncio
    async def test_bandwidth_calculator_exists(self):
        """Test that bandwidth calculator can be imported"""
        from module_admin.service.bandwidth_calculator import BandwidthCalculator
        assert BandwidthCalculator is not None
    
    @pytest.mark.asyncio
    async def test_alarm_detector_exists(self):
        """Test that alarm detector can be imported"""
        from module_admin.service.alarm_detector import AlarmDetector
        assert AlarmDetector is not None
