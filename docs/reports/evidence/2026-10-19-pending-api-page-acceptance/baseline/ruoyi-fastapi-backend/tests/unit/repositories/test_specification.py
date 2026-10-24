"""
Specification 规范模式测试
测试灵活的查询条件组合能力
"""
import pytest
from sqlalchemy import select
from module_admin.repository.specification import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    EqualsSpecification,
    NotEqualsSpecification,
    LikeSpecification,
    InSpecification,
    NotInSpecification,
    BetweenSpecification,
    GreaterThanSpecification,
    GreaterThanOrEqualSpecification,
    LessThanSpecification,
    LessThanOrEqualSpecification,
    IsNullSpecification,
    IsNotNullSpecification,
    OrderBySpecification,
    LimitSpecification,
    OffsetSpecification,
    equals,
    not_equals,
    like,
    in_,
    not_in,
    between,
    gt,
    gte,
    lt,
    lte,
    is_null,
    is_not_null,
    order_by,
    limit,
    offset
)
from module_admin.entity.do.user_do import UserDO


class TestBasicSpecifications:
    """基础规范测试"""
    
    @pytest.mark.asyncio
    async def test_equals_specification(self, db_session, test_user):
        """测试等于规范"""
        spec = equals(UserDO.user_name, test_user.user_name)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) >= 1
        assert all(u.user_name == test_user.user_name for u in users)
    
    @pytest.mark.asyncio
    async def test_not_equals_specification(self, db_session, test_user):
        """测试不等于规范"""
        spec = not_equals(UserDO.user_name, test_user.user_name)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_name != test_user.user_name for u in users)
    
    @pytest.mark.asyncio
    async def test_like_specification(self, db_session):
        """测试模糊匹配规范"""
        spec = like(UserDO.user_name, "test")
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_in_specification(self, db_session, test_user):
        """测试 IN 规范"""
        spec = in_(UserDO.user_id, [test_user.user_id])
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) >= 1
    
    @pytest.mark.asyncio
    async def test_not_in_specification(self, db_session, test_user):
        """测试 NOT IN 规范"""
        spec = not_in(UserDO.user_id, [test_user.user_id])
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_id != test_user.user_id for u in users)
    
    @pytest.mark.asyncio
    async def test_between_specification(self, db_session):
        """测试范围规范"""
        spec = between(UserDO.user_id, 1, 100)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)


class TestComparisonSpecifications:
    """比较规范测试"""
    
    @pytest.mark.asyncio
    async def test_greater_than_specification(self, db_session):
        """测试大于规范"""
        spec = gt(UserDO.user_id, 0)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_id > 0 for u in users)
    
    @pytest.mark.asyncio
    async def test_greater_than_or_equal_specification(self, db_session):
        """测试大于等于规范"""
        spec = gte(UserDO.user_id, 1)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_id >= 1 for u in users)
    
    @pytest.mark.asyncio
    async def test_less_than_specification(self, db_session):
        """测试小于规范"""
        spec = lt(UserDO.user_id, 1000)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_id < 1000 for u in users)
    
    @pytest.mark.asyncio
    async def test_less_than_or_equal_specification(self, db_session):
        """测试小于等于规范"""
        spec = lte(UserDO.user_id, 1000)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_id <= 1000 for u in users)


class TestNullSpecifications:
    """NULL 规范测试"""
    
    @pytest.mark.asyncio
    async def test_is_null_specification(self, db_session):
        """测试为空规范"""
        spec = is_null(UserDO.remark)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.remark is None for u in users)
    
    @pytest.mark.asyncio
    async def test_is_not_null_specification(self, db_session):
        """测试不为空规范"""
        spec = is_not_null(UserDO.user_name)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.user_name is not None for u in users)


class TestCompositeSpecifications:
    """组合规范测试"""
    
    @pytest.mark.asyncio
    async def test_and_specification(self, db_session):
        """测试 AND 组合"""
        spec = equals(UserDO.status, "0") & equals(UserDO.del_flag, "0")
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.status == "0" and u.del_flag == "0" for u in users)
    
    @pytest.mark.asyncio
    async def test_or_specification(self, db_session):
        """测试 OR 组合"""
        spec = equals(UserDO.status, "0") | equals(UserDO.status, "1")
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.status in ["0", "1"] for u in users)
    
    @pytest.mark.asyncio
    async def test_not_specification(self, db_session):
        """测试 NOT 规范"""
        spec = ~equals(UserDO.status, "1")
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(u.status != "1" for u in users)
    
    @pytest.mark.asyncio
    async def test_complex_combination(self, db_session):
        """测试复杂组合"""
        spec = (
            (equals(UserDO.status, "0") | equals(UserDO.status, "1")) &
            equals(UserDO.del_flag, "0")
        )
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert all(
            u.status in ["0", "1"] and u.del_flag == "0"
            for u in users
        )
    
    @pytest.mark.asyncio
    async def test_multiple_and_conditions(self, db_session):
        """测试多个 AND 条件"""
        spec = AndSpecification(
            equals(UserDO.status, "0"),
            equals(UserDO.del_flag, "0"),
            gt(UserDO.user_id, 0)
        )
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_multiple_or_conditions(self, db_session):
        """测试多个 OR 条件"""
        spec = OrSpecification(
            equals(UserDO.status, "0"),
            equals(UserDO.status, "1"),
            equals(UserDO.status, "2")
        )
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)


