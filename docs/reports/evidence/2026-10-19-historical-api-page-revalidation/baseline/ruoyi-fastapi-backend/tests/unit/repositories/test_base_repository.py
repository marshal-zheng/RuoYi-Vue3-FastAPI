"""
BaseRepository 基础仓储测试
测试统一的数据访问抽象层功能
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.enums import DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from module_admin.entity.do.user_do import UserDO


class TestBaseRepositoryBasicOperations:
    """BaseRepository 基础操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session, test_user):
        """测试根据ID获取记录"""
        repo = BaseRepository(db_session, UserDO)
        user = await repo.get_by_id(test_user.user_id)
        assert user is not None
        assert user.user_id == test_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """测试获取不存在的记录"""
        repo = BaseRepository(db_session, UserDO)
        user = await repo.get_by_id(999999)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_find_all(self, db_session):
        """测试查找所有记录"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_find_all_with_filters(self, db_session, test_user):
        """测试带过滤条件查找"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(filters={"user_name": test_user.user_name})
        assert len(users) >= 1
        assert all(u.user_name == test_user.user_name for u in users)
    
    @pytest.mark.asyncio
    async def test_find_one(self, db_session, test_user):
        """测试查找单条记录"""
        repo = BaseRepository(db_session, UserDO)
        user = await repo.find_one(filters={"user_id": test_user.user_id})
        assert user is not None
        assert user.user_id == test_user.user_id
    
    @pytest.mark.asyncio
    async def test_find_one_not_found(self, db_session):
        """测试查找不存在的记录"""
        repo = BaseRepository(db_session, UserDO)
        user = await repo.find_one(filters={"user_id": 999999})
        assert user is None


class TestBaseRepositoryAddOperations:
    """BaseRepository 添加操作测试"""
    
    @pytest.mark.asyncio
    async def test_add(self, db_session):
        """测试添加记录"""
        repo = BaseRepository(db_session, UserDO)
        new_user = UserDO(
            user_name="test_add_user",
            nick_name="Test Add",
            password="test123",
            status="0",
            del_flag="0"
        )
        added_user = await repo.add(new_user)
        assert added_user.user_id is not None
        assert added_user.user_name == "test_add_user"
    
    @pytest.mark.asyncio
    async def test_add_all(self, db_session):
        """测试批量添加记录"""
        repo = BaseRepository(db_session, UserDO)
        users = [
            UserDO(
                user_name=f"test_batch_{i}",
                nick_name=f"Test Batch {i}",
                password="test123",
                status="0",
                del_flag="0"
            )
            for i in range(3)
        ]
        added_users = await repo.add_all(users)
        assert len(added_users) == 3
        assert all(u.user_id is not None for u in added_users)


class TestBaseRepositoryUpdateOperations:
    """BaseRepository 更新操作测试"""
    
    @pytest.mark.asyncio
    async def test_update(self, db_session, test_user):
        """测试更新记录"""
        repo = BaseRepository(db_session, UserDO)
        test_user.remark = "Updated remark"
        updated_user = await repo.update(test_user)
        assert updated_user.remark == "Updated remark"


class TestBaseRepositoryDeleteOperations:
    """BaseRepository 删除操作测试"""
    
    @pytest.mark.asyncio
    async def test_delete_by_id(self, db_session):
        """测试根据ID删除记录"""
        repo = BaseRepository(db_session, UserDO)
        # 创建测试用户
        new_user = UserDO(
            user_name="test_delete",
            nick_name="Test Delete",
            password="test123",
            status="0",
            del_flag="0"
        )
        added_user = await repo.add(new_user)
        user_id = added_user.user_id
        
        # 删除
        deleted = await repo.delete_by_id(user_id)
        assert deleted is True
        
        # 验证已删除
        user = await repo.get_by_id(user_id)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_delete_by_id_not_found(self, db_session):
        """测试删除不存在的记录"""
        repo = BaseRepository(db_session, UserDO)
        deleted = await repo.delete_by_id(999999)
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_delete_by_ids(self, db_session):
        """测试批量删除记录"""
        repo = BaseRepository(db_session, UserDO)
        # 创建测试用户
        users = [
            UserDO(
                user_name=f"test_batch_delete_{i}",
                nick_name=f"Test Batch Delete {i}",
                password="test123",
                status="0",
                del_flag="0"
            )
            for i in range(3)
        ]
        added_users = await repo.add_all(users)
        user_ids = [u.user_id for u in added_users]
        
        # 批量删除
        deleted_count = await repo.delete_by_ids(user_ids)
        assert deleted_count == 3
    
    @pytest.mark.asyncio
    async def test_delete_by_ids_empty_list(self, db_session):
        """测试空列表批量删除"""
        repo = BaseRepository(db_session, UserDO)
        deleted_count = await repo.delete_by_ids([])
        assert deleted_count == 0


