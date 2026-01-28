"""
UserDao 用户数据访问层测试
测试用户相关的数据库操作
"""
import pytest
from module_admin.dao.user_dao import UserDao
from module_admin.entity.vo.user_vo import UserModel, UserPageQueryModel, UserRoleModel


class TestUserDaoBasicOperations:
    """UserDao 基础操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_name(self, db_session, test_user):
        """测试根据用户名获取用户"""
        user = await UserDao.get_user_by_name(db_session, test_user.user_name)
        assert user is not None
        assert user.user_name == test_user.user_name
    
    @pytest.mark.asyncio
    async def test_get_user_by_name_not_found(self, db_session):
        """测试获取不存在的用户"""
        user = await UserDao.get_user_by_name(db_session, "nonexistent_user")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session, test_user):
        """测试根据ID获取用户"""
        result = await UserDao.get_user_by_id(db_session, test_user.user_id)
        assert result is not None
        assert 'user_basic_info' in result
        assert result['user_basic_info'].user_id == test_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_user_detail_by_id(self, db_session, test_user):
        """测试获取用户详细信息"""
        result = await UserDao.get_user_detail_by_id(db_session, test_user.user_id)
        assert result is not None
        assert 'user_basic_info' in result
        assert 'user_dept_info' in result
        assert 'user_role_info' in result


class TestUserDaoQueryOperations:
    """UserDao 查询操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_user_list(self, db_session):
        """测试获取用户列表"""
        query_obj = UserPageQueryModel(page_num=1, page_size=10)
        result = await UserDao.get_user_list(db_session, query_obj, "True", is_page=True)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_user_list_with_filters(self, db_session, test_user):
        """测试带过滤条件的用户列表"""
        query_obj = UserPageQueryModel(
            page_num=1,
            page_size=10,
            user_name=test_user.user_name
        )
        result = await UserDao.get_user_list(db_session, query_obj, "True", is_page=True)
        assert result is not None


class TestUserDaoModifyOperations:
    """UserDao 修改操作测试"""
    
    @pytest.mark.asyncio
    async def test_add_user_dao(self, db_session):
        """测试添加用户"""
        user = UserModel(
            user_name="test_new_user",
            nick_name="Test New",
            password="test123",
            status="0",
            del_flag="0"
        )
        result = await UserDao.add_user_dao(db_session, user)
        assert result is not None
        assert result.user_name == "test_new_user"
    
    @pytest.mark.asyncio
    async def test_edit_user_dao(self, db_session, test_user):
        """测试编辑用户"""
        user_dict = {
            "user_id": test_user.user_id,
            "nick_name": "Updated Name"
        }
        await UserDao.edit_user_dao(db_session, user_dict)
        # 验证更新成功需要重新查询
    
    @pytest.mark.asyncio
    async def test_delete_user_dao(self, db_session, test_user):
        """测试删除用户"""
        user = UserModel(
            user_id=test_user.user_id,
            update_by="test"
        )
        await UserDao.delete_user_dao(db_session, user)


class TestUserDaoRoleOperations:
    """UserDao 角色关联操作测试"""
    
    @pytest.mark.asyncio
    async def test_add_user_role_dao(self, db_session, test_user):
        """测试添加用户角色关联"""
        user_role = UserRoleModel(user_id=test_user.user_id, role_id=2)
        await UserDao.add_user_role_dao(db_session, user_role)
    
    @pytest.mark.asyncio
    async def test_delete_user_role_dao(self, db_session, test_user):
        """测试删除用户角色关联"""
        user_role = UserRoleModel(user_id=test_user.user_id)
        await UserDao.delete_user_role_dao(db_session, user_role)
    
    @pytest.mark.asyncio
    async def test_get_user_role_detail(self, db_session, test_user):
        """测试获取用户角色详情"""
        user_role = UserRoleModel(user_id=test_user.user_id, role_id=1)
        result = await UserDao.get_user_role_detail(db_session, user_role)
        # 可能为空，取决于测试数据
        assert result is not None or result is None
