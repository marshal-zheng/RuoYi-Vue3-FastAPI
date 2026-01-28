"""
Unit tests for config service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from module_admin.service.config_service import ConfigService
from module_admin.entity.do.config_do import SysConfig
from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel, DeleteConfigModel
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from exceptions.exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException
)


@pytest.fixture
def mock_request():
    """Create mock request object."""
    request = MagicMock()
    request.app.state.redis = MagicMock()
    request.app.state.redis.set = AsyncMock()
    request.app.state.redis.get = AsyncMock()
    request.app.state.redis.delete = AsyncMock()
    request.app.state.redis.keys = AsyncMock(return_value=[])
    return request


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = MagicMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock()
    redis.delete = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    return redis


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_config():
    """Create sample config for testing."""
    return SysConfig(
        config_id=1,
        config_name='系统名称',
        config_key='sys.name',
        config_value='RuoYi',
        config_type='N',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


@pytest.fixture
def sample_builtin_config():
    """Create sample built-in config."""
    return SysConfig(
        config_id=2,
        config_name='内置参数',
        config_key='sys.builtin',
        config_value='value',
        config_type='Y',  # Built-in
        create_time=datetime.now(),
    )


class TestConfigServiceQuery:
    """Test suite for config query operations."""

    @pytest.mark.asyncio
    async def test_get_config_list_with_pagination(self, mock_db, sample_config):
        """Test getting config list with pagination."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_config]
            mock_result.total = 1
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = ConfigPageQueryModel(page_num=1, page_size=10)
            result = await ConfigService.get_config_list_services(mock_db, query, is_page=True)
            
            assert result.total == 1
            assert len(result.rows) == 1

    @pytest.mark.asyncio
    async def test_get_config_list_without_pagination(self, mock_db, sample_config):
        """Test getting config list without pagination."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_config]
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = ConfigPageQueryModel(page_num=1, page_size=10)
            result = await ConfigService.get_config_list_services(mock_db, query, is_page=False)
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_config_list_with_filters(self, mock_db, sample_config):
        """Test getting config list with filters."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_config]
            mock_result.total = 1
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = ConfigPageQueryModel(
                config_name='系统',
                config_key='sys',
                config_type='N',
                page_num=1,
                page_size=10
            )
            result = await ConfigService.get_config_list_services(mock_db, query, is_page=True)
            
            assert result.total == 1
            mock_repo.paginate_with_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_config_detail_success(self, mock_db, sample_config):
        """Test getting config detail successfully."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=sample_config)
            
            result = await ConfigService.config_detail_services(mock_db, 1)
            
            assert result.config_id == 1
            assert result.config_name == '系统名称'

    @pytest.mark.asyncio
    async def test_config_detail_not_found(self, mock_db):
        """Test getting non-existent config detail."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=None)
            
            result = await ConfigService.config_detail_services(mock_db, 999)
            
            assert result.config_id is None


class TestConfigServiceCache:
    """Test suite for config cache operations."""

    @pytest.mark.asyncio
    async def test_init_cache_sys_config(self, mock_db, mock_redis, sample_config):
        """Test initializing config cache."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [{'configKey': 'sys.name', 'configValue': 'RuoYi'}]
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            await ConfigService.init_cache_sys_config_services(mock_db, mock_redis)
            
            mock_redis.keys.assert_called_once()
            mock_redis.set.assert_called()

    @pytest.mark.asyncio
    async def test_init_cache_clears_existing_keys(self, mock_db, mock_redis):
        """Test that init cache clears existing keys."""
        mock_redis.keys = AsyncMock(return_value=['sys_config:key1', 'sys_config:key2'])
        
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = []
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            await ConfigService.init_cache_sys_config_services(mock_db, mock_redis)
            
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_config_from_cache(self, mock_redis):
        """Test querying config from cache."""
        mock_redis.get = AsyncMock(return_value='RuoYi')
        
        result = await ConfigService.query_config_list_from_cache_services(mock_redis, 'sys.name')
        
        assert result == 'RuoYi'
        mock_redis.get.assert_called_once_with(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.name')

    @pytest.mark.asyncio
    async def test_refresh_sys_config(self, mock_request, mock_db):
        """Test refreshing config cache."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = []
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            result = await ConfigService.refresh_sys_config_services(mock_request, mock_db)
            
            assert result.is_success is True
            assert result.message == '刷新成功'


