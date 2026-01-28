"""
Unit tests for simulation service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st

from module_admin.service.simulation_service import SimulationService
from module_admin.entity.do.project_do import Project


@pytest.fixture
def mock_simulation_dao():
    """Create mock simulation DAO."""
    dao = MagicMock()
    dao.get_simulation_by_id = AsyncMock()
    dao.create_simulation = AsyncMock()
    dao.update_simulation_status = AsyncMock()
    return dao


@pytest.fixture
def mock_simulation_engine():
    """Create mock simulation engine."""
    engine = MagicMock()
    engine.start = AsyncMock()
    engine.pause = AsyncMock()
    engine.resume = AsyncMock()
    engine.stop = AsyncMock()
    engine.get_status = AsyncMock()
    return engine


@pytest.fixture
def simulation_service(mock_simulation_dao, mock_simulation_engine):
    """Create simulation service with mocked dependencies."""
    service = SimulationService()
    service.simulation_dao = mock_simulation_dao
    service.simulation_engine = mock_simulation_engine
    return service


@pytest.fixture
def sample_project():
    """Create sample project for simulation."""
    return Project(
        project_id=1,
        project_name='Test Project',
        project_code='TEST001',
        status='0',
    )


class TestSimulationServiceStart:
    """Test suite for simulation start operations."""

    @pytest.mark.asyncio
    async def test_start_simulation_success(self, simulation_service, mock_simulation_engine):
        """Test starting simulation successfully."""
        mock_simulation_engine.start.return_value = {'status': 'running', 'simulation_id': 1}

        result = await simulation_service.start_simulation(1)

        assert result['status'] == 'running'
        assert result['simulation_id'] == 1
        mock_simulation_engine.start.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_start_simulation_with_config(self, simulation_service, mock_simulation_engine):
        """Test starting simulation with custom configuration."""
        config = {
            'speed': 2.0,
            'duration': 3600,
            'protocols': ['1553B', 'CAN']
        }

        mock_simulation_engine.start.return_value = {'status': 'running'}

        result = await simulation_service.start_simulation(1, config)

        assert result['status'] == 'running'
        mock_simulation_engine.start.assert_called_once_with(1, config)

    @pytest.mark.asyncio
    async def test_start_simulation_already_running(self, simulation_service, mock_simulation_engine):
        """Test starting already running simulation."""
        mock_simulation_engine.get_status.return_value = {'status': 'running'}

        with pytest.raises(ValueError, match='仿真已在运行中'):
            await simulation_service.start_simulation(1)

    @pytest.mark.asyncio
    async def test_start_simulation_invalid_project(self, simulation_service):
        """Test starting simulation with invalid project."""
        with pytest.raises(ValueError, match='项目不存在'):
            await simulation_service.start_simulation(999)


class TestSimulationServiceControl:
    """Test suite for simulation control operations."""

    @pytest.mark.asyncio
    async def test_pause_simulation(self, simulation_service, mock_simulation_engine):
        """Test pausing running simulation."""
        mock_simulation_engine.get_status.return_value = {'status': 'running'}
        mock_simulation_engine.pause.return_value = {'status': 'paused'}

        result = await simulation_service.pause_simulation(1)

        assert result['status'] == 'paused'
        mock_simulation_engine.pause.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_pause_not_running_simulation(self, simulation_service, mock_simulation_engine):
        """Test pausing non-running simulation."""
        mock_simulation_engine.get_status.return_value = {'status': 'stopped'}

        with pytest.raises(ValueError, match='仿真未运行'):
            await simulation_service.pause_simulation(1)

    @pytest.mark.asyncio
    async def test_resume_simulation(self, simulation_service, mock_simulation_engine):
        """Test resuming paused simulation."""
        mock_simulation_engine.get_status.return_value = {'status': 'paused'}
        mock_simulation_engine.resume.return_value = {'status': 'running'}

        result = await simulation_service.resume_simulation(1)

        assert result['status'] == 'running'
        mock_simulation_engine.resume.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_stop_simulation(self, simulation_service, mock_simulation_engine):
        """Test stopping simulation."""
        mock_simulation_engine.stop.return_value = {'status': 'stopped', 'duration': 100}

        result = await simulation_service.stop_simulation(1)

        assert result['status'] == 'stopped'
        assert result['duration'] == 100
        mock_simulation_engine.stop.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_set_simulation_speed(self, simulation_service, mock_simulation_engine):
        """Test setting simulation speed."""
        mock_simulation_engine.set_speed = AsyncMock(return_value={'speed': 2.0})

        result = await simulation_service.set_speed(1, 2.0)

        assert result['speed'] == 2.0

    @pytest.mark.asyncio
    async def test_set_invalid_speed(self, simulation_service):
        """Test setting invalid simulation speed."""
        with pytest.raises(ValueError, match='速度必须在0.1-10之间'):
            await simulation_service.set_speed(1, 0)

        with pytest.raises(ValueError, match='速度必须在0.1-10之间'):
            await simulation_service.set_speed(1, 100)


class TestSimulationServiceStatus:
    """Test suite for simulation status operations."""

    @pytest.mark.asyncio
    async def test_get_simulation_status(self, simulation_service, mock_simulation_engine):
        """Test getting simulation status."""
        mock_status = {
            'status': 'running',
            'current_time': 100.5,
            'speed': 1.0,
            'messages_sent': 1000
        }
        mock_simulation_engine.get_status.return_value = mock_status

        result = await simulation_service.get_status(1)

        assert result['status'] == 'running'
        assert result['current_time'] == 100.5
        assert result['messages_sent'] == 1000

    @pytest.mark.asyncio
    async def test_get_simulation_statistics(self, simulation_service, mock_simulation_engine):
        """Test getting simulation statistics."""
        mock_stats = {
            'total_messages': 10000,
            'messages_by_protocol': {
                '1553B': 6000,
                'CAN': 4000
            },
            'bandwidth_usage': {
                'peak': 950000,
                'average': 500000
            },
            'errors': 5
        }
        mock_simulation_engine.get_statistics = AsyncMock(return_value=mock_stats)

        result = await simulation_service.get_statistics(1)

        assert result['total_messages'] == 10000
        assert result['messages_by_protocol']['1553B'] == 6000
        assert result['bandwidth_usage']['peak'] == 950000


class TestSimulationServiceEvents:
    """Test suite for simulation event handling."""

    @pytest.mark.asyncio
    async def test_trigger_event(self, simulation_service, mock_simulation_engine):
        """Test triggering simulation event."""
        event_data = {
            'event_type': 'fault_injection',
            'target_device': 'device_1',
            'fault_type': 'communication_loss'
        }

        mock_simulation_engine.trigger_event = AsyncMock(return_value={'success': True})

        result = await simulation_service.trigger_event(1, event_data)

        assert result['success'] is True
        mock_simulation_engine.trigger_event.assert_called_once_with(1, event_data)

    @pytest.mark.asyncio
    async def test_get_event_history(self, simulation_service, mock_simulation_engine):
        """Test getting event history."""
        mock_events = [
            {'timestamp': 10.0, 'event_type': 'start'},
            {'timestamp': 50.0, 'event_type': 'fault_injection'},
            {'timestamp': 100.0, 'event_type': 'stop'}
        ]
        mock_simulation_engine.get_event_history = AsyncMock(return_value=mock_events)

        result = await simulation_service.get_event_history(1)

        assert len(result) == 3
        assert result[1]['event_type'] == 'fault_injection'


class TestSimulationServiceValidation:
    """Test suite for simulation validation."""

    def test_validate_simulation_config(self, simulation_service):
        """Test simulation configuration validation."""
        valid_config = {
            'speed': 1.0,
            'duration': 3600,
            'protocols': ['1553B', 'CAN']
        }

        # Should not raise exception
        simulation_service._validate_config(valid_config)

    def test_validate_invalid_speed(self, simulation_service):
        """Test validation of invalid speed."""
        invalid_config = {'speed': -1}

        with pytest.raises(ValueError, match='速度必须为正数'):
            simulation_service._validate_config(invalid_config)

    def test_validate_invalid_duration(self, simulation_service):
        """Test validation of invalid duration."""
        invalid_config = {'duration': -100}

        with pytest.raises(ValueError, match='持续时间必须为正数'):
            simulation_service._validate_config(invalid_config)

    def test_validate_invalid_protocols(self, simulation_service):
        """Test validation of invalid protocols."""
        invalid_config = {'protocols': ['INVALID_PROTOCOL']}

        with pytest.raises(ValueError, match='不支持的协议类型'):
            simulation_service._validate_config(invalid_config)

    @given(st.floats(min_value=0.1, max_value=10.0))
    def test_validate_speed_range_property(self, speed: float):
        """Property test: valid speed range."""
        service = SimulationService()
        assert service._validate_speed(speed) is True

    @given(st.integers(min_value=1, max_value=86400))
    def test_validate_duration_range_property(self, duration: int):
        """Property test: valid duration range."""
        service = SimulationService()
        assert service._validate_duration(duration) is True


class TestSimulationServiceBandwidth:
    """Test suite for bandwidth calculation."""

    @pytest.mark.asyncio
    async def test_calculate_bandwidth_usage(self, simulation_service):
        """Test bandwidth usage calculation."""
        messages = [
            {'protocol': '1553B', 'size': 40, 'timestamp': 1.0},
            {'protocol': 'CAN', 'size': 8, 'timestamp': 1.0},
            {'protocol': '1553B', 'size': 40, 'timestamp': 2.0}
        ]

        result = simulation_service.calculate_bandwidth(messages, time_window=1.0)

        assert result['total_bandwidth'] > 0
        assert '1553B' in result['by_protocol']
        assert 'CAN' in result['by_protocol']

    @pytest.mark.asyncio
    async def test_detect_bandwidth_congestion(self, simulation_service):
        """Test bandwidth congestion detection."""
        high_bandwidth_messages = [
            {'protocol': '1553B', 'size': 1000, 'timestamp': t}
            for t in range(100)
        ]

        result = simulation_service.detect_congestion(
            high_bandwidth_messages,
            max_bandwidth=10000
        )

        assert result['is_congested'] is True
        assert result['utilization'] > 90


class TestSimulationServiceAlarms:
    """Test suite for alarm detection."""

    @pytest.mark.asyncio
    async def test_detect_message_loss(self, simulation_service):
        """Test message loss detection."""
        messages = [
            {'id': 1, 'timestamp': 1.0, 'status': 'sent'},
            {'id': 2, 'timestamp': 2.0, 'status': 'lost'},
            {'id': 3, 'timestamp': 3.0, 'status': 'sent'}
        ]

        alarms = simulation_service.detect_alarms(messages)

        assert len(alarms) > 0
        assert any(a['type'] == 'message_loss' for a in alarms)

    @pytest.mark.asyncio
    async def test_detect_timing_violation(self, simulation_service):
        """Test timing violation detection."""
        messages = [
            {'id': 1, 'expected_time': 1.0, 'actual_time': 1.5},
            {'id': 2, 'expected_time': 2.0, 'actual_time': 2.1}
        ]

        alarms = simulation_service.detect_alarms(messages)

        timing_alarms = [a for a in alarms if a['type'] == 'timing_violation']
        assert len(timing_alarms) > 0


class TestSimulationServiceExport:
    """Test suite for simulation data export."""

    @pytest.mark.asyncio
    async def test_export_simulation_results(self, simulation_service, mock_simulation_engine):
        """Test exporting simulation results."""
        mock_results = {
            'simulation_id': 1,
            'duration': 100.0,
            'messages': [],
            'statistics': {},
            'events': []
        }
        mock_simulation_engine.get_results = AsyncMock(return_value=mock_results)

        result = await simulation_service.export_results(1, format='json')

        assert result['simulation_id'] == 1
        assert result['duration'] == 100.0

    @pytest.mark.asyncio
    async def test_export_to_csv(self, simulation_service):
        """Test exporting results to CSV format."""
        result = await simulation_service.export_results(1, format='csv')

        assert isinstance(result, str)
        assert 'timestamp' in result
        assert 'protocol' in result

    @pytest.mark.asyncio
    async def test_export_invalid_format(self, simulation_service):
        """Test exporting with invalid format."""
        with pytest.raises(ValueError, match='不支持的导出格式'):
            await simulation_service.export_results(1, format='invalid')
