"""
Service layer import and basic functionality tests
Focus on ensuring all services can be imported and instantiated
"""
import pytest

SKIPPED_SCOPE_REASON = 'simulation/protocol/device 当前阶段暂不纳入验收范围'


class TestServiceImports:
    """Test that all service modules can be imported"""
    
    def test_project_service_import(self):
        """Test ProjectService import"""
        from modules.project.application.services.project_service import ProjectService
        assert ProjectService is not None
        assert hasattr(ProjectService, '__init__')
    
    @pytest.mark.skip(reason=SKIPPED_SCOPE_REASON)
    def test_protocol_service_import(self):
        """Test ProtocolService import"""
        from module_admin.service.protocol_service import ProtocolService
        assert ProtocolService is not None
        assert hasattr(ProtocolService, '__init__')
    
    @pytest.mark.skip(reason=SKIPPED_SCOPE_REASON)
    def test_simulation_service_import(self):
        """Test SimulationService import"""
        from module_admin.service.simulation_service import SimulationService
        assert SimulationService is not None
        assert hasattr(SimulationService, '__init__')
    
    def test_user_service_import(self):
        """Test UserService import"""
        from modules.system.application.services.user_service import UserService
        assert UserService is not None
        assert hasattr(UserService, '__init__')
    
    def test_role_service_import(self):
        """Test RoleService import"""
        from modules.system.application.services.role_service import RoleService
        assert RoleService is not None
        assert hasattr(RoleService, '__init__')
    
    def test_menu_service_import(self):
        """Test MenuService import"""
        from modules.system.application.services.menu_service import MenuService
        assert MenuService is not None
        assert hasattr(MenuService, '__init__')
    
    def test_dept_service_import(self):
        """Test DeptService import"""
        from modules.system.application.services.dept_service import DeptService
        assert DeptService is not None
        assert hasattr(DeptService, '__init__')
    
    def test_config_service_import(self):
        """Test ConfigService import"""
        from modules.system.application.services.config_service import ConfigService
        assert ConfigService is not None
        assert hasattr(ConfigService, '__init__')
    
    def test_notice_service_import(self):
        """Test NoticeService import"""
        from modules.system.application.services.notice_service import NoticeService
        assert NoticeService is not None
        assert hasattr(NoticeService, '__init__')
    
    def test_post_service_import(self):
        """Test PostService import"""
        from modules.system.application.services.post_service import PostService
        assert PostService is not None
        assert hasattr(PostService, '__init__')
    
    def test_job_service_import(self):
        """Test JobService import"""
        from modules.scheduler.application.job_service import JobService
        assert JobService is not None
        assert hasattr(JobService, '__init__')
    
    def test_login_service_import(self):
        """Test LoginService import"""
        from modules.identity.application.services.login_service import LoginService
        assert LoginService is not None
        assert hasattr(LoginService, '__init__')


@pytest.mark.skip(reason=SKIPPED_SCOPE_REASON)
class TestSimulationModules:
    """Test simulation-related modules"""
    
    def test_simulation_engine_import(self):
        """Test SimulationEngine import"""
        from module_admin.service.simulation_engine import SimulationEngine
        assert SimulationEngine is not None
    
    def test_bandwidth_calculator_import(self):
        """Test BandwidthCalculator import"""
        from module_admin.service.bandwidth_calculator import BandwidthCalculator
        assert BandwidthCalculator is not None
    
    def test_alarm_detector_import(self):
        """Test AlarmDetector import"""
        from module_admin.service.alarm_detector import AlarmDetector
        assert AlarmDetector is not None
    
    def test_simulation_runner_import(self):
        """Test SimulationRunner import"""
        from module_admin.service.simulation_runner import SimulationRunner
        assert SimulationRunner is not None


@pytest.mark.skip(reason=SKIPPED_SCOPE_REASON)
class TestProtocolModules:
    """Test protocol-related modules"""
    
    def test_protocol_io_adapter_import(self):
        """Test ProtocolIOAdapter import"""
        from module_admin.service.protocol_io_adapter import ProtocolIOAdapter
        assert ProtocolIOAdapter is not None
    
    def test_protocol_parser_import(self):
        """Test ProtocolParser import"""
        from module_admin.service.protocol_parser import ProtocolParser
        assert ProtocolParser is not None
    
    def test_base_protocol_import(self):
        """Test BaseProtocol import"""
        from module_admin.service.protocol_models.base_protocol import BaseProtocol
        assert BaseProtocol is not None
    
    def test_can_model_import(self):
        """Test CANModel import"""
        from module_admin.service.protocol_models.can_model import CANProtocol
        assert CANProtocol is not None
    
    def test_lan_model_import(self):
        """Test LANModel import"""
        from module_admin.service.protocol_models.lan_model import LANProtocol
        assert LANProtocol is not None
    
    def test_mil1553b_model_import(self):
        """Test MIL1553BModel import"""
        from module_admin.service.protocol_models.mil1553b_model import MIL1553BProtocol
        assert MIL1553BProtocol is not None
    
    def test_rs485_model_import(self):
        """Test RS485Model import"""
        from module_admin.service.protocol_models.rs485_model import RS485Protocol
        assert RS485Protocol is not None
