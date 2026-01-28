"""
Unit tests for project service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st

from module_admin.service.project_service import ProjectService
from module_admin.entity.do.project_do import Project
from module_admin.entity.vo.project_vo import ProjectQueryModel, AddProjectModel, EditProjectModel


@pytest.fixture
def mock_project_dao():
    """Create mock project DAO."""
    dao = MagicMock()
    dao.get_project_by_id = AsyncMock()
    dao.get_project_list = AsyncMock()
    dao.add_project = AsyncMock()
    dao.edit_project = AsyncMock()
    dao.delete_project = AsyncMock()
    dao.count_projects = AsyncMock()
    return dao


@pytest.fixture
def project_service(mock_project_dao):
    """Create project service with mocked dependencies."""
    service = ProjectService()
    service.project_dao = mock_project_dao
    return service


@pytest.fixture
def sample_project():
    """Create sample project for testing."""
    return Project(
        project_id=1,
        project_name='Test Project',
        project_code='TEST001',
        description='Test project description',
        status='0',
        del_flag='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


class TestProjectServiceQuery:
    """Test suite for project query operations."""

    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self, project_service, mock_project_dao, sample_project):
        """Test getting project by ID successfully."""
        mock_project_dao.get_project_by_id.return_value = sample_project

        result = await project_service.get_project_by_id(1)

        assert result is not None
        assert result.project_id == 1
        assert result.project_name == 'Test Project'
        mock_project_dao.get_project_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, project_service, mock_project_dao):
        """Test getting non-existent project."""
        mock_project_dao.get_project_by_id.return_value = None

        result = await project_service.get_project_by_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_project_list_with_filters(self, project_service, mock_project_dao, sample_project):
        """Test getting project list with filters."""
        mock_project_dao.get_project_list.return_value = [sample_project]
        mock_project_dao.count_projects.return_value = 1

        query = ProjectQueryModel(project_name='Test', status='0', page_num=1, page_size=10)
        result = await project_service.get_project_list(query)

        assert result['total'] == 1
        assert len(result['rows']) == 1
        assert result['rows'][0].project_name == 'Test Project'

    @pytest.mark.asyncio
    async def test_get_project_list_pagination(self, project_service, mock_project_dao):
        """Test project list pagination."""
        projects = [
            Project(project_id=i, project_name=f'Project {i}', project_code=f'P{i:03d}')
            for i in range(1, 6)
        ]
        mock_project_dao.get_project_list.return_value = projects[:3]
        mock_project_dao.count_projects.return_value = 5

        query = ProjectQueryModel(page_num=1, page_size=3)
        result = await project_service.get_project_list(query)

        assert result['total'] == 5
        assert len(result['rows']) == 3


class TestProjectServiceCreate:
    """Test suite for project creation operations."""

    @pytest.mark.asyncio
    async def test_add_project_success(self, project_service, mock_project_dao):
        """Test adding new project successfully."""
        mock_project_dao.add_project.return_value = 1

        project_data = AddProjectModel(
            project_name='New Project',
            project_code='NEW001',
            description='New project description',
            status='0',
        )

        result = await project_service.add_project(project_data)

        assert result == 1
        mock_project_dao.add_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_project_validates_name(self, project_service, mock_project_dao):
        """Test project creation validates name."""
        project_data = AddProjectModel(
            project_name='',
            project_code='NEW001',
        )

        with pytest.raises(ValueError, match='项目名称不能为空'):
            await project_service.add_project(project_data)

    @pytest.mark.asyncio
    async def test_add_project_validates_code(self, project_service, mock_project_dao):
        """Test project creation validates code."""
        project_data = AddProjectModel(
            project_name='New Project',
            project_code='',
        )

        with pytest.raises(ValueError, match='项目编码不能为空'):
            await project_service.add_project(project_data)

    @pytest.mark.asyncio
    async def test_add_project_duplicate_code(self, project_service, mock_project_dao, sample_project):
        """Test adding project with duplicate code."""
        mock_project_dao.get_project_by_code = AsyncMock(return_value=sample_project)

        project_data = AddProjectModel(
            project_name='New Project',
            project_code='TEST001',
        )

        with pytest.raises(ValueError, match='项目编码已存在'):
            await project_service.add_project(project_data)


class TestProjectServiceUpdate:
    """Test suite for project update operations."""

    @pytest.mark.asyncio
    async def test_edit_project_success(self, project_service, mock_project_dao, sample_project):
        """Test editing project successfully."""
        mock_project_dao.get_project_by_id.return_value = sample_project
        mock_project_dao.edit_project.return_value = True

        project_data = EditProjectModel(
            project_id=1,
            project_name='Updated Project',
            description='Updated description',
        )

        result = await project_service.edit_project(project_data)

        assert result is True
        mock_project_dao.edit_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_project_not_found(self, project_service, mock_project_dao):
        """Test editing non-existent project."""
        mock_project_dao.get_project_by_id.return_value = None

        project_data = EditProjectModel(project_id=999, project_name='Updated')

        with pytest.raises(ValueError, match='项目不存在'):
            await project_service.edit_project(project_data)

    @pytest.mark.asyncio
    async def test_edit_project_validates_status(self, project_service, mock_project_dao, sample_project):
        """Test editing project validates status."""
        mock_project_dao.get_project_by_id.return_value = sample_project

        project_data = EditProjectModel(project_id=1, status='9')

        with pytest.raises(ValueError, match='状态值无效'):
            await project_service.edit_project(project_data)


class TestProjectServiceDelete:
    """Test suite for project deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_service, mock_project_dao, sample_project):
        """Test deleting project successfully."""
        mock_project_dao.get_project_by_id.return_value = sample_project
        mock_project_dao.delete_project.return_value = True

        result = await project_service.delete_project(1)

        assert result is True
        mock_project_dao.delete_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_service, mock_project_dao):
        """Test deleting non-existent project."""
        mock_project_dao.get_project_by_id.return_value = None

        with pytest.raises(ValueError, match='项目不存在'):
            await project_service.delete_project(999)

    @pytest.mark.asyncio
    async def test_batch_delete_projects(self, project_service, mock_project_dao):
        """Test batch deleting projects."""
        mock_project_dao.delete_project.return_value = True

        project_ids = [1, 2, 3]
        result = await project_service.batch_delete_projects(project_ids)

        assert result is True
        assert mock_project_dao.delete_project.call_count == 3


