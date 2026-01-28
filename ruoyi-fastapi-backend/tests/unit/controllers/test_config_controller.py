"""
Unit tests for config controller.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from module_admin.controller.config_controller import configController


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(configController)
    return app


@pytest.fixture
def mock_config_service():
    """Create mock config service."""
    with patch('module_admin.controller.config_controller.ConfigService') as mock:
        mock.get_config_list_services = AsyncMock()
        mock.add_config_services = AsyncMock()
        mock.edit_config_services = AsyncMock()
        mock.delete_config_services = AsyncMock()
        mock.config_detail_services = AsyncMock()
        mock.get_config_key_services = AsyncMock()
        mock.refresh_config_services = AsyncMock()
        mock.export_config_list_services = AsyncMock()
        yield mock


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    user = MagicMock()
    user.user_id = 1
    user.user_name = 'admin'
    user.admin = True
    
    current_user = MagicMock()
    current_user.user = user
    return current_user


@pytest.fixture
def mock_login_service(mock_current_user):
    """Create mock login service."""
    with patch('module_admin.controller.config_controller.LoginService') as mock:
        mock.get_current_user = AsyncMock(return_value=mock_current_user)
        yield mock


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    with patch('module_admin.controller.config_controller.CheckUserInterfaceAuth') as mock:
        mock.return_value = lambda: True
        yield mock


@pytest.fixture
def mock_db():
    """Create mock database session."""
    with patch('module_admin.controller.config_controller.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


class TestConfigControllerQuery:
    """Test suite for config query endpoints."""

    def test_get_config_list_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting config list successfully."""
        mock_config_service.get_config_list_services.return_value = {
            'total': 2,
            'rows': [
                {'config_id': 1, 'config_name': 'Config1', 'config_key': 'key1'},
                {'config_id': 2, 'config_name': 'Config2', 'config_key': 'key2'},
            ],
        }

        with TestClient(app) as client:
            response = client.get('/system/config/list?pageNum=1&pageSize=10')

        assert response.status_code == 200

    def test_get_config_list_with_filters(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting config list with filters."""
        mock_config_service.get_config_list_services.return_value = {
            'total': 1,
            'rows': [{'config_id': 1, 'config_name': 'Config1'}],
        }

        with TestClient(app) as client:
            response = client.get('/system/config/list?pageNum=1&pageSize=10&configName=Config1')

        assert response.status_code == 200

    def test_get_config_detail_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting config detail successfully."""
        mock_config_service.config_detail_services.return_value = {
            'config_id': 1,
            'config_name': 'Config1',
            'config_key': 'key1',
            'config_value': 'value1',
        }

        with TestClient(app) as client:
            response = client.get('/system/config/1')

        assert response.status_code == 200

    def test_get_config_by_key_success(
        self, app, mock_config_service, mock_login_service, mock_db
    ):
        """Test getting config by key successfully."""
        mock_config_service.get_config_key_services.return_value = 'value1'

        with TestClient(app) as client:
            response = client.get('/system/config/configKey/key1')

        assert response.status_code == 200


class TestConfigControllerCreate:
    """Test suite for config creation endpoints."""

    def test_add_config_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding config successfully."""
        mock_config_service.add_config_services.return_value = MagicMock(message='新增成功')

        config_data = {
            'configName': 'New Config',
            'configKey': 'new_key',
            'configValue': 'new_value',
            'configType': 'Y',
        }

        with TestClient(app) as client:
            response = client.post('/system/config', json=config_data)

        assert response.status_code == 200

    def test_add_config_validation_error(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding config with validation error."""
        config_data = {
            'configName': '',  # Empty config name
        }

        with TestClient(app) as client:
            response = client.post('/system/config', json=config_data)

        assert response.status_code == 422


class TestConfigControllerUpdate:
    """Test suite for config update endpoints."""

    def test_edit_config_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test editing config successfully."""
        mock_config_service.edit_config_services.return_value = MagicMock(message='修改成功')

        config_data = {
            'configId': 1,
            'configName': 'Updated Config',
            'configValue': 'updated_value',
        }

        with TestClient(app) as client:
            response = client.put('/system/config', json=config_data)

        assert response.status_code == 200

    def test_refresh_config_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test refreshing config cache successfully."""
        mock_config_service.refresh_config_services.return_value = MagicMock(message='刷新成功')

        with TestClient(app) as client:
            response = client.delete('/system/config/refreshCache')

        assert response.status_code == 200


class TestConfigControllerDelete:
    """Test suite for config deletion endpoints."""

    def test_delete_config_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting config successfully."""
        mock_config_service.delete_config_services.return_value = MagicMock(message='删除成功')

        with TestClient(app) as client:
            response = client.delete('/system/config/1,2')

        assert response.status_code == 200

    def test_delete_single_config(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting single config."""
        mock_config_service.delete_config_services.return_value = MagicMock(message='删除成功')

        with TestClient(app) as client:
            response = client.delete('/system/config/1')

        assert response.status_code == 200


class TestConfigControllerExport:
    """Test suite for config export endpoints."""

    def test_export_config_list_success(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test exporting config list successfully."""
        mock_config_service.get_config_list_services.return_value = {
            'total': 2,
            'rows': [
                {'config_id': 1, 'config_name': 'Config1'},
                {'config_id': 2, 'config_name': 'Config2'},
            ],
        }
        mock_config_service.export_config_list_services.return_value = b'excel_data'

        with TestClient(app) as client:
            response = client.post('/system/config/export')

        assert response.status_code == 200


class TestConfigControllerEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_get_config_list_empty(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting empty config list."""
        mock_config_service.get_config_list_services.return_value = {
            'total': 0,
            'rows': [],
        }

        with TestClient(app) as client:
            response = client.get('/system/config/list?pageNum=1&pageSize=10')

        assert response.status_code == 200

    def test_get_config_by_key_not_found(
        self, app, mock_config_service, mock_login_service, mock_db
    ):
        """Test getting config by non-existent key."""
        mock_config_service.get_config_key_services.return_value = None

        with TestClient(app) as client:
            response = client.get('/system/config/configKey/nonexistent')

        assert response.status_code == 200

    def test_add_config_with_minimal_data(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding config with minimal required data."""
        mock_config_service.add_config_services.return_value = MagicMock(message='新增成功')

        config_data = {
            'configName': 'Minimal Config',
            'configKey': 'minimal_key',
            'configValue': 'minimal_value',
        }

        with TestClient(app) as client:
            response = client.post('/system/config', json=config_data)

        assert response.status_code == 200

    def test_delete_empty_config_ids(
        self, app, mock_config_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting with empty config IDs."""
        mock_config_service.delete_config_services.return_value = MagicMock(message='删除成功')

        with TestClient(app) as client:
            response = client.delete('/system/config/')

        assert response.status_code == 200