class TestOrderingSpecifications:
    """排序规范测试"""
    
    @pytest.mark.asyncio
    async def test_order_by_specification(self, db_session):
        """测试排序规范"""
        spec = order_by(UserDO.user_id.asc())
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        if len(users) > 1:
            assert users[0].user_id <= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_order_by_desc(self, db_session):
        """测试降序排序"""
        spec = order_by(UserDO.user_id.desc())
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        if len(users) > 1:
            assert users[0].user_id >= users[1].user_id
    
    @pytest.mark.asyncio
    async def test_multiple_order_by(self, db_session):
        """测试多字段排序"""
        spec = order_by(UserDO.status.asc(), UserDO.user_id.desc())
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)


class TestPaginationSpecifications:
    """分页规范测试"""
    
    @pytest.mark.asyncio
    async def test_limit_specification(self, db_session):
        """测试限制数量规范"""
        spec = limit(5)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) <= 5
    
    @pytest.mark.asyncio
    async def test_offset_specification(self, db_session):
        """测试偏移规范"""
        spec = offset(1)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_limit_and_offset(self, db_session):
        """测试限制和偏移组合"""
        # 注意：需要按顺序应用
        stmt = select(UserDO)
        stmt = offset(1).apply(stmt)
        stmt = limit(5).apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) <= 5


class TestSpecificationEdgeCases:
    """规范边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_in_list(self, db_session):
        """测试空 IN 列表"""
        spec = in_(UserDO.user_id, [])
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_single_item_in_list(self, db_session, test_user):
        """测试单项 IN 列表"""
        spec = in_(UserDO.user_id, [test_user.user_id])
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) >= 1
    
    @pytest.mark.asyncio
    async def test_zero_limit(self, db_session):
        """测试零限制"""
        spec = limit(0)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_large_offset(self, db_session):
        """测试大偏移量"""
        spec = offset(10000)
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)


class TestSpecificationConditions:
    """规范条件测试"""
    
    def test_to_condition_equals(self):
        """测试等于条件"""
        spec = equals(UserDO.user_name, "test")
        condition = spec.to_condition()
        assert condition is not None
    
    def test_to_condition_and(self):
        """测试 AND 条件"""
        spec = equals(UserDO.status, "0") & equals(UserDO.del_flag, "0")
        condition = spec.to_condition()
        assert condition is not None
    
    def test_to_condition_or(self):
        """测试 OR 条件"""
        spec = equals(UserDO.status, "0") | equals(UserDO.status, "1")
        condition = spec.to_condition()
        assert condition is not None
    
    def test_to_condition_not(self):
        """测试 NOT 条件"""
        spec = ~equals(UserDO.status, "1")
        condition = spec.to_condition()
        assert condition is not None


class TestSpecificationOperators:
    """规范操作符测试"""
    
    def test_and_operator(self):
        """测试 & 操作符"""
        spec1 = equals(UserDO.status, "0")
        spec2 = equals(UserDO.del_flag, "0")
        combined = spec1 & spec2
        assert isinstance(combined, AndSpecification)
    
    def test_or_operator(self):
        """测试 | 操作符"""
        spec1 = equals(UserDO.status, "0")
        spec2 = equals(UserDO.status, "1")
        combined = spec1 | spec2
        assert isinstance(combined, OrSpecification)
    
    def test_not_operator(self):
        """测试 ~ 操作符"""
        spec = equals(UserDO.status, "1")
        inverted = ~spec
        assert isinstance(inverted, NotSpecification)
    
    def test_chained_operators(self):
        """测试链式操作符"""
        spec = (
            equals(UserDO.status, "0") &
            equals(UserDO.del_flag, "0") &
            gt(UserDO.user_id, 0)
        )
        assert isinstance(spec, AndSpecification)


class TestSpecificationIntegration:
    """规范集成测试"""
    
    @pytest.mark.asyncio
    async def test_filter_and_order(self, db_session):
        """测试过滤和排序组合"""
        filter_spec = equals(UserDO.status, "0")
        order_spec = order_by(UserDO.user_id.desc())
        
        stmt = select(UserDO)
        stmt = filter_spec.apply(stmt)
        stmt = order_spec.apply(stmt)
        
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_filter_order_and_paginate(self, db_session):
        """测试过滤、排序和分页组合"""
        filter_spec = equals(UserDO.status, "0")
        order_spec = order_by(UserDO.user_id.desc())
        limit_spec = limit(10)
        
        stmt = select(UserDO)
        stmt = filter_spec.apply(stmt)
        stmt = order_spec.apply(stmt)
        stmt = limit_spec.apply(stmt)
        
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) <= 10
    
    @pytest.mark.asyncio
    async def test_complex_business_logic(self, db_session):
        """测试复杂业务逻辑"""
        # 查找活跃用户：状态为0，未删除，ID大于0
        spec = (
            equals(UserDO.status, "0") &
            equals(UserDO.del_flag, "0") &
            gt(UserDO.user_id, 0)
        )
        
        stmt = select(UserDO)
        stmt = spec.apply(stmt)
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        
        assert all(
            u.status == "0" and u.del_flag == "0" and u.user_id > 0
            for u in users
        )
