"""
Unit tests for department service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from modules.system.application.services.dept_service import DeptService
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.vo.dept_vo import DeptModel, DeleteDeptModel
from config.constant import CommonConstant
from exceptions.exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    PermissionException
)


@pytest.fixture
def mock_dept_repo():
    """Create mock department repository."""
    repo = MagicMock()
    repo.find_all_for_tree = AsyncMock()
    repo.find_for_edit_option = AsyncMock()
    repo.find_with_filters = AsyncMock()
    repo.find_by_parent_and_name = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.add = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.find_active_by_id = AsyncMock()
    repo.count_normal_children = AsyncMock()
    repo.count_direct_children = AsyncMock()
    repo.count_users = AsyncMock()
    repo.update_status_normal = AsyncMock()
    repo.find_children = AsyncMock()
    repo.update_children_ancestors = AsyncMock()
    return repo


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_dept():
    """Create sample department for testing."""
    return DeptDO(
        dept_id=1,
        parent_id=0,
        ancestors='0',
        dept_name='测试部门',
        order_num=1,
        leader='张三',
        phone='13800138000',
        email='test@example.com',
        status='0',
        del_flag='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


@pytest.fixture
def sample_child_dept():
    """Create sample child department."""
    return DeptDO(
        dept_id=2,
        parent_id=1,
        ancestors='0,1',
        dept_name='子部门',
        order_num=1,
        status='0',
        del_flag='0',
        create_time=datetime.now(),
    )


class TestDeptServiceQuery:
    """Test suite for department query operations."""

    @pytest.mark.asyncio
    async def test_get_dept_tree_success(self, mock_db, sample_dept, sample_child_dept):
        """Test getting department tree successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_all_for_tree = AsyncMock(return_value=[sample_dept, sample_child_dept])
            
            query = DeptModel(dept_name='测试')
            result = await DeptService(mock_repo, mock_db).get_dept_tree_services(query, '')
            
            assert isinstance(result, list)
            assert len(result) > 0
            mock_repo.find_all_for_tree.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dept_for_edit_option(self, mock_db, sample_dept):
        """Test getting department edit options."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_for_edit_option = AsyncMock(return_value=[sample_dept])
            
            query = DeptModel(dept_id=2)
            result = await DeptService(mock_repo, mock_db).get_dept_for_edit_option_services(query, '')
            
            assert isinstance(result, list)
            mock_repo.find_for_edit_option.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dept_list_with_filters(self, mock_db, sample_dept):
        """Test getting department list with filters."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_with_filters = AsyncMock(return_value=[sample_dept])
            
            query = DeptModel(dept_name='测试', status='0')
            result = await DeptService(mock_repo, mock_db).get_dept_list_services(query, '')
            
            assert isinstance(result, list)
            mock_repo.find_with_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_dept_detail_success(self, mock_db, sample_dept):
        """Test getting department detail successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_active_by_id = AsyncMock(return_value=sample_dept)
            
            result = await DeptService(mock_repo, mock_db).dept_detail_services(1)
            
            assert result.dept_id == 1
            assert result.dept_name == '测试部门'

    @pytest.mark.asyncio
    async def test_dept_detail_not_found(self, mock_db):
        """Test getting non-existent department detail."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_active_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(ResourceNotFoundException):
                await DeptService(mock_repo, mock_db).dept_detail_services(999)


class TestDeptServiceDataScope:
    """Test suite for department data scope operations."""

    @pytest.mark.asyncio
    async def test_check_dept_data_scope_success(self, mock_db, sample_dept):
        """Test checking department data scope successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_with_filters = AsyncMock(return_value=[sample_dept])
            
            result = await DeptService(mock_repo, mock_db).check_dept_data_scope_services(1, '')
            
            assert result.is_success is True

    @pytest.mark.asyncio
    async def test_check_dept_data_scope_no_permission(self, mock_db):
        """Test checking department data scope without permission."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_with_filters = AsyncMock(return_value=[])
            
            with pytest.raises(PermissionException, match='没有权限访问部门数据'):
                await DeptService(mock_repo, mock_db).check_dept_data_scope_services(1, '')