class TestConfigServiceValidation:
    """Test suite for config validation operations."""

    @pytest.mark.asyncio
    async def test_check_config_key_unique_success(self, mock_db):
        """Test checking config key uniqueness - unique."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=None)
            
            config = ConfigModel(config_key='new.key', config_name='新参数', config_value='value')
            result = await ConfigService.check_config_key_unique_services(mock_db, config)
            
            assert result == CommonConstant.UNIQUE

    @pytest.mark.asyncio
    async def test_check_config_key_not_unique(self, mock_db, sample_config):
        """Test checking config key uniqueness - not unique."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=sample_config)
            
            config = ConfigModel(configId=2, configKey='sys.name', configName='系统名称', configValue='value')
            result = await ConfigService.check_config_key_unique_services(mock_db, config)
            
            assert result == CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_config_key_unique_same_config(self, mock_db, sample_config):
        """Test checking config key uniqueness - same config."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=sample_config)
            
            config = ConfigModel(configId=1, configKey='sys.name', configName='系统名称', configValue='value')
            result = await ConfigService.check_config_key_unique_services(mock_db, config)
            
            assert result == CommonConstant.UNIQUE


class TestConfigServiceCreate:
    """Test suite for config creation operations."""

    @pytest.mark.asyncio
    async def test_add_config_success(self, mock_request, mock_db):
        """Test adding new config successfully."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            new_config = ConfigModel(
                configName='新参数',
                configKey='new.key',
                configValue='value',
                configType='N'
            )
            
            result = await ConfigService.add_config_services(mock_request, mock_db, new_config)
            
            assert result.is_success is True
            mock_repo.add.assert_called_once()
            mock_request.app.state.redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_config_duplicate_key(self, mock_request, mock_db, sample_config):
        """Test adding config with duplicate key."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=sample_config)
            
            new_config = ConfigModel(
                configName='新参数',
                configKey='sys.name',
                configValue='value',
                configType='N'
            )
            
            with pytest.raises(ResourceConflictException, match='参数键名已存在'):
                await ConfigService.add_config_services(mock_request, mock_db, new_config)


class TestConfigServiceUpdate:
    """Test suite for config update operations."""

    @pytest.mark.asyncio
    async def test_edit_config_success(self, mock_request, mock_db, sample_config):
        """Test editing config successfully."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=sample_config)
            mock_repo.update = AsyncMock()
            
            with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel(
                configId=1,
                configKey='sys.name',
                configName='系统名称',
                configValue='RuoYi',
                configType='N'
            ))):
                edit_config = ConfigModel(
                    configId=1,
                    configName='更新名称',
                    configKey='sys.name',
                    configValue='NewValue',
                    configType='N'
                )
                
                result = await ConfigService.edit_config_services(mock_request, mock_db, edit_config)
                
                assert result.is_success is True
                mock_repo.update.assert_called_once()
                mock_request.app.state.redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_config_not_found(self, mock_request, mock_db):
        """Test editing non-existent config."""
        with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel())):
            edit_config = ConfigModel(
                config_id=999,
                config_name='不存在',
                config_key='not.exist',
                config_value='value'
            )
            
            with pytest.raises(ResourceNotFoundException, match='参数配置不存在'):
                await ConfigService.edit_config_services(mock_request, mock_db, edit_config)

    @pytest.mark.asyncio
    async def test_edit_config_duplicate_key(self, mock_request, mock_db, sample_config):
        """Test editing config with duplicate key."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=sample_config)
            
            with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel(
                configId=2,
                configKey='other.key',
                configName='其他参数',
                configValue='value',
                configType='N'
            ))):
                edit_config = ConfigModel(
                    configId=2,
                    configName='更新',
                    configKey='sys.name',
                    configValue='value'
                )
                
                with pytest.raises(ResourceConflictException, match='参数键名已存在'):
                    await ConfigService.edit_config_services(mock_request, mock_db, edit_config)

    @pytest.mark.asyncio
    async def test_edit_config_updates_cache_key(self, mock_request, mock_db, sample_config):
        """Test editing config updates cache when key changes."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_key = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=sample_config)
            mock_repo.update = AsyncMock()
            
            with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel(
                configId=1,
                configKey='old.key',
                configName='旧参数',
                configValue='value',
                configType='N'
            ))):
                edit_config = ConfigModel(
                    configId=1,
                    configName='新参数',
                    configKey='new.key',
                    configValue='value',
                    configType='N'
                )
                
                result = await ConfigService.edit_config_services(mock_request, mock_db, edit_config)
                
                assert result.is_success is True
                mock_request.app.state.redis.delete.assert_called_once()
                mock_request.app.state.redis.set.assert_called_once()


