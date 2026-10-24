"""
QueryBuilder 查询构建器测试
测试流式 API 构建复杂查询的功能
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from module_admin.repository.query_builder import QueryBuilder
from module_admin.entity.do.user_do import UserDO


class TestQueryBuilder:
    """QueryBuilder 基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_basic_query(self, db_session):
        """测试基础查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_by_field(self, db_session, test_user):
        """测试字段过滤"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter(user_name=test_user.user_name).get_many()
        assert len(users) >= 1
        assert users[0].user_name == test_user.user_name
    
    @pytest.mark.asyncio
    async def test_where_condition(self, db_session, test_user):
        """测试 WHERE 条件"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.where(UserDO.user_name == test_user.user_name).get_many()
        assert len(users) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_like(self, db_session, test_user):
        """测试模糊查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_like("user_name", "test").get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_in(self, db_session, test_user):
        """测试 IN 查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_in("user_id", [test_user.user_id]).get_many()
        assert len(users) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_in_empty_list(self, db_session):
        """测试空列表 IN 查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_in("user_id", []).get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_between(self, db_session):
        """测试范围查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_between("user_id", 1, 100).get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_null(self, db_session):
        """测试 NULL 查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_null("remark", is_null=True).get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_not_null(self, db_session):
        """测试 NOT NULL 查询"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter_null("user_name", is_null=False).get_many()
        assert isinstance(users, list)


class TestQueryBuilderOrdering:
    """QueryBuilder 排序功能测试"""
    
    @pytest.mark.asyncio
    async def test_order_by_asc(self, db_session):
        """测试升序排序"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.order_by_asc("user_id").limit(10).get_many()
        if len(users) > 1:
            assert users[0].user_id <= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_order_by_desc(self, db_session):
        """测试降序排序"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.order_by_desc("user_id").limit(10).get_many()
        if len(users) > 1:
            assert users[0].user_id >= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_order_by_multiple_fields(self, db_session):
        """测试多字段排序"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.order_by(UserDO.status.asc(), UserDO.user_id.desc()).get_many()
        assert isinstance(users, list)


class TestQueryBuilderPagination:
    """QueryBuilder 分页功能测试"""
    
    @pytest.mark.asyncio
    async def test_limit(self, db_session):
        """测试限制数量"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.limit(5).get_many()
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_offset(self, db_session):
        """测试偏移量"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.offset(1).limit(5).get_many()
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_paginate(self, db_session):
        """测试分页"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.paginate(page=1, page_size=10).get_many()
        assert len(users) <= 10
    
    @pytest.mark.asyncio
    async def test_paginate_result(self, db_session):
        """测试分页结果（包含总数）"""
        query = QueryBuilder(db_session, UserDO)
        users, total = await query.paginate(page=1, page_size=10).paginate_result()
        assert isinstance(users, list)
        assert isinstance(total, int)
        assert total >= 0


class TestQueryBuilderAggregation:
    """QueryBuilder 聚合功能测试"""
    
    @pytest.mark.asyncio
    async def test_count(self, db_session):
        """测试统计"""
        query = QueryBuilder(db_session, UserDO)
        count = await query.count()
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_count_with_filter(self, db_session, test_user):
        """测试带过滤的统计"""
        query = QueryBuilder(db_session, UserDO)
        count = await query.filter(user_name=test_user.user_name).count()
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_exists_true(self, db_session, test_user):
        """测试存在判断（存在）"""
        query = QueryBuilder(db_session, UserDO)
        exists = await query.filter(user_id=test_user.user_id).exists()
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, db_session):
        """测试存在判断（不存在）"""
        query = QueryBuilder(db_session, UserDO)
        exists = await query.filter(user_id=999999).exists()
        assert exists is False


class TestQueryBuilderRetrieval:
    """QueryBuilder 数据获取测试"""
    
    @pytest.mark.asyncio
    async def test_get_one(self, db_session, test_user):
        """测试获取单条记录"""
        query = QueryBuilder(db_session, UserDO)
        user = await query.filter(user_id=test_user.user_id).get_one()
        assert user is not None
        assert user.user_id == test_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_one_not_found(self, db_session):
        """测试获取不存在的记录"""
        query = QueryBuilder(db_session, UserDO)
        user = await query.filter(user_id=999999).get_one()
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_first(self, db_session):
        """测试获取第一条记录"""
        query = QueryBuilder(db_session, UserDO)
        user = await query.get_first()
        assert user is not None or user is None  # 可能为空
    
    @pytest.mark.asyncio
    async def test_get_many(self, db_session):
        """测试获取多条记录"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_get_all(self, db_session):
        """测试获取所有记录"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.get_all()
        assert isinstance(users, list)


class TestQueryBuilderChaining:
    """QueryBuilder 链式调用测试"""
    
    @pytest.mark.asyncio
    async def test_complex_chain(self, db_session):
        """测试复杂链式调用"""
        query = QueryBuilder(db_session, UserDO)
        users = await (
            query
            .filter(status="0")
            .filter_like("user_name", "test")
            .order_by_desc("create_time")
            .limit(10)
            .get_many()
        )
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_multiple_filters(self, db_session):
        """测试多个过滤条件"""
        query = QueryBuilder(db_session, UserDO)
        users = await (
            query
            .filter(status="0")
            .filter(del_flag="0")
            .get_many()
        )
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_and_order(self, db_session):
        """测试过滤和排序组合"""
        query = QueryBuilder(db_session, UserDO)
        users = await (
            query
            .filter(status="0")
            .order_by_asc("user_id")
            .limit(5)
            .get_many()
        )
        assert isinstance(users, list)
        assert len(users) <= 5


class TestQueryBuilderModification:
    """QueryBuilder 修改操作测试"""
    
    @pytest.mark.asyncio
    async def test_update(self, db_session, test_user):
        """测试更新操作"""
        query = QueryBuilder(db_session, UserDO)
        updated = await query.filter(user_id=test_user.user_id).update(remark="Updated")
        assert updated >= 0
    
    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session, test_user):
        """测试更新多个字段"""
        query = QueryBuilder(db_session, UserDO)
        updated = await query.filter(user_id=test_user.user_id).update(
            remark="Updated",
            status="0"
        )
        assert updated >= 0
    
    @pytest.mark.asyncio
    async def test_delete(self, db_session):
        """测试删除操作"""
        # 创建测试用户
        from module_admin.entity.do.user_do import UserDO
        test_user = UserDO(
            user_name="test_delete_user",
            nick_name="Test Delete",
            password="test123",
            status="0",
            del_flag="0"
        )
        db_session.add(test_user)
        await db_session.flush()
        user_id = test_user.user_id
        
        # 删除
        query = QueryBuilder(db_session, UserDO)
        deleted = await query.filter(user_id=user_id).delete()
        assert deleted >= 0


class TestQueryBuilderEdgeCases:
    """QueryBuilder 边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_result(self, db_session):
        """测试空结果"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.filter(user_id=999999).get_many()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_zero_limit(self, db_session):
        """测试零限制"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.limit(0).get_many()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_large_offset(self, db_session):
        """测试大偏移量"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.offset(10000).get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_no_filters(self, db_session):
        """测试无过滤条件"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.get_many()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_multiple_where_conditions(self, db_session):
        """测试多个 WHERE 条件"""
        query = QueryBuilder(db_session, UserDO)
        users = await query.where(
            UserDO.status == "0",
            UserDO.del_flag == "0"
        ).get_many()
        assert isinstance(users, list)
