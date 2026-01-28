"""
Unit tests for config DAO.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.config_dao import ConfigDao
from module_admin.entity.do.config_do import SysConfig
from module_admin.entity.vo.config_vo import ConfigModel, ConfigQueryModel


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def config_dao():
    """Create ConfigDao instance."""
    return ConfigDao()


@pytest.fixture
def sample_config():
    """Create sample config for testing."""
    return SysConfig(
        config_id=1,
        config_name='Test Config',
        config_key='test.config',
        config_value='test_value',
        config_type='Y',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


class TestConfigDaoQuery:
    """Test suite for config query operations."""

    @pytest.mark.asyncio
    async def test_get_config_by_id_success(self, config_dao, mock_db, sample_config):
        """Test getting config by ID successfully."""
        with patch.object(config_dao, 'get_config_by_id', return_value=sample_config):
            result = await config_dao.get_config_by_id(mock_db, 1)

        assert result is not None
        assert result.config_id == 1
        assert result.config_key == 'test.config'

    @pytest.mark.asyncio
    async def test_get_config_by_key_success(self, config_dao, mock_db, sample_config):
        """Test getting config by key successfully."""
        with patch.object(config_dao, 'get_config_by_key', return_value=sample_config):
            result = await config_dao.get_config_by_key(mock_db, 'test.config')

        assert result is not None
        assert result.config_key == 'test.config'

    @pytest.mark.asyncio
    async def test_get_config_list_success(self, config_dao, mock_db, sample_config):
        """Test getting config list successfully."""
        with patch.object(config_dao, 'get_config_list', return_value=[sample_config]):
            result = await config_dao.get_config_list(mock_db, ConfigQueryModel())

        assert len(result) == 1
        assert result[0].config_name == 'Test Config'

    @pytest.mark.asyncio
    async def test_get_config_list_with_filters(self, config_dao, mock_db, sample_config):
        """Test getting config list with filters."""
        query = ConfigQueryModel(config_name='Test', config_type='Y')
        with patch.object(config_dao, 'get_config_list', return_value=[sample_config]):
            result = await config_dao.get_config_list(mock_db, query)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count_configs(self, config_dao, mock_db):
        """Test counting configs."""
        with patch.object(config_dao, 'count_configs', return_value=10):
            result = await config_dao.count_configs(mock_db, ConfigQueryModel())

        assert result == 10


class TestConfigDaoCreate:
    """Test suite for config creation operations."""

    @pytest.mark.asyncio
    async def test_add_config_success(self, config_dao, mock_db):
        """Test adding config successfully."""
        config_data = ConfigModel(
            config_name='New Config',
            config_key='new.config',
            config_value='new_value',
            config_type='Y',
        )

        with patch.object(config_dao, 'add_config', return_value=2):
            result = await config_dao.add_config(mock_db, config_data)

        assert result == 2

    @pytest.mark.asyncio
    async def test_add_config_duplicate_key(self, config_dao, mock_db, sample_config):
        """Test adding config with duplicate key."""
        with patch.object(config_dao, 'get_config_by_key', return_value=sample_config):
            exists = await config_dao.get_config_by_key(mock_db, 'test.config')

        assert exists is not None


class TestConfigDaoUpdate:
    """Test suite for config update operations."""

    @pytest.mark.asyncio
    async def test_edit_config_success(self, config_dao, mock_db):
        """Test editing config successfully."""
        config_data = ConfigModel(
            config_id=1,
            config_name='Updated Config',
            config_value='updated_value',
        )

        with patch.object(config_dao, 'edit_config', return_value=True):
            result = await config_dao.edit_config(mock_db, config_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_edit_config_not_found(self, config_dao, mock_db):
        """Test editing non-existent config."""
        config_data = ConfigModel(config_id=999, config_name='Updated')

        with patch.object(config_dao, 'edit_config', return_value=False):
            result = await config_dao.edit_config(mock_db, config_data)

        assert result is False


class TestConfigDaoDelete:
    """Test suite for config deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_config_success(self, config_dao, mock_db):
        """Test deleting config successfully."""
        with patch.object(config_dao, 'delete_config', return_value=True):
            result = await config_dao.delete_config(mock_db, 1)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, config_dao, mock_db):
        """Test deleting non-existent config."""
        with patch.object(config_dao, 'delete_config', return_value=False):
            result = await config_dao.delete_config(mock_db, 999)

        assert result is False

    @pytest.mark.asyncio
    async def test_batch_delete_configs(self, config_dao, mock_db):
        """Test batch deleting configs."""
        with patch.object(config_dao, 'batch_delete_configs', return_value=3):
            result = await config_dao.batch_delete_configs(mock_db, [1, 2, 3])

        assert result == 3