class TestProjectServiceValidation:
    """Test suite for project validation logic."""

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def test_validate_project_name_property(self, project_name: str):
        """Property test: valid project names should pass validation."""
        service = ProjectService()
        # Should not raise exception
        service._validate_project_name(project_name)

    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))))
    def test_validate_project_code_property(self, project_code: str):
        """Property test: valid project codes should pass validation."""
        service = ProjectService()
        # Should not raise exception
        service._validate_project_code(project_code)

    def test_validate_project_name_too_long(self):
        """Test project name length validation."""
        service = ProjectService()
        long_name = 'A' * 101

        with pytest.raises(ValueError, match='项目名称长度不能超过100'):
            service._validate_project_name(long_name)

    def test_validate_project_code_invalid_chars(self):
        """Test project code character validation."""
        service = ProjectService()

        with pytest.raises(ValueError, match='项目编码只能包含字母和数字'):
            service._validate_project_code('TEST-001')


class TestProjectServiceExport:
    """Test suite for project export operations."""

    @pytest.mark.asyncio
    async def test_export_project_success(self, project_service, mock_project_dao, sample_project):
        """Test exporting project data."""
        mock_project_dao.get_project_by_id.return_value = sample_project

        result = await project_service.export_project(1)

        assert result is not None
        assert 'project_name' in result
        assert 'topology' in result
        assert 'devices' in result

    @pytest.mark.asyncio
    async def test_export_project_not_found(self, project_service, mock_project_dao):
        """Test exporting non-existent project."""
        mock_project_dao.get_project_by_id.return_value = None

        with pytest.raises(ValueError, match='项目不存在'):
            await project_service.export_project(999)

    @pytest.mark.asyncio
    async def test_import_project_success(self, project_service, mock_project_dao):
        """Test importing project data."""
        mock_project_dao.add_project.return_value = 1

        project_data = {
            'project_name': 'Imported Project',
            'project_code': 'IMP001',
            'topology': {},
            'devices': [],
        }

        result = await project_service.import_project(project_data)

        assert result == 1
        mock_project_dao.add_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_project_validates_data(self, project_service, mock_project_dao):
        """Test import validates project data."""
        invalid_data = {'invalid': 'data'}

        with pytest.raises(ValueError, match='导入数据格式不正确'):
            await project_service.import_project(invalid_data)
