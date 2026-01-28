"""
Unit tests for dictionary service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from module_admin.service.dict_service import DictService
from module_admin.entity.do.dict_do import SysDictType, SysDictData


@pytest.fixture
def mock_dict_dao():
    """Create mock dictionary DAO."""
    dao = MagicMock()
    dao.get_dict_type_by_id = AsyncMock()
    dao.get_dict_data_by_id = AsyncMock()
    dao.get_dict_type_list = AsyncMock()
    dao.get_dict_data_list = AsyncMock()
    dao.add_dict_type = AsyncMock()
    dao.add_dict_data = AsyncMock()
    dao.edit_dict_type = AsyncMock()
    dao.edit_dict_data = AsyncMock()
    dao.delete_dict_type = AsyncMock()
    dao.delete_dict_data = AsyncMock()
    return dao


@pytest.fixture
def dict_service(mock_dict_dao):
    """Create dict service with mocked dependencies."""
    service = DictService()
    service.dict_dao = mock_dict_dao
    return service


@pytest.fixture
def sample_dict_type():
    """Create sample dictionary type."""
    return SysDictType(
        dict_id=1,
        dict_name='用户性别',
        dict_type='sys_user_sex',
        status='0',
        create_time=datetime.now(),
    )


@pytest.fixture
def sample_dict_data():
    """Create sample dictionary data."""
    return [
        SysDictData(
            dict_code=1,
            dict_type='sys_user_sex',
            dict_label='男',
            dict_value='0',
            dict_sort=1,
            status='0',
        ),
        SysDictData(
            dict_code=2,
            dict_type='sys_user_sex',
            dict_label='女',
            dict_value='1',
            dict_sort=2,
            status='0',
        ),
    ]


class TestDictServiceTypeOperations:
    """Test suite for dictionary type operations."""

    @pytest.mark.asyncio
    async def test_get_dict_type_by_id(self, dict_service, mock_dict_dao, sample_dict_type):
        """Test getting dictionary type by ID."""
        mock_dict_dao.get_dict_type_by_id.return_value = sample_dict_type

        result = await dict_service.get_dict_type_by_id(1)

        assert result is not None
        assert result.dict_type == 'sys_user_sex'

    @pytest.mark.asyncio
    async def test_add_dict_type(self, dict_service, mock_dict_dao):
        """Test adding dictionary type."""
        mock_dict_dao.add_dict_type.return_value = 1

        dict_data = {
            'dict_name': '用户状态',
            'dict_type': 'sys_user_status',
            'status': '0',
        }

        result = await dict_service.add_dict_type(dict_data)

        assert result == 1

    @pytest.mark.asyncio
    async def test_add_dict_type_duplicate(self, dict_service, mock_dict_dao, sample_dict_type):
        """Test adding duplicate dictionary type."""
        mock_dict_dao.get_dict_type_by_type = AsyncMock(return_value=sample_dict_type)

        dict_data = {
            'dict_name': '用户性别',
            'dict_type': 'sys_user_sex',
        }

        with pytest.raises(ValueError, match='字典类型已存在'):
            await dict_service.add_dict_type(dict_data)


class TestDictServiceDataOperations:
    """Test suite for dictionary data operations."""

    @pytest.mark.asyncio
    async def test_get_dict_data_by_type(self, dict_service, mock_dict_dao, sample_dict_data):
        """Test getting dictionary data by type."""
        mock_dict_dao.get_dict_data_list.return_value = sample_dict_data

        result = await dict_service.get_dict_data_by_type('sys_user_sex')

        assert len(result) == 2
        assert result[0].dict_label == '男'

    @pytest.mark.asyncio
    async def test_add_dict_data(self, dict_service, mock_dict_dao):
        """Test adding dictionary data."""
        mock_dict_dao.add_dict_data.return_value = 1

        dict_data = {
            'dict_type': 'sys_user_sex',
            'dict_label': '未知',
            'dict_value': '2',
            'dict_sort': 3,
        }

        result = await dict_service.add_dict_data(dict_data)

        assert result == 1

    @pytest.mark.asyncio
    async def test_get_dict_label(self, dict_service, mock_dict_dao, sample_dict_data):
        """Test getting dictionary label by value."""
        mock_dict_dao.get_dict_data_list.return_value = sample_dict_data

        result = await dict_service.get_dict_label('sys_user_sex', '0')

        assert result == '男'

    @pytest.mark.asyncio
    async def test_get_dict_value(self, dict_service, mock_dict_dao, sample_dict_data):
        """Test getting dictionary value by label."""
        mock_dict_dao.get_dict_data_list.return_value = sample_dict_data

        result = await dict_service.get_dict_value('sys_user_sex', '女')

        assert result == '1'


class TestDictServiceCache:
    """Test suite for dictionary caching."""

    @pytest.mark.asyncio
    async def test_refresh_dict_cache(self, dict_service, mock_dict_dao, sample_dict_data):
        """Test refreshing dictionary cache."""
        mock_dict_dao.get_dict_data_list.return_value = sample_dict_data

        await dict_service.refresh_dict_cache('sys_user_sex')

        # Should fetch from DAO
        mock_dict_dao.get_dict_data_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_dict_cache(self, dict_service):
        """Test clearing dictionary cache."""
        await dict_service.clear_dict_cache()

        # Cache should be empty
        assert dict_service.cache == {}
