"""
Unit tests for notice service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from module_admin.service.notice_service import NoticeService
from module_admin.entity.do.notice_do import NoticeDO
from module_admin.entity.vo.notice_vo import NoticeModel, NoticePageQueryModel, DeleteNoticeModel
from config.constant import CommonConstant
from exceptions.exception import ServiceException


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_notice():
    """Create sample notice for testing."""
    return NoticeDO(
        notice_id=1,
        notice_title='系统维护通知',
        notice_type='1',
        notice_content='系统将于今晚进行维护',
        status='0',
        create_by='admin',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


@pytest.fixture
def sample_announcement():
    """Create sample announcement."""
    return NoticeDO(
        notice_id=2,
        notice_title='重要公告',
        notice_type='2',
        notice_content='公告内容',
        status='0',
        create_by='admin',
        create_time=datetime.now(),
    )


class TestNoticeServiceQuery:
    """Test suite for notice query operations."""

    @pytest.mark.asyncio
    async def test_get_notice_list_with_pagination(self, mock_db, sample_notice):
        """Test getting notice list with pagination."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_notice]
            mock_result.total = 1
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = NoticePageQueryModel(page_num=1, page_size=10)
            result = await NoticeService.get_notice_list_services(mock_db, query, is_page=True)
            
            assert result.total == 1
            assert len(result.rows) == 1

    @pytest.mark.asyncio
    async def test_get_notice_list_without_pagination(self, mock_db, sample_notice):
        """Test getting notice list without pagination."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_notice]
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = NoticePageQueryModel(page_num=1, page_size=10)
            result = await NoticeService.get_notice_list_services(mock_db, query, is_page=False)
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_notice_list_with_filters(self, mock_db, sample_notice):
        """Test getting notice list with filters."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_notice]
            mock_result.total = 1
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = NoticePageQueryModel(
                notice_title='维护',
                notice_type='1',
                create_by='admin',
                page_num=1,
                page_size=10
            )
            result = await NoticeService.get_notice_list_services(mock_db, query, is_page=True)
            
            assert result.total == 1
            mock_repo.paginate_with_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notice_list_with_date_range(self, mock_db, sample_notice):
        """Test getting notice list with date range."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = [sample_notice]
            mock_result.total = 1
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = NoticePageQueryModel(
                begin_time='2024-01-01',
                end_time='2024-12-31',
                page_num=1,
                page_size=10
            )
            result = await NoticeService.get_notice_list_services(mock_db, query, is_page=True)
            
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_notice_list_empty(self, mock_db):
        """Test getting empty notice list."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_result = MagicMock()
            mock_result.rows = []
            mock_result.total = 0
            mock_repo.paginate_with_filters = AsyncMock(return_value=mock_result)
            
            query = NoticePageQueryModel(page_num=1, page_size=10)
            result = await NoticeService.get_notice_list_services(mock_db, query, is_page=True)
            
            assert result.total == 0
            assert len(result.rows) == 0

    @pytest.mark.asyncio
    async def test_notice_detail_success(self, mock_db, sample_notice):
        """Test getting notice detail successfully."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=sample_notice)
            
            result = await NoticeService.notice_detail_services(mock_db, 1)
            
            assert result.notice_id == 1
            assert result.notice_title == '系统维护通知'
            assert result.notice_type == '1'

    @pytest.mark.asyncio
    async def test_notice_detail_not_found(self, mock_db):
        """Test getting non-existent notice detail."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_id = AsyncMock(return_value=None)
            
            result = await NoticeService.notice_detail_services(mock_db, 999)
            
            assert result.notice_id is None


