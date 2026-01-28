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
        from module_admin.service.project_service import ProjectService
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
        from module_admin.service.role_service import RoleService
        assert RoleService is not None
    
    @pytest.mark.asyncio
    async def test_dept_service_import(self):
        """Test that DeptService can be imported"""
        from module_admin.service.dept_service import DeptService
        assert DeptService is not None
    
    @pytest.mark.asyncio
    async def test_dict_service_import(self):
        """Test that DictService can be imported"""
        from module_admin.service.dict_service import DictService
        assert DictService is not None
    
    @pytest.mark.asyncio
    async def test_config_service_import(self):
        """Test that ConfigService can be imported"""
        from module_admin.service.config_service import ConfigService
        assert ConfigService is not None


class TestDAOLayerIntegration:
    """Integration tests for DAO layer modules"""
    
    @pytest.mark.asyncio
    async def test_project_dao_import(self):
        """Test that ProjectDao can be imported"""
        from module_admin.dao.project_dao import ProjectDao
        assert ProjectDao is not None
    
    @pytest.mark.asyncio
    async def test_protocol_dao_import(self):
        """Test that ProtocolDao can be imported"""
        from module_admin.dao.protocol_dao import ProtocolDao
        assert ProtocolDao is not None
    
    @pytest.mark.asyncio
    async def test_simulation_dao_import(self):
        """Test that SimulationDao can be imported"""
        from module_admin.dao.simulation_dao import SimulationDao
        assert SimulationDao is not None
    
    @pytest.mark.asyncio
    async def test_role_dao_import(self):
        """Test that RoleDao can be imported"""
        from module_admin.dao.role_dao import RoleDao
        assert RoleDao is not None
    
    @pytest.mark.asyncio
    async def test_dept_dao_import(self):
        """Test that DeptDao can be imported"""
        from module_admin.dao.dept_dao import DeptDao
        assert DeptDao is not None


class TestControllerLayerIntegration:
    """Integration tests for controller layer modules"""
    
    def test_project_controller_import(self):
        """Test that project controller can be imported"""
        from module_admin.controller.project_controller import projectController
        assert projectController is not None
    
    def test_protocol_controller_import(self):
        """Test that protocol controller can be imported"""
        from module_admin.controller.protocol_controller import protocolController
        assert protocolController is not None
    
    def test_simulation_controller_import(self):
        """Test that simulation controller can be imported"""
        from module_admin.controller.simulation_controller import simulationController
        assert simulationController is not None