class TestConfigServiceDelete:
    """Test suite for config deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_config_success(self, mock_request, mock_db):
        """Test deleting config successfully."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.delete_by_id = AsyncMock()
            
            with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel(
                configId=1,
                configKey='test.key',
                configName='测试参数',
                configValue='value',
                configType='N'
            ))):
                delete_obj = DeleteConfigModel(configIds='1,2')
                result = await ConfigService.delete_config_services(mock_request, mock_db, delete_obj)
                
                assert result.is_success is True
                assert mock_repo.delete_by_id.call_count == 2
                mock_request.app.state.redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_config_empty_ids(self, mock_request, mock_db):
        """Test deleting config with empty IDs."""
        delete_obj = DeleteConfigModel(configIds='')
        
        with pytest.raises(ValidationException, match='传入参数配置id为空'):
            await ConfigService.delete_config_services(mock_request, mock_db, delete_obj)

    @pytest.mark.asyncio
    async def test_delete_builtin_config_forbidden(self, mock_request, mock_db):
        """Test that built-in config cannot be deleted."""
        with patch('module_admin.service.config_service.ConfigRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            
            with patch.object(ConfigService, 'config_detail_services', new=AsyncMock(return_value=ConfigModel(
                configId=1,
                configKey='builtin.key',
                configName='内置参数',
                configValue='value',
                configType='Y'  # Built-in
            ))):
                delete_obj = DeleteConfigModel(configIds='1')
                
                with pytest.raises(ValidationException, match='内置参数.*不能删除'):
                    await ConfigService.delete_config_services(mock_request, mock_db, delete_obj)


class TestConfigServiceExport:
    """Test suite for config export operations."""

    @pytest.mark.asyncio
    async def test_export_config_list(self):
        """Test exporting config list to Excel."""
        config_list = [
            {
                'configId': 1,
                'configName': '系统名称',
                'configKey': 'sys.name',
                'configValue': 'RuoYi',
                'configType': 'Y',
                'createBy': 'admin',
                'createTime': '2024-01-01',
                'remark': '备注'
            },
            {
                'configId': 2,
                'configName': '版本号',
                'configKey': 'sys.version',
                'configValue': '1.0.0',
                'configType': 'N',
                'createBy': 'admin',
                'createTime': '2024-01-01',
                'remark': ''
            }
        ]
        
        with patch('module_admin.service.config_service.ExcelUtil.export_list2excel') as mock_export:
            mock_export.return_value = b'excel_data'
            
            result = await ConfigService.export_config_list_services(config_list)
            
            assert result == b'excel_data'
            mock_export.assert_called_once()
            # Verify config_type was transformed
            assert config_list[0]['configType'] == '是'
            assert config_list[1]['configType'] == '否'