class TestBaseRepositoryCountOperations:
    """BaseRepository 统计操作测试"""
    
    @pytest.mark.asyncio
    async def test_count(self, db_session):
        """测试统计记录数"""
        repo = BaseRepository(db_session, UserDO)
        count = await repo.count()
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, db_session, test_user):
        """测试带过滤条件统计"""
        repo = BaseRepository(db_session, UserDO)
        count = await repo.count(filters={"user_name": test_user.user_name})
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_exists_true(self, db_session, test_user):
        """测试存在判断（存在）"""
        repo = BaseRepository(db_session, UserDO)
        exists = await repo.exists(filters={"user_id": test_user.user_id})
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, db_session):
        """测试存在判断（不存在）"""
        repo = BaseRepository(db_session, UserDO)
        exists = await repo.exists(filters={"user_id": 999999})
        assert exists is False


class TestBaseRepositoryPagination:
    """BaseRepository 分页测试"""
    
    @pytest.mark.asyncio
    async def test_paginate(self, db_session):
        """测试分页查询"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(page=1, page_size=10)
        assert isinstance(users, list)
        assert isinstance(total, int)
        assert len(users) <= 10
        assert total >= 0
    
    @pytest.mark.asyncio
    async def test_paginate_with_filters(self, db_session):
        """测试带过滤条件分页"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(
            page=1,
            page_size=10,
            filters={"status": "0"}
        )
        assert isinstance(users, list)
        assert all(u.status == "0" for u in users)
    
    @pytest.mark.asyncio
    async def test_paginate_second_page(self, db_session):
        """测试第二页"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(page=2, page_size=5)
        assert isinstance(users, list)
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_paginate_with_order(self, db_session):
        """测试带排序分页"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(
            page=1,
            page_size=10,
            order_by=[UserDO.user_id.desc()]
        )
        if len(users) > 1:
            assert users[0].user_id >= users[1].user_id


