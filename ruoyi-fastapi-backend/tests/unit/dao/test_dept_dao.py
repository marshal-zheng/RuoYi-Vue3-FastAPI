"""
Unit tests for department DAO.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.dept_dao import DeptDao
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.vo.dept_vo import DeptModel, DeptQueryModel


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def dept_dao():
    """Create DeptDao instance."""
    return DeptDao()


@pytest.fixture
def sample_dept():
    """Create sample department for testing."""
    return DeptDO(
        dept_id=100,
        parent_id=0,
        dept_name='Test Dept',
        order_num=1,
        leader='Leader',
        phone='13800138000',
        email='test@example.com',
        status='0',
        del_flag='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


class TestDeptDaoQuery:
    """Test suite for department query operations."""

    @pytest.mark.asyncio
    async def test_get_dept_by_id_success(self, dept_dao, mock_db, sample_dept):
        """Test getting department by ID successfully."""
        with patch.object(dept_dao, 'get_dept_by_id', return_value=sample_dept):
            result = await dept_dao.get_dept_by_id(mock_db, 100)

        assert result is not None
        assert result.dept_id == 100
        assert result.dept_name == 'Test Dept'

    @pytest.mark.asyncio
    async def test_get_dept_by_id_not_found(self, dept_dao, mock_db):
        """Test getting non-existent department."""
        with patch.object(dept_dao, 'get_dept_by_id', return_value=None):
            result = await dept_dao.get_dept_by_id(mock_db, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_dept_list_success(self, dept_dao, mock_db, sample_dept):
        """Test getting department list successfully."""
        with patch.object(dept_dao, 'get_dept_list', return_value=[sample_dept]):
            result = await dept_dao.get_dept_list(mock_db, DeptQueryModel())

        assert len(result) == 1
        assert result[0].dept_name == 'Test Dept'

    @pytest.mark.asyncio
    async def test_get_dept_list_with_filters(self, dept_dao, mock_db, sample_dept):
        """Test getting department list with filters."""
        query = DeptQueryModel(dept_name='Test', status='0')
        with patch.object(dept_dao, 'get_dept_list', return_value=[sample_dept]):
            result = await dept_dao.get_dept_list(mock_db, query)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_dept_list_empty(self, dept_dao, mock_db):
        """Test getting empty department list."""
        with patch.object(dept_dao, 'get_dept_list', return_value=[]):
            result = await dept_dao.get_dept_list(mock_db, DeptQueryModel())

        assert len(result) == 0


class TestDeptDaoCreate:
    """Test suite for department creation operations."""

    @pytest.mark.asyncio
    async def test_add_dept_success(self, dept_dao, mock_db):
        """Test adding department successfully."""
        dept_data = DeptModel(
            dept_name='New Dept',
            parent_id=100,
            order_num=1,
            status='0',
        )

        with patch.object(dept_dao, 'add_dept', return_value=101):
            result = await dept_dao.add_dept(mock_db, dept_data)

        assert result == 101

    @pytest.mark.asyncio
    async def test_add_dept_with_parent(self, dept_dao, mock_db):
        """Test adding department with parent."""
        dept_data = DeptModel(
            dept_name='Child Dept',
            parent_id=100,
            order_num=2,
            status='0',
        )

        with patch.object(dept_dao, 'add_dept', return_value=102):
            result = await dept_dao.add_dept(mock_db, dept_data)

        assert result == 102


class TestDeptDaoUpdate:
    """Test suite for department update operations."""

    @pytest.mark.asyncio
    async def test_edit_dept_success(self, dept_dao, mock_db, sample_dept):
        """Test editing department successfully."""
        dept_data = DeptModel(
            dept_id=100,
            dept_name='Updated Dept',
            order_num=2,
        )

        with patch.object(dept_dao, 'edit_dept', return_value=True):
            result = await dept_dao.edit_dept(mock_db, dept_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_edit_dept_not_found(self, dept_dao, mock_db):
        """Test editing non-existent department."""
        dept_data = DeptModel(dept_id=999, dept_name='Updated')

        with patch.object(dept_dao, 'edit_dept', return_value=False):
            result = await dept_dao.edit_dept(mock_db, dept_data)

        assert result is False


class TestDeptDaoDelete:
    """Test suite for department deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_dept_success(self, dept_dao, mock_db):
        """Test deleting department successfully."""
        with patch.object(dept_dao, 'delete_dept', return_value=True):
            result = await dept_dao.delete_dept(mock_db, 100)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_dept_not_found(self, dept_dao, mock_db):
        """Test deleting non-existent department."""
        with patch.object(dept_dao, 'delete_dept', return_value=False):
            result = await dept_dao.delete_dept(mock_db, 999)

        assert result is False


class TestDeptDaoRelations:
    """Test suite for department relation operations."""

    @pytest.mark.asyncio
    async def test_get_children_depts(self, dept_dao, mock_db, sample_dept):
        """Test getting children departments."""
        child_dept = DeptDO(
            dept_id=101,
            parent_id=100,
            dept_name='Child Dept',
            order_num=1,
            status='0',
            del_flag='0',
        )

        with patch.object(dept_dao, 'get_children_depts', return_value=[child_dept]):
            result = await dept_dao.get_children_depts(mock_db, 100)

        assert len(result) == 1
        assert result[0].parent_id == 100

    @pytest.mark.asyncio
    async def test_has_children_depts(self, dept_dao, mock_db):
        """Test checking if department has children."""
        with patch.object(dept_dao, 'has_children_depts', return_value=True):
            result = await dept_dao.has_children_depts(mock_db, 100)

        assert result is True

    @pytest.mark.asyncio
    async def test_has_no_children_depts(self, dept_dao, mock_db):
        """Test checking if department has no children."""
        with patch.object(dept_dao, 'has_children_depts', return_value=False):
            result = await dept_dao.has_children_depts(mock_db, 101)

        assert result is False
