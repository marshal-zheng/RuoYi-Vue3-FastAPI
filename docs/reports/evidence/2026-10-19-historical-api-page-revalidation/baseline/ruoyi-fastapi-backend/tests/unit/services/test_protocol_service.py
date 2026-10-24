"""
Unit tests for ProtocolService current runtime paths.
"""

from unittest.mock import AsyncMock

import pytest

from module_admin.entity.vo.protocol_vo import AddProtocolModel, ProtocolModel
from module_admin.service.protocol_service import ProtocolService


@pytest.fixture
def protocol_service():
    fake_repo = type('FakeProtocolRepo', (), {})()
    return ProtocolService(protocol_repo=fake_repo)


class TestProtocolServiceValidation:
    @pytest.mark.asyncio
    async def test_validate_1553b_protocol_success(self, protocol_service):
        model = AddProtocolModel(protocol_type='1553B', rt_address=1, word_count=16)

        await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_1553b_invalid_rt_address(self, protocol_service):
        model = AddProtocolModel(protocol_type='1553B', rt_address=32)

        with pytest.raises(ValueError, match='RT地址必须在0-31之间'):
            await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_1553b_invalid_word_count(self, protocol_service):
        model = AddProtocolModel(protocol_type='1553B', word_count=33)

        with pytest.raises(ValueError, match='字数必须在1-32之间'):
            await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_can_protocol_success(self, protocol_service):
        model = AddProtocolModel(protocol_type='CAN', baud_rate=500000, can_id=0x123)

        await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_can_invalid_baud_rate(self, protocol_service):
        model = AddProtocolModel(protocol_type='CAN', baud_rate=9600)

        with pytest.raises(ValueError, match='波特率无效'):
            await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_can_invalid_id(self, protocol_service):
        model = AddProtocolModel(protocol_type='CAN', can_id=0x800)

        with pytest.raises(ValueError, match='CAN ID超出范围'):
            await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_ethernet_protocol_success(self, protocol_service):
        model = AddProtocolModel(protocol_type='Ethernet', ip_address='192.168.1.10')

        await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_ethernet_invalid_ip(self, protocol_service):
        model = AddProtocolModel(protocol_type='ETHERNET', ip_address='999.999.1.1')

        with pytest.raises(ValueError, match='IP地址格式不正确'):
            await protocol_service._validate_protocol(model)

    @pytest.mark.asyncio
    async def test_validate_rs422_protocol_is_noop(self, protocol_service):
        model = AddProtocolModel(protocol_type='RS422')

        await protocol_service._validate_protocol(model)


class TestProtocolServiceValidators:
    def test_validate_ip_address(self):
        assert ProtocolService._validate_ip_address('192.168.1.1') is True
        assert ProtocolService._validate_ip_address('2001:db8::1') is True
        assert ProtocolService._validate_ip_address('999.999.999.999') is False

    def test_validate_rt_address_boundary(self):
        assert ProtocolService._validate_rt_address(-1) is False
        assert ProtocolService._validate_rt_address(0) is True
        assert ProtocolService._validate_rt_address(31) is True
        assert ProtocolService._validate_rt_address(32) is False

    def test_validate_word_count_boundary(self):
        assert ProtocolService._validate_word_count(0) is False
        assert ProtocolService._validate_word_count(1) is True
        assert ProtocolService._validate_word_count(32) is True
        assert ProtocolService._validate_word_count(33) is False

    def test_validate_can_id_boundary(self):
        assert ProtocolService._validate_can_id(-1) is False
        assert ProtocolService._validate_can_id(0x7FF, extended=False) is True
        assert ProtocolService._validate_can_id(0x800, extended=False) is False
        assert ProtocolService._validate_can_id(0x1FFFFFFF, extended=True) is True
        assert ProtocolService._validate_can_id(0x20000000, extended=True) is False


class TestProtocolServiceParsing:
    def test_parse_1553b_message(self, protocol_service):
        data = {
            'command_word': 0x1234,
            'data_words': [1, 2, 3],
            'status_word': 0x5678,
        }

        parsed = protocol_service.parse_1553b_message(data)

        assert parsed['rt_address'] == ((0x1234 >> 11) & 0x1F)
        assert parsed['tr_bit'] == ((0x1234 >> 10) & 0x01)
        assert parsed['sub_address'] == ((0x1234 >> 5) & 0x1F)
        assert parsed['word_count'] == (0x1234 & 0x1F)
        assert parsed['data_words'] == [1, 2, 3]
        assert parsed['status_word'] == 0x5678

    def test_parse_can_frame(self, protocol_service):
        data = {'can_id': 0x123, 'dlc': 8, 'data': [1, 2, 3, 4]}

        parsed = protocol_service.parse_can_frame(data)

        assert parsed == {'can_id': 0x123, 'dlc': 8, 'data': [1, 2, 3, 4]}

    def test_parse_ethernet_packet(self, protocol_service):
        data = {
            'src_ip': '10.0.0.1',
            'dst_ip': '10.0.0.2',
            'src_port': 8000,
            'dst_port': 9000,
            'protocol': 'TCP',
            'payload': b'hello',
        }

        parsed = protocol_service.parse_ethernet_packet(data)

        assert parsed['src_ip'] == '10.0.0.1'
        assert parsed['dst_ip'] == '10.0.0.2'
        assert parsed['src_port'] == 8000
        assert parsed['dst_port'] == 9000
        assert parsed['protocol'] == 'TCP'
        assert parsed['payload_length'] == 5

    def test_parse_ethernet_packet_none_payload(self, protocol_service):
        parsed = protocol_service.parse_ethernet_packet({'payload': None})

        assert parsed['payload_length'] == 0


class TestProtocolServiceRepositoryOnly:
    @pytest.mark.asyncio
    async def test_edit_protocol_uses_repository_update(self):
        query_db = AsyncMock()
        query_db.flush = AsyncMock()
        protocol_entity = type('ProtocolEntity', (), {'protocol_id': 1, 'protocol_name': 'old'})()

        fake_repo = type(
            'FakeProtocolRepo',
            (),
            {
                'find_by_id': AsyncMock(return_value=protocol_entity),
                'update': AsyncMock(return_value=protocol_entity),
            },
        )()
        protocol_service = ProtocolService(protocol_repo=fake_repo, query_db=query_db)

        model = ProtocolModel(protocolId=1, protocolName='new-name')
        result = await protocol_service.edit_protocol_services(model)

        assert result.is_success is True
        assert protocol_entity.protocol_name == 'new-name'
        fake_repo.update.assert_awaited_once_with(protocol_entity)
        query_db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_protocol_batch_uses_repository_commit(self):
        query_db = AsyncMock()
        query_db.commit = AsyncMock()

        fake_repo = type(
            'FakeProtocolRepo',
            (),
            {
                'soft_delete_batch': AsyncMock(return_value=1),
                'commit': AsyncMock(return_value=None),
            },
        )()
        protocol_service = ProtocolService(protocol_repo=fake_repo, query_db=query_db)

        summary = await protocol_service.delete_protocol_batch_services(protocol_ids=[1, 2], operator='tester')

        assert len(summary['failed']) == 0
        assert len(summary['success']) == 2
        assert fake_repo.soft_delete_batch.await_count == 2
        assert fake_repo.commit.await_count == 2
        query_db.commit.assert_not_awaited()