class TestBaseRepositoryOrdering:
    """BaseRepository 排序测试"""
    
    @pytest.mark.asyncio
    async def test_find_all_with_order_asc(self, db_session):
        """测试升序排序"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(
            order_by=[UserDO.user_id.asc()],
            limit=10
        )
        if len(users) > 1:
            assert users[0].user_id <= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_find_all_with_order_desc(self, db_session):
        """测试降序排序"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(
            order_by=[UserDO.user_id.desc()],
            limit=10
        )
        if len(users) > 1:
            assert users[0].user_id >= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_find_all_with_multiple_order(self, db_session):
        """测试多字段排序"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(
            order_by=[UserDO.status.asc(), UserDO.user_id.desc()],
            limit=10
        )
        assert isinstance(users, list)


class TestBaseRepositoryLimitOffset:
    """BaseRepository 限制和偏移测试"""
    
    @pytest.mark.asyncio
    async def test_find_all_with_limit(self, db_session):
        """测试限制数量"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(limit=5)
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_find_all_with_offset(self, db_session):
        """测试偏移量"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(offset=1, limit=5)
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_find_all_with_zero_limit(self, db_session):
        """测试零限制"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(limit=0)
        assert users == []
    
    @pytest.mark.asyncio
    async def test_find_all_with_large_offset(self, db_session):
        """测试大偏移量"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(offset=10000, limit=10)
        assert isinstance(users, list)


class TestBaseRepositoryEdgeCases:
    """BaseRepository 边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_find_all_empty_filters(self, db_session):
        """测试空过滤条件"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(filters={})
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_find_all_no_results(self, db_session):
        """测试无结果查询"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(filters={"user_id": 999999})
        assert users == []
    
    @pytest.mark.asyncio
    async def test_count_no_results(self, db_session):
        """测试无结果统计"""
        repo = BaseRepository(db_session, UserDO)
        count = await repo.count(filters={"user_id": 999999})
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_paginate_empty_page(self, db_session):
        """测试空页"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(page=1000, page_size=10)
        assert users == []
        assert total >= 0


class TestBaseRepositorySoftDeleteFiltering:
    """Soft delete filter coverage"""

    @pytest.mark.asyncio
    async def test_soft_delete_auto_filter_blocks_deleted_records(self, db_session: AsyncSession):
        repo = BaseRepository(db_session, UserDO)
        deleted_user = UserDO(
            user_name="deleted_user_auto_filter",
            nick_name="Deleted Auto",
            password="hidden",
            status="0",
            del_flag=DelFlagEnum.DELETED.value,
        )
        await repo.add(deleted_user)

        assert await repo.find_one(filters={"user_name": deleted_user.user_name}) is None
        assert await repo.count(filters={"user_name": deleted_user.user_name}) == 0

        included = await repo.find_one(
            filters={"user_name": deleted_user.user_name},
            include_deleted=True,
        )
        assert included is not None
        assert included.del_flag == DelFlagEnum.DELETED.value

        included_count = await repo.count(
            filters={"user_name": deleted_user.user_name},
            include_deleted=True,
        )
        assert included_count == 1


class TestBaseRepositoryMultipleFilters:
    """BaseRepository 多过滤条件测试"""
    
    @pytest.mark.asyncio
    async def test_find_all_multiple_filters(self, db_session):
        """测试多个过滤条件"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(filters={
            "status": "0",
            "del_flag": "0"
        })
        assert all(u.status == "0" and u.del_flag == "0" for u in users)
    
    @pytest.mark.asyncio
    async def test_count_multiple_filters(self, db_session):
        """测试多过滤条件统计"""
        repo = BaseRepository(db_session, UserDO)
        count = await repo.count(filters={
            "status": "0",
            "del_flag": "0"
        })
        assert isinstance(count, int)
    
    @pytest.mark.asyncio
    async def test_exists_multiple_filters(self, db_session, test_user):
        """测试多过滤条件存在判断"""
        repo = BaseRepository(db_session, UserDO)
        exists = await repo.exists(filters={
            "user_id": test_user.user_id,
            "user_name": test_user.user_name
        })
        assert exists is True


class TestBaseRepositoryComplexQueries:
    """BaseRepository 复杂查询测试"""
    
    @pytest.mark.asyncio
    async def test_filter_order_limit(self, db_session):
        """测试过滤、排序、限制组合"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(
            filters={"status": "0"},
            order_by=[UserDO.user_id.desc()],
            limit=5
        )
        assert len(users) <= 5
        assert all(u.status == "0" for u in users)
    
    @pytest.mark.asyncio
    async def test_filter_order_offset_limit(self, db_session):
        """测试过滤、排序、偏移、限制组合"""
        repo = BaseRepository(db_session, UserDO)
        users = await repo.find_all(
            filters={"status": "0"},
            order_by=[UserDO.user_id.desc()],
            offset=1,
            limit=5
        )
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_paginate_with_all_options(self, db_session):
        """测试分页所有选项"""
        repo = BaseRepository(db_session, UserDO)
        users, total = await repo.paginate(
            page=1,
            page_size=10,
            filters={"status": "0"},
            order_by=[UserDO.user_id.desc()]
        )
        assert len(users) <= 10
        assert isinstance(total, int)