class TestNoticeServiceValidation:
    """Test suite for notice validation operations."""

    @pytest.mark.asyncio
    async def test_check_notice_unique_success(self, mock_db):
        """Test checking notice uniqueness - unique."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            
            notice = NoticeModel(
                notice_title='新通知',
                notice_type='1',
                notice_content='新内容'
            )
            result = await NoticeService.check_notice_unique_services(mock_db, notice)
            
            assert result == CommonConstant.UNIQUE

    @pytest.mark.asyncio
    async def test_check_notice_not_unique(self, mock_db, sample_notice):
        """Test checking notice uniqueness - not unique."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=sample_notice)
            
            notice = NoticeModel(
                notice_id=2,
                notice_title='系统维护通知',
                notice_type='1',
                notice_content='系统将于今晚进行维护'
            )
            result = await NoticeService.check_notice_unique_services(mock_db, notice)
            
            assert result == CommonConstant.NOT_UNIQUE

    @pytest.mark.asyncio
    async def test_check_notice_unique_same_notice(self, mock_db, sample_notice):
        """Test checking notice uniqueness - same notice."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=sample_notice)
            
            notice = NoticeModel(
                notice_id=1,
                notice_title='系统维护通知',
                notice_type='1',
                notice_content='系统将于今晚进行维护'
            )
            result = await NoticeService.check_notice_unique_services(mock_db, notice)
            
            assert result == CommonConstant.UNIQUE


class TestNoticeServiceCreate:
    """Test suite for notice creation operations."""

    @pytest.mark.asyncio
    async def test_add_notice_success(self, mock_db):
        """Test adding new notice successfully."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            new_notice = NoticeModel(
                notice_title='新通知',
                notice_type='1',
                notice_content='通知内容',
                status='0',
                create_by='admin'
            )
            
            result = await NoticeService.add_notice_services(mock_db, new_notice)
            
            assert result.is_success is True
            assert result.message == '新增成功'
            mock_repo.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_notice_duplicate(self, mock_db, sample_notice):
        """Test adding duplicate notice."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=sample_notice)
            
            new_notice = NoticeModel(
                notice_title='系统维护通知',
                notice_type='1',
                notice_content='系统将于今晚进行维护',
                status='0'
            )
            
            with pytest.raises(ServiceException, match='通知公告已存在'):
                await NoticeService.add_notice_services(mock_db, new_notice)

    @pytest.mark.asyncio
    async def test_add_announcement_success(self, mock_db):
        """Test adding new announcement successfully."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            new_announcement = NoticeModel(
                notice_title='重要公告',
                notice_type='2',  # Announcement type
                notice_content='公告内容',
                status='0',
                create_by='admin'
            )
            
            result = await NoticeService.add_notice_services(mock_db, new_announcement)
            
            assert result.is_success is True
            mock_repo.add.assert_called_once()


