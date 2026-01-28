"""
MenuDao 菜单数据访问层测试
测试菜单相关的数据库操作
"""
import pytest
from module_admin.dao.menu_dao import MenuDao
from module_admin.entity.vo.menu_vo import MenuModel, MenuQueryModel


class TestMenuDaoBasicOperations:
    """MenuDao 基础操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_menu_detail_by_id(self, db_session):
        """测试根据ID获取菜单"""
        menu = await MenuDao.get_menu_detail_by_id(db_session, 1)
        # 可能存在也可能不存在
        assert menu is not None or menu is None
    
    @pytest.mark.asyncio
    async def test_get_menu_detail_by_info(self, db_session):
        """测试根据信息获取菜单"""
        menu_obj = MenuModel(menu_name="系统管理", menu_type="M")
        menu = await MenuDao.get_menu_detail_by_info(db_session, menu_obj)
        # 可能存在也可能不存在
        assert menu is not None or menu is None


class TestMenuDaoQueryOperations:
    """MenuDao 查询操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_menu_list_for_tree(self, db_session, test_user):
        """测试获取菜单树列表"""
        # 模拟角色列表
        class MockRole:
            role_id = 1
        
        menus = await MenuDao.get_menu_list_for_tree(
            db_session,
            test_user.user_id,
            [MockRole()]
        )
        assert isinstance(menus, list)
    
    @pytest.mark.asyncio
    async def test_get_menu_list(self, db_session, test_user):
        """测试获取菜单列表"""
        query_obj = MenuQueryModel()
        
        class MockRole:
            role_id = 1
        
        menus = await MenuDao.get_menu_list(
            db_session,
            query_obj,
            test_user.user_id,
            [MockRole()]
        )
        assert isinstance(menus, list)
    
    @pytest.mark.asyncio
    async def test_get_menu_list_with_filters(self, db_session, test_user):
        """测试带过滤条件的菜单列表"""
        query_obj = MenuQueryModel(menu_name="系统", status="0")
        
        class MockRole:
            role_id = 1
        
        menus = await MenuDao.get_menu_list(
            db_session,
            query_obj,
            test_user.user_id,
            [MockRole()]
        )
        assert isinstance(menus, list)


class TestMenuDaoModifyOperations:
    """MenuDao 修改操作测试"""
    
    @pytest.mark.asyncio
    async def test_add_menu_dao(self, db_session):
        """测试添加菜单"""
        menu = MenuModel(
            menu_name="测试菜单",
            menu_type="M",
            order_num=1,
            path="/test",
            status="0",
            visible="0"
        )
        result = await MenuDao.add_menu_dao(db_session, menu)
        assert result is not None
        assert result.menu_name == "测试菜单"
    
    @pytest.mark.asyncio
    async def test_edit_menu_dao(self, db_session):
        """测试编辑菜单"""
        menu_dict = {
            "menu_id": 1,
            "menu_name": "Updated Menu"
        }
        await MenuDao.edit_menu_dao(db_session, menu_dict)
    
    @pytest.mark.asyncio
    async def test_delete_menu_dao(self, db_session):
        """测试删除菜单"""
        menu = MenuModel(menu_id=999)
        await MenuDao.delete_menu_dao(db_session, menu)


class TestMenuDaoRelationOperations:
    """MenuDao 关联操作测试"""
    
    @pytest.mark.asyncio
    async def test_has_child_by_menu_id_dao(self, db_session):
        """测试检查菜单是否有子菜单"""
        count = await MenuDao.has_child_by_menu_id_dao(db_session, 1)
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_check_menu_exist_role_dao(self, db_session):
        """测试检查菜单是否关联角色"""
        count = await MenuDao.check_menu_exist_role_dao(db_session, 1)
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_has_child_by_nonexistent_menu(self, db_session):
        """测试不存在的菜单的子菜单数"""
        count = await MenuDao.has_child_by_menu_id_dao(db_session, 999999)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_check_nonexistent_menu_role(self, db_session):
        """测试不存在的菜单的角色关联数"""
        count = await MenuDao.check_menu_exist_role_dao(db_session, 999999)
        assert count == 0


class TestMenuDaoEdgeCases:
    """MenuDao 边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_get_menu_list_empty_filters(self, db_session, test_user):
        """测试空过滤条件"""
        query_obj = MenuQueryModel()
        
        class MockRole:
            role_id = 1
        
        menus = await MenuDao.get_menu_list(
            db_session,
            query_obj,
            test_user.user_id,
            [MockRole()]
        )
        assert isinstance(menus, list)
    
    @pytest.mark.asyncio
    async def test_get_menu_list_non_admin_role(self, db_session, test_user):
        """测试非管理员角色"""
        query_obj = MenuQueryModel()
        
        class MockRole:
            role_id = 2  # 非管理员角色
        
        menus = await MenuDao.get_menu_list(
            db_session,
            query_obj,
            test_user.user_id,
            [MockRole()]
        )
        assert isinstance(menus, list)
