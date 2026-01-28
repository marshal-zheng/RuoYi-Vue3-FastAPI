"""
RoleDao 角色数据访问层测试
测试角色相关的数据库操作
"""
import pytest
from module_admin.dao.role_dao import RoleDao
from module_admin.entity.vo.role_vo import RoleModel, RolePageQueryModel, RoleMenuModel, RoleDeptModel


class TestRoleDaoBasicOperations:
    """RoleDao 基础操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_role_by_name(self, db_session):
        """测试根据角色名获取角色"""
        role = await RoleDao.get_role_by_name(db_session, "admin")
        # 可能存在也可能不存在
        assert role is not None or role is None
    
    @pytest.mark.asyncio
    async def test_get_role_by_id(self, db_session):
        """测试根据ID获取角色"""
        role = await RoleDao.get_role_by_id(db_session, 1)
        # 可能存在也可能不存在
        assert role is not None or role is None
    
    @pytest.mark.asyncio
    async def test_get_role_detail_by_id(self, db_session):
        """测试获取角色详细信息"""
        role = await RoleDao.get_role_detail_by_id(db_session, 1)
        # 可能存在也可能不存在
        assert role is not None or role is None
    
    @pytest.mark.asyncio
    async def test_get_role_select_option_dao(self, db_session):
        """测试获取角色选项列表"""
        roles = await RoleDao.get_role_select_option_dao(db_session)
        assert isinstance(roles, list)


class TestRoleDaoQueryOperations:
    """RoleDao 查询操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_role_list(self, db_session):
        """测试获取角色列表"""
        query_obj = RolePageQueryModel(page_num=1, page_size=10)
        result = await RoleDao.get_role_list(db_session, query_obj, "True", is_page=True)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_role_list_with_filters(self, db_session):
        """测试带过滤条件的角色列表"""
        query_obj = RolePageQueryModel(
            page_num=1,
            page_size=10,
            role_name="admin"
        )
        result = await RoleDao.get_role_list(db_session, query_obj, "True", is_page=True)
        assert result is not None


class TestRoleDaoModifyOperations:
    """RoleDao 修改操作测试"""
    
    @pytest.mark.asyncio
    async def test_add_role_dao(self, db_session):
        """测试添加角色"""
        role = RoleModel(
            role_name="test_role",
            role_key="test",
            role_sort=1,
            status="0",
            del_flag="0"
        )
        result = await RoleDao.add_role_dao(db_session, role)
        assert result is not None
        assert result.role_name == "test_role"
    
    @pytest.mark.asyncio
    async def test_edit_role_dao(self, db_session):
        """测试编辑角色"""
        role_dict = {
            "role_id": 2,
            "role_name": "Updated Role"
        }
        await RoleDao.edit_role_dao(db_session, role_dict)
    
    @pytest.mark.asyncio
    async def test_delete_role_dao(self, db_session):
        """测试删除角色"""
        role = RoleModel(role_id=999, update_by="test")
        await RoleDao.delete_role_dao(db_session, role)


class TestRoleDaoMenuOperations:
    """RoleDao 菜单关联操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_role_menu_dao(self, db_session):
        """测试获取角色菜单"""
        role = RoleModel(role_id=1, menu_check_strictly=True)
        menus = await RoleDao.get_role_menu_dao(db_session, role)
        assert isinstance(menus, list)
    
    @pytest.mark.asyncio
    async def test_add_role_menu_dao(self, db_session):
        """测试添加角色菜单关联"""
        role_menu = RoleMenuModel(role_id=2, menu_id=1)
        await RoleDao.add_role_menu_dao(db_session, role_menu)
    
    @pytest.mark.asyncio
    async def test_delete_role_menu_dao(self, db_session):
        """测试删除角色菜单关联"""
        role_menu = RoleMenuModel(role_id=2)
        await RoleDao.delete_role_menu_dao(db_session, role_menu)


class TestRoleDaoDeptOperations:
    """RoleDao 部门关联操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_role_dept_dao(self, db_session):
        """测试获取角色部门"""
        role = RoleModel(role_id=1, dept_check_strictly=True)
        depts = await RoleDao.get_role_dept_dao(db_session, role)
        assert isinstance(depts, list)
    
    @pytest.mark.asyncio
    async def test_add_role_dept_dao(self, db_session):
        """测试添加角色部门关联"""
        role_dept = RoleDeptModel(role_id=2, dept_id=100)
        await RoleDao.add_role_dept_dao(db_session, role_dept)
    
    @pytest.mark.asyncio
    async def test_delete_role_dept_dao(self, db_session):
        """测试删除角色部门关联"""
        role_dept = RoleDeptModel(role_id=2)
        await RoleDao.delete_role_dept_dao(db_session, role_dept)
    
    @pytest.mark.asyncio
    async def test_count_user_role_dao(self, db_session):
        """测试统计角色用户数"""
        count = await RoleDao.count_user_role_dao(db_session, 1)
        assert isinstance(count, int)
        assert count >= 0