class TestNoticeServiceUpdate:
    """Test suite for notice update operations."""

    @pytest.mark.asyncio
    async def test_edit_notice_success(self, mock_db, sample_notice):
        """Test editing notice successfully."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=sample_notice)
            mock_repo.update = AsyncMock()
            
            with patch.object(NoticeService, 'notice_detail_services', new=AsyncMock(return_value=NoticeModel(
                notice_id=1,
                notice_title='系统维护通知',
                notice_type='1',
                notice_content='原内容',
                status='0'
            ))):
                edit_notice = NoticeModel(
                    notice_id=1,
                    notice_title='更新通知',
                    notice_type='1',
                    notice_content='更新内容',
                    status='0',
                    update_by='admin'
                )
                
                result = await NoticeService.edit_notice_services(mock_db, edit_notice)
                
                assert result.is_success is True
                assert result.message == '更新成功'
                mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_notice_not_found(self, mock_db):
        """Test editing non-existent notice."""
        with patch.object(NoticeService, 'notice_detail_services', new=AsyncMock(return_value=NoticeModel())):
            edit_notice = NoticeModel(
                notice_id=999,
                notice_title='不存在',
                notice_type='1',
                notice_content='内容'
            )
            
            with pytest.raises(ServiceException, match='通知公告不存在'):
                await NoticeService.edit_notice_services(mock_db, edit_notice)

    @pytest.mark.asyncio
    async def test_edit_notice_duplicate(self, mock_db, sample_notice):
        """Test editing notice with duplicate content."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=sample_notice)
            
            with patch.object(NoticeService, 'notice_detail_services', new=AsyncMock(return_value=NoticeModel(
                notice_id=2,
                notice_title='其他通知',
                notice_type='1',
                notice_content='其他内容',
                status='0'
            ))):
                edit_notice = NoticeModel(
                    notice_id=2,
                    notice_title='系统维护通知',
                    notice_type='1',
                    notice_content='系统将于今晚进行维护'
                )
                
                with pytest.raises(ServiceException, match='通知公告已存在'):
                    await NoticeService.edit_notice_services(mock_db, edit_notice)

    @pytest.mark.asyncio
    async def test_edit_notice_status(self, mock_db, sample_notice):
        """Test editing notice status."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.find_by_id = AsyncMock(return_value=sample_notice)
            mock_repo.update = AsyncMock()
            
            with patch.object(NoticeService, 'notice_detail_services', new=AsyncMock(return_value=NoticeModel(
                notice_id=1,
                notice_title='系统维护通知',
                notice_type='1',
                notice_content='内容',
                status='0'
            ))):
                edit_notice = NoticeModel(
                    notice_id=1,
                    notice_title='系统维护通知',
                    notice_type='1',
                    notice_content='内容',
                    status='1'  # Close notice
                )
                
                result = await NoticeService.edit_notice_services(mock_db, edit_notice)
                
                assert result.is_success is True


class TestNoticeServiceDelete:
    """Test suite for notice deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_notice_success(self, mock_db):
        """Test deleting notice successfully."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.delete_by_id = AsyncMock()
            
            delete_obj = DeleteNoticeModel(notice_ids='1,2,3')
            result = await NoticeService.delete_notice_services(mock_db, delete_obj)
            
            assert result.is_success is True
            assert result.message == '删除成功'
            assert mock_repo.delete_by_id.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_single_notice(self, mock_db):
        """Test deleting single notice."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.delete_by_id = AsyncMock()
            
            delete_obj = DeleteNoticeModel(notice_ids='1')
            result = await NoticeService.delete_notice_services(mock_db, delete_obj)
            
            assert result.is_success is True
            mock_repo.delete_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_notice_empty_ids(self, mock_db):
        """Test deleting notice with empty IDs."""
        delete_obj = DeleteNoticeModel(notice_ids='')
        
        with pytest.raises(ServiceException, match='传入通知公告id为空'):
            await NoticeService.delete_notice_services(mock_db, delete_obj)

    @pytest.mark.asyncio
    async def test_delete_notice_none_ids(self, mock_db):
        """Test deleting notice with None IDs."""
        delete_obj = DeleteNoticeModel(notice_ids=None)
        
        with pytest.raises(ServiceException, match='传入通知公告id为空'):
            await NoticeService.delete_notice_services(mock_db, delete_obj)

    @pytest.mark.asyncio
    async def test_batch_delete_notices(self, mock_db):
        """Test batch deleting multiple notices."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.delete_by_id = AsyncMock()
            
            delete_obj = DeleteNoticeModel(notice_ids='1,2,3,4,5')
            result = await NoticeService.delete_notice_services(mock_db, delete_obj)
            
            assert result.is_success is True
            assert mock_repo.delete_by_id.call_count == 5


class TestNoticeServiceEdgeCases:
    """Test suite for notice service edge cases."""

    @pytest.mark.asyncio
    async def test_notice_with_long_content(self, mock_db):
        """Test adding notice with long content."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            long_content = 'A' * 10000  # Very long content
            new_notice = NoticeModel(
                notice_title='长内容通知',
                notice_type='1',
                notice_content=long_content,
                status='0'
            )
            
            result = await NoticeService.add_notice_services(mock_db, new_notice)
            
            assert result.is_success is True

    @pytest.mark.asyncio
    async def test_notice_with_special_characters(self, mock_db):
        """Test adding notice with special characters."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            new_notice = NoticeModel(
                notice_title='特殊字符<>&"\'',
                notice_type='1',
                notice_content='内容包含特殊字符: <script>alert("XSS")</script>',
                status='0'
            )
            
            result = await NoticeService.add_notice_services(mock_db, new_notice)
            
            assert result.is_success is True

    @pytest.mark.asyncio
    async def test_notice_with_html_content(self, mock_db):
        """Test adding notice with HTML content."""
        with patch('module_admin.service.notice_service.NoticeRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.find_by_content = AsyncMock(return_value=None)
            mock_repo.add = AsyncMock()
            
            html_content = '<p>这是<strong>HTML</strong>内容</p>'
            new_notice = NoticeModel(
                notice_title='HTML通知',
                notice_type='1',
                notice_content=html_content,
                status='0'
            )
            
            result = await NoticeService.add_notice_services(mock_db, new_notice)
            
            assert result.is_success is True
