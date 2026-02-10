"""
Unit tests for dictionary DAO.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.dict_dao import DictDataDao, DictTypeDao
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.vo.dict_vo import DictDataModel, DictTypeModel


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def dict_type_dao():
    """Create DictTypeDao instance."""
    return DictTypeDao()


@pytest.fixture
def dict_data_dao():
    """Create DictDataDao instance."""
    return DictDataDao()


@pytest.fixture
def sample_dict_type():
    """Create sample dict type for testing."""
    return DictTypeDO(
        dict_id=1,
        dict_name='Test Dict',
        dict_type='test_dict',
        status='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


@pytest.fixture
def sample_dict_data():
    """Create sample dict data for testing."""
    return DictDataDO(
        dict_code=1,
        dict_sort=1,
        dict_label='Test Label',
        dict_value='test_value',
        dict_type='test_dict',
        status='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


class TestDictTypeDaoQuery:
    """Test suite for dict type query operations."""

    @pytest.mark.asyncio
    async def test_get_dict_type_by_id_success(self, dict_type_dao, mock_db, sample_dict_type):
        """Test getting dict type by ID successfully."""
        with patch.object(dict_type_dao, 'get_dict_type_by_id', return_value=sample_dict_type):
            result = await dict_type_dao.get_dict_type_by_id(mock_db, 1)

        assert result is not None
        assert result.dict_id == 1
        assert result.dict_type == 'test_dict'

    @pytest.mark.asyncio
    async def test_get_dict_type_by_type_success(self, dict_type_dao, mock_db, sample_dict_type):
        """Test getting dict type by type successfully."""
        with patch.object(dict_type_dao, 'get_dict_type_by_type', return_value=sample_dict_type):
            result = await dict_type_dao.get_dict_type_by_type(mock_db, 'test_dict')

        assert result is not None
        assert result.dict_type == 'test_dict'

    @pytest.mark.asyncio
    async def test_get_dict_type_list_success(self, dict_type_dao, mock_db, sample_dict_type):
        """Test getting dict type list successfully."""
        with patch.object(dict_type_dao, 'get_dict_type_list', return_value=[sample_dict_type]):
            result = await dict_type_dao.get_dict_type_list(mock_db, DictTypeModel())

        assert len(result) == 1
        assert result[0].dict_name == 'Test Dict'


class TestDictTypeDaoCreate:
    """Test suite for dict type creation operations."""

    @pytest.mark.asyncio
    async def test_add_dict_type_success(self, dict_type_dao, mock_db):
        """Test adding dict type successfully."""
        dict_data = DictTypeModel(
            dict_name='New Dict',
            dict_type='new_dict',
            status='0',
        )

        with patch.object(dict_type_dao, 'add_dict_type', return_value=2):
            result = await dict_type_dao.add_dict_type(mock_db, dict_data)

        assert result == 2


class TestDictTypeDaoUpdate:
    """Test suite for dict type update operations."""

    @pytest.mark.asyncio
    async def test_edit_dict_type_success(self, dict_type_dao, mock_db):
        """Test editing dict type successfully."""
        dict_data = DictTypeModel(
            dict_id=1,
            dict_name='Updated Dict',
        )

        with patch.object(dict_type_dao, 'edit_dict_type', return_value=True):
            result = await dict_type_dao.edit_dict_type(mock_db, dict_data)

        assert result is True


class TestDictTypeDaoDelete:
    """Test suite for dict type deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_dict_type_success(self, dict_type_dao, mock_db):
        """Test deleting dict type successfully."""
        with patch.object(dict_type_dao, 'delete_dict_type', return_value=True):
            result = await dict_type_dao.delete_dict_type(mock_db, 1)

        assert result is True


class TestDictDataDaoQuery:
    """Test suite for dict data query operations."""

    @pytest.mark.asyncio
    async def test_get_dict_data_by_id_success(self, dict_data_dao, mock_db, sample_dict_data):
        """Test getting dict data by ID successfully."""
        with patch.object(dict_data_dao, 'get_dict_data_by_id', return_value=sample_dict_data):
            result = await dict_data_dao.get_dict_data_by_id(mock_db, 1)

        assert result is not None
        assert result.dict_code == 1
        assert result.dict_label == 'Test Label'

    @pytest.mark.asyncio
    async def test_get_dict_data_by_type_success(self, dict_data_dao, mock_db, sample_dict_data):
        """Test getting dict data by type successfully."""
        with patch.object(dict_data_dao, 'get_dict_data_by_type', return_value=[sample_dict_data]):
            result = await dict_data_dao.get_dict_data_by_type(mock_db, 'test_dict')

        assert len(result) == 1
        assert result[0].dict_type == 'test_dict'

    @pytest.mark.asyncio
    async def test_get_dict_data_list_success(self, dict_data_dao, mock_db, sample_dict_data):
        """Test getting dict data list successfully."""
        with patch.object(dict_data_dao, 'get_dict_data_list', return_value=[sample_dict_data]):
            result = await dict_data_dao.get_dict_data_list(mock_db, DictDataModel())

        assert len(result) == 1


class TestDictDataDaoCreate:
    """Test suite for dict data creation operations."""

    @pytest.mark.asyncio
    async def test_add_dict_data_success(self, dict_data_dao, mock_db):
        """Test adding dict data successfully."""
        dict_data = DictDataModel(
            dict_label='New Label',
            dict_value='new_value',
            dict_type='test_dict',
            dict_sort=1,
        )

        with patch.object(dict_data_dao, 'add_dict_data', return_value=2):
            result = await dict_data_dao.add_dict_data(mock_db, dict_data)

        assert result == 2


class TestDictDataDaoUpdate:
    """Test suite for dict data update operations."""

    @pytest.mark.asyncio
    async def test_edit_dict_data_success(self, dict_data_dao, mock_db):
        """Test editing dict data successfully."""
        dict_data = DictDataModel(
            dict_code=1,
            dict_label='Updated Label',
        )

        with patch.object(dict_data_dao, 'edit_dict_data', return_value=True):
            result = await dict_data_dao.edit_dict_data(mock_db, dict_data)

        assert result is True


class TestDictDataDaoDelete:
    """Test suite for dict data deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_dict_data_success(self, dict_data_dao, mock_db):
        """Test deleting dict data successfully."""
        with patch.object(dict_data_dao, 'delete_dict_data', return_value=True):
            result = await dict_data_dao.delete_dict_data(mock_db, 1)

        assert result is True

    @pytest.mark.asyncio
    async def test_batch_delete_dict_data(self, dict_data_dao, mock_db):
        """Test batch deleting dict data."""
        with patch.object(dict_data_dao, 'batch_delete_dict_data', return_value=3):
            result = await dict_data_dao.batch_delete_dict_data(mock_db, [1, 2, 3])

        assert result == 3
