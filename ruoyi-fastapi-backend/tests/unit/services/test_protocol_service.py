"""
Unit tests for protocol service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st

from module_admin.service.protocol_service import ProtocolService
from module_admin.entity.do.protocol_do import Protocol
from module_admin.entity.vo.protocol_vo import ProtocolQueryModel, AddProtocolModel


@pytest.fixture
def mock_protocol_dao():
    """Create mock protocol DAO."""
    dao = MagicMock()
    dao.get_protocol_by_id = AsyncMock()
    dao.get_protocol_list = AsyncMock()
    dao.add_protocol = AsyncMock()
    dao.edit_protocol = AsyncMock()
    dao.delete_protocol = AsyncMock()
    return dao


@pytest.fixture
def protocol_service(mock_protocol_dao):
    """Create protocol service with mocked dependencies."""
    service = ProtocolService()
    service.protocol_dao = mock_protocol_dao
    return service


@pytest.fixture
def sample_1553b_protocol():
    """Create sample 1553B protocol."""
    return Protocol(
        protocol_id=1,
        protocol_name='Flight Control Bus',
        protocol_type='1553B',
        bus_speed=1000000,
        word_length=20,
        rt_address=1,
        sub_address=1,
        word_count=32,
        status='0',
        create_time=datetime.now(),
    )


@pytest.fixture
def sample_can_protocol():
    """Create sample CAN protocol."""
    return Protocol(
        protocol_id=2,
        protocol_name='Engine Control',
        protocol_type='CAN',
        baud_rate=500000,
        can_id=0x123,
        data_length=8,
        status='0',
        create_time=datetime.now(),
    )


class TestProtocolServiceQuery:
    """Test suite for protocol query operations."""

    @pytest.mark.asyncio
    async def test_get_protocol_by_id_success(self, protocol_service, mock_protocol_dao, sample_1553b_protocol):
        """Test getting protocol by ID."""
        mock_protocol_dao.get_protocol_by_id.return_value = sample_1553b_protocol

        result = await protocol_service.get_protocol_by_id(1)

        assert result is not None
        assert result.protocol_type == '1553B'
        assert result.bus_speed == 1000000

    @pytest.mark.asyncio
    async def test_get_protocol_list_by_type(self, protocol_service, mock_protocol_dao, sample_1553b_protocol):
        """Test filtering protocols by type."""
        mock_protocol_dao.get_protocol_list.return_value = [sample_1553b_protocol]

        query = ProtocolQueryModel(protocol_type='1553B')
        result = await protocol_service.get_protocol_list(query)

        assert len(result['rows']) == 1
        assert result['rows'][0].protocol_type == '1553B'


class TestProtocolServiceValidation:
    """Test suite for protocol validation."""

    @pytest.mark.asyncio
    async def test_validate_1553b_protocol(self, protocol_service):
        """Test 1553B protocol validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test Bus',
            protocol_type='1553B',
            bus_speed=1000000,
            word_length=20,
            rt_address=1,
            sub_address=1,
            word_count=32,
        )

        # Should not raise exception
        await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_1553b_invalid_rt_address(self, protocol_service):
        """Test 1553B RT address validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test Bus',
            protocol_type='1553B',
            rt_address=32,  # Invalid: must be 0-31
        )

        with pytest.raises(ValueError, match='RT地址必须在0-31之间'):
            await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_1553b_invalid_word_count(self, protocol_service):
        """Test 1553B word count validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test Bus',
            protocol_type='1553B',
            word_count=33,  # Invalid: must be 1-32
        )

        with pytest.raises(ValueError, match='字数必须在1-32之间'):
            await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_can_protocol(self, protocol_service):
        """Test CAN protocol validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test CAN',
            protocol_type='CAN',
            baud_rate=500000,
            can_id=0x123,
            data_length=8,
        )

        await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_can_invalid_baud_rate(self, protocol_service):
        """Test CAN baud rate validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test CAN',
            protocol_type='CAN',
            baud_rate=999,  # Invalid baud rate
        )

        with pytest.raises(ValueError, match='波特率无效'):
            await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_can_invalid_id(self, protocol_service):
        """Test CAN ID validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test CAN',
            protocol_type='CAN',
            can_id=0x800,  # Invalid: exceeds 11-bit standard ID
        )

        with pytest.raises(ValueError, match='CAN ID超出范围'):
            await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_rs422_protocol(self, protocol_service):
        """Test RS422 protocol validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test RS422',
            protocol_type='RS422',
            baud_rate=115200,
            data_bits=8,
            stop_bits=1,
            parity='N',
        )

        await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_ethernet_protocol(self, protocol_service):
        """Test Ethernet protocol validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test Ethernet',
            protocol_type='Ethernet',
            ip_address='192.168.1.100',
            port=8080,
            protocol='TCP',
        )

        await protocol_service._validate_protocol(protocol_data)

    @pytest.mark.asyncio
    async def test_validate_ethernet_invalid_ip(self, protocol_service):
        """Test Ethernet IP validation."""
        protocol_data = AddProtocolModel(
            protocol_name='Test Ethernet',
            protocol_type='Ethernet',
            ip_address='999.999.999.999',
        )

        with pytest.raises(ValueError, match='IP地址格式不正确'):
            await protocol_service._validate_protocol(protocol_data)


class TestProtocolServiceCreate:
    """Test suite for protocol creation."""

    @pytest.mark.asyncio
    async def test_add_1553b_protocol(self, protocol_service, mock_protocol_dao):
        """Test adding 1553B protocol."""
        mock_protocol_dao.add_protocol.return_value = 1

        protocol_data = AddProtocolModel(
            protocol_name='New Bus',
            protocol_type='1553B',
            bus_speed=1000000,
            word_length=20,
            rt_address=5,
            sub_address=10,
            word_count=16,
        )

        result = await protocol_service.add_protocol(protocol_data)

        assert result == 1
        mock_protocol_dao.add_protocol.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_can_protocol(self, protocol_service, mock_protocol_dao):
        """Test adding CAN protocol."""
        mock_protocol_dao.add_protocol.return_value = 1

        protocol_data = AddProtocolModel(
            protocol_name='New CAN',
            protocol_type='CAN',
            baud_rate=250000,
            can_id=0x456,
            data_length=8,
        )

        result = await protocol_service.add_protocol(protocol_data)

        assert result == 1


class TestProtocolServiceParsing:
    """Test suite for protocol parsing."""

    def test_parse_1553b_message(self, protocol_service):
        """Test parsing 1553B message."""
        message_data = {
            'command_word': 0x1234,
            'data_words': [0x0001, 0x0002, 0x0003],
            'status_word': 0x5678,
        }

        result = protocol_service.parse_1553b_message(message_data)

        assert result['rt_address'] == (0x1234 >> 11) & 0x1F
        assert result['tr_bit'] == (0x1234 >> 10) & 0x01
        assert len(result['data_words']) == 3

    def test_parse_can_frame(self, protocol_service):
        """Test parsing CAN frame."""
        frame_data = {
            'can_id': 0x123,
            'data': [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
            'dlc': 8,
        }

        result = protocol_service.parse_can_frame(frame_data)

        assert result['can_id'] == 0x123
        assert result['dlc'] == 8
        assert len(result['data']) == 8

    def test_parse_ethernet_packet(self, protocol_service):
        """Test parsing Ethernet packet."""
        packet_data = {
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.200',
            'src_port': 8080,
            'dst_port': 9090,
            'protocol': 'TCP',
            'payload': b'Hello World',
        }

        result = protocol_service.parse_ethernet_packet(packet_data)

        assert result['src_ip'] == '192.168.1.100'
        assert result['dst_ip'] == '192.168.1.200'
        assert result['payload_length'] == 11


class TestProtocolServicePropertyBased:
    """Property-based tests for protocol service."""

    @given(st.integers(min_value=0, max_value=31))
    def test_1553b_rt_address_range(self, rt_address: int):
        """Property test: RT address must be 0-31."""
        service = ProtocolService()
        assert service._validate_rt_address(rt_address) is True

    @given(st.integers(min_value=1, max_value=32))
    def test_1553b_word_count_range(self, word_count: int):
        """Property test: word count must be 1-32."""
        service = ProtocolService()
        assert service._validate_word_count(word_count) is True

    @given(st.integers(min_value=0, max_value=0x7FF))
    def test_can_standard_id_range(self, can_id: int):
        """Property test: standard CAN ID must be 0-0x7FF."""
        service = ProtocolService()
        assert service._validate_can_id(can_id, extended=False) is True

    @given(st.integers(min_value=0, max_value=0x1FFFFFFF))
    def test_can_extended_id_range(self, can_id: int):
        """Property test: extended CAN ID must be 0-0x1FFFFFFF."""
        service = ProtocolService()
        assert service._validate_can_id(can_id, extended=True) is True


class TestProtocolServiceExport:
    """Test suite for protocol export/import."""

    @pytest.mark.asyncio
    async def test_export_protocol(self, protocol_service, mock_protocol_dao, sample_1553b_protocol):
        """Test exporting protocol configuration."""
        mock_protocol_dao.get_protocol_by_id.return_value = sample_1553b_protocol

        result = await protocol_service.export_protocol(1)

        assert result['protocol_type'] == '1553B'
        assert result['bus_speed'] == 1000000
        assert 'rt_address' in result

    @pytest.mark.asyncio
    async def test_import_protocol(self, protocol_service, mock_protocol_dao):
        """Test importing protocol configuration."""
        mock_protocol_dao.add_protocol.return_value = 1

        protocol_data = {
            'protocol_name': 'Imported Bus',
            'protocol_type': '1553B',
            'bus_speed': 1000000,
            'rt_address': 1,
        }

        result = await protocol_service.import_protocol(protocol_data)

        assert result == 1
        mock_protocol_dao.add_protocol.assert_called_once()
