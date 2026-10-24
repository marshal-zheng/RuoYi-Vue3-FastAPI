"""
Core modules integration tests
Tests that all core modules can be imported and basic functionality works
"""
import pytest


class TestUtilsIntegration:
    """Integration tests for utility modules"""
    
    def test_pwd_util_import(self):
        """Test that PwdUtil can be imported"""
        from utils.pwd_util import PwdUtil
        assert PwdUtil is not None
    
    def test_pwd_util_password_hashing(self):
        """Test password hashing functionality"""
        from utils.pwd_util import PwdUtil
        
        password = "test123"
        hashed = PwdUtil.get_password_hash(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_pwd_util_password_verification(self):
        """Test password verification functionality"""
        from utils.pwd_util import PwdUtil
        
        password = "test123"
        hashed = PwdUtil.get_password_hash(password)
        
        # Correct password should verify
        assert PwdUtil.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert PwdUtil.verify_password("wrong", hashed) is False
    
    def test_common_util_import(self):
        """Test that common utils can be imported"""
        from utils.common_util import CamelCaseUtil, SnakeCaseUtil
        assert CamelCaseUtil is not None
        assert SnakeCaseUtil is not None
    
    def test_camel_case_conversion(self):
        """Test camel case conversion"""
        from utils.common_util import CamelCaseUtil
        
        result = CamelCaseUtil.snake_to_camel("test_value")
        assert result == "testValue"
    
    def test_snake_case_conversion(self):
        """Test snake case conversion"""
        from utils.common_util import SnakeCaseUtil
        
        result = SnakeCaseUtil.camel_to_snake("testValue")
        assert result == "test_value"
    
    def test_time_format_util_import(self):
        """Test that TimeFormatUtil can be imported"""
        from utils.time_format_util import TimeFormatUtil
        assert TimeFormatUtil is not None


class TestServiceLayerIntegration:
    """Integration tests for service layer modules"""
    
    @pytest.mark.asyncio
    async def test_project_service_import(self):
        """Test that ProjectService can be imported"""
        from modules.project.application.services.project_service import ProjectService
        assert ProjectService is not None
    
    @pytest.mark.asyncio
    async def test_protocol_service_import(self):
        """Test that ProtocolService can be imported"""
        from module_admin.service.protocol_service import ProtocolService
        assert ProtocolService is not None
    
    @pytest.mark.asyncio
    async def test_simulation_service_import(self):
        """Test that SimulationService can be imported"""
        from module_admin.service.simulation_service import SimulationService
        assert SimulationService is not None
    
    @pytest.mark.asyncio
    async def test_role_service_import(self):
        """Test that RoleService can be imported"""
        from modules.system.application.services.role_service import RoleService
        assert RoleService is not None
    
    @pytest.mark.asyncio
    async def test_dept_service_import(self):
        """Test that DeptService can be imported"""
        from modules.system.application.services.dept_service import DeptService
        assert DeptService is not None
    
    @pytest.mark.asyncio
    async def test_dict_service_import(self):
        """Test that dict services can be imported"""
        from modules.system.application.services import DictTypeService, DictDataService
        assert DictTypeService is not None
        assert DictDataService is not None
    
    @pytest.mark.asyncio
    async def test_config_service_import(self):
        """Test that ConfigService can be imported"""
        from modules.system.application.services.config_service import ConfigService
        assert ConfigService is not None


class TestControllerLayerIntegration:
    """Integration tests for controller layer modules"""
    
    def test_project_controller_import(self):
        """Test that project controller can be imported"""
        from modules.project.api.project_controller import projectController
        assert projectController is not None
    
    def test_protocol_controller_import(self):
        """Test that protocol controller can be imported"""
        from module_admin.controller.protocol_controller import protocolController
        assert protocolController is not None
    
    def test_simulation_controller_import(self):
        """Test that simulation controller can be imported"""
        from module_admin.controller.simulation_controller import simulationController
        assert simulationController is not None