class TestDeptServiceValidation:
    """Test suite for department validation operations."""

    @pytest.mark.asyncio
    async def test_check_dept_name_unique_success(self, mock_db):
        """Test checking department name uniqueness - unique."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            
            dept = DeptModel(parent_id=0, dept_name='新部门')
            result = await DeptService(mock_repo, mock_db).check_dept_name_unique_services(dept)
            
            assert result == CommonConstant.UNIQUE

    @pytest.mark.asyncio
    async def test_check_dept_name_not_unique(self, mock_db, sample_dept):
        """Test checking department name uniqueness - not unique."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=sample_dept)
            
            dept = DeptModel(dept_id=2, parent_id=0, dept_name='测试部门')
            result = await DeptService(mock_repo, mock_db).check_dept_name_unique_services(dept)
            
            assert result == CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_dept_name_unique_same_dept(self, mock_db, sample_dept):
        """Test checking department name uniqueness - same department."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=sample_dept)
            
            dept = DeptModel(dept_id=1, parent_id=0, dept_name='测试部门')
            result = await DeptService(mock_repo, mock_db).check_dept_name_unique_services(dept)
            
            assert result == CommonConstant.UNIQUE


class TestDeptServiceCreate:
    """Test suite for department creation operations."""

    @pytest.mark.asyncio
    async def test_add_dept_success(self, mock_db, sample_dept):
        """Test adding new department successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=sample_dept)
            mock_repo.add = AsyncMock()
            
            new_dept = DeptModel(
                parent_id=1,
                dept_name='新部门',
                order_num=1,
                status='0'
            )
            
            result = await DeptService(mock_repo, mock_db).add_dept_services(new_dept)
            
            assert result.is_success is True
            mock_repo.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_dept_duplicate_name(self, mock_db, sample_dept):
        """Test adding department with duplicate name."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=sample_dept)
            
            new_dept = DeptModel(
                parent_id=0,
                dept_name='测试部门',
                order_num=1
            )
            
            with pytest.raises(ResourceConflictException, match='部门名称已存在'):
                await DeptService(mock_repo, mock_db).add_dept_services(new_dept)

    @pytest.mark.asyncio
    async def test_add_dept_parent_disabled(self, mock_db):
        """Test adding department under disabled parent."""
        disabled_parent = DeptDO(
            dept_id=1,
            parent_id=0,
            ancestors='0',
            dept_name='停用部门',
            status='1',  # Disabled
            del_flag='0'
        )
        
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=disabled_parent)
            
            new_dept = DeptModel(
                parent_id=1,
                dept_name='新部门',
                order_num=1
            )
            
            with pytest.raises(ValidationException, match='停用，不允许新增'):
                await DeptService(mock_repo, mock_db).add_dept_services(new_dept)


class TestDeptServiceUpdate:
    """Test suite for department update operations."""

    @pytest.mark.asyncio
    async def test_edit_dept_success(self, mock_db, sample_dept):
        """Test editing department successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            mock_repo.count_normal_children = AsyncMock(return_value=0)
            mock_repo.find_by_id = AsyncMock(return_value=sample_dept)
            mock_repo.update = AsyncMock()
            mock_repo.find_children = AsyncMock(return_value=[])
            mock_repo.update_status_normal = AsyncMock()
            
            edit_dept = DeptModel(
                dept_id=1,
                parent_id=0,
                dept_name='更新部门',
                status='0'
            )
            
            result = await DeptService(mock_repo, mock_db).edit_dept_services(edit_dept)
            
            assert result.is_success is True
            mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_dept_duplicate_name(self, mock_db, sample_dept):
        """Test editing department with duplicate name."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=DeptDO(dept_id=2, parent_id=0, ancestors='0', dept_name='目标', status='0'))
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=sample_dept)
            
            edit_dept = DeptModel(
                dept_id=2,
                parent_id=0,
                dept_name='测试部门'
            )
            
            with pytest.raises(ResourceConflictException, match='部门名称已存在'):
                await DeptService(mock_repo, mock_db).edit_dept_services(edit_dept)

    @pytest.mark.asyncio
    async def test_edit_dept_self_as_parent(self, mock_db):
        """Test editing department with self as parent."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=DeptDO(dept_id=1, parent_id=0, ancestors='0', dept_name='目标', status='0'))
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            
            edit_dept = DeptModel(
                dept_id=1,
                parent_id=1,  # Self as parent
                dept_name='测试部门'
            )
            
            with pytest.raises(ValidationException, match='上级部门不能是自己'):
                await DeptService(mock_repo, mock_db).edit_dept_services(edit_dept)

    @pytest.mark.asyncio
    async def test_edit_dept_disable_with_normal_children(self, mock_db, sample_dept):
        """Test disabling department with normal children."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=DeptDO(dept_id=1, parent_id=0, ancestors='0', dept_name='目标', status='0'))
            mock_repo.find_by_parent_and_name = AsyncMock(return_value=None)
            mock_repo.count_normal_children = AsyncMock(return_value=1)
            
            edit_dept = DeptModel(
                dept_id=1,
                parent_id=0,
                dept_name='测试部门',
                status='1'  # Disable
            )
            
            with pytest.raises(ValidationException, match='包含未停用的子部门'):
                await DeptService(mock_repo, mock_db).edit_dept_services(edit_dept)


class TestDeptServiceDelete:
    """Test suite for department deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_dept_success(self, mock_db):
        """Test deleting department successfully."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.count_direct_children = AsyncMock(return_value=0)
            mock_repo.count_users = AsyncMock(return_value=0)
            mock_repo.soft_delete = AsyncMock()
            
            delete_obj = DeleteDeptModel(dept_ids='1,2', update_by='admin')
            result = await DeptService(mock_repo, mock_db).delete_dept_services(delete_obj)
            
            assert result.is_success is True
            assert mock_repo.soft_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_dept_empty_ids(self, mock_db):
        """Test deleting department with empty IDs."""
        delete_obj = DeleteDeptModel(dept_ids='', update_by='admin')
        
        with pytest.raises(ValidationException, match='传入部门id为空'):
            await DeptService(MagicMock(), mock_db).delete_dept_services(delete_obj)

    @pytest.mark.asyncio
    async def test_delete_dept_with_children(self, mock_db):
        """Test deleting department with children."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.count_direct_children = AsyncMock(return_value=1)
            
            delete_obj = DeleteDeptModel(dept_ids='1', update_by='admin')
            
            with pytest.raises(ResourceConflictException, match='存在下级部门'):
                await DeptService(mock_repo, mock_db).delete_dept_services(delete_obj)

    @pytest.mark.asyncio
    async def test_delete_dept_with_users(self, mock_db):
        """Test deleting department with users."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.count_direct_children = AsyncMock(return_value=0)
            mock_repo.count_users = AsyncMock(return_value=1)
            
            delete_obj = DeleteDeptModel(dept_ids='1', update_by='admin')
            
            with pytest.raises(ResourceConflictException, match='部门存在用户'):
                await DeptService(mock_repo, mock_db).delete_dept_services(delete_obj)


class TestDeptServiceUtility:
    """Test suite for department utility methods."""

    def test_list_to_tree_single_level(self):
        """Test converting flat list to tree - single level."""
        dept1 = DeptDO(dept_id=1, parent_id=0, dept_name='部门1', ancestors='0', status='0', del_flag='0')
        dept2 = DeptDO(dept_id=2, parent_id=0, dept_name='部门2', ancestors='0', status='0', del_flag='0')
        
        result = DeptService.list_to_tree([dept1, dept2])
        
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['id'] == 2

    def test_list_to_tree_nested(self):
        """Test converting flat list to tree - nested."""
        parent = DeptDO(dept_id=1, parent_id=0, dept_name='父部门', ancestors='0', status='0', del_flag='0')
        child = DeptDO(dept_id=2, parent_id=1, dept_name='子部门', ancestors='0,1', status='0', del_flag='0')
        
        result = DeptService.list_to_tree([parent, child])
        
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert 'children' in result[0]
        assert len(result[0]['children']) == 1
        assert result[0]['children'][0]['id'] == 2

    @pytest.mark.asyncio
    async def test_replace_first_match(self):
        """Test replacing first occurrence in string."""
        result = await DeptService.replace_first('0,1,2', '0,1', '0,3')
        assert result == '0,3,2'

    @pytest.mark.asyncio
    async def test_replace_first_no_match(self):
        """Test replacing when pattern not at start."""
        result = await DeptService.replace_first('0,1,2', '1,2', '3,4')
        assert result == '0,1,2'

    @pytest.mark.asyncio
    async def test_update_parent_dept_status_normal(self, mock_db):
        """Test updating parent department status to normal."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.update_status_normal = AsyncMock()
            
            dept = DeptModel(dept_id=3, ancestors='0,1,2')
            await DeptService(mock_repo, mock_db).update_parent_dept_status_normal(dept)
            
            mock_repo.update_status_normal.assert_called_once_with([1, 2])

    @pytest.mark.asyncio
    async def test_update_dept_children(self, mock_db, sample_child_dept):
        """Test updating department children ancestors."""
        with patch('modules.system.application.services.dept_service.DeptRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_children = AsyncMock(return_value=[sample_child_dept])
            mock_repo.update_children_ancestors = AsyncMock()
            
            await DeptService(mock_repo, mock_db).update_dept_children(1, '0,2', '0,1')
            
            mock_repo.find_children.assert_called_once_with(1)
            mock_repo.update_children_ancestors.assert_called_once()
