from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from config.constant import CommonConstant, MenuConstant
from config.env import CacheConfig
from exceptions.exception import (
    BusinessException, 
    ResourceNotFoundException, 
    ResourceConflictException,
    ValidationException
)
from config.error_codes import ErrorCode
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuQueryModel, MenuModel
from module_admin.entity.vo.role_vo import RoleMenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.repository import MenuRepository, RoleRepository, RoleMenuRepository
from utils.common_util import CamelCaseUtil
from utils.string_util import StringUtil
from utils.transaction_manager import transactional
from utils.query_cache import get_query_cache


class MenuService:
    """
    菜单管理模块服务层
    """

    @classmethod
    async def get_menu_tree_services(cls, query_db: AsyncSession, current_user: Optional[CurrentUserModel] = None):
        """
        获取菜单树信息service

        :param query_db: orm对象
        :param current_user: 当前用户对象
        :return: 菜单树信息对象
        """
        cache = get_query_cache()
        is_admin = bool(getattr(current_user.user, 'admin', False)) or 'admin' in (current_user.roles or [])
        cache_key = cache.build_key(
            'menu:tree',
            {
                'user_id': current_user.user.user_id,
                'is_admin': is_admin,
            },
        )
        async def _load():
            menu_repo = MenuRepository(query_db)
            if is_admin:
                menu_list_result = await menu_repo.find_all_active()
            else:
                menu_list_result = await menu_repo.find_menus_by_user(current_user.user.user_id)
            return cls.list_to_tree(menu_list_result)

        return await cache.get_or_set(
            cache_key,
            _load,
            CacheConfig.query_cache_default_ttl,
            CacheConfig.query_cache_lock_enabled,
        )

    @classmethod
    async def get_role_menu_tree_services(
        cls, query_db: AsyncSession, role_id: int, current_user: Optional[CurrentUserModel] = None
    ):
        """
        根据角色id获取菜单树信息service

        :param query_db: orm对象
        :param role_id: 角色id
        :param current_user: 当前用户对象
        :return: 当前角色id的菜单树信息对象
        """
        cache = get_query_cache()
        is_admin = bool(getattr(current_user.user, 'admin', False)) or 'admin' in (current_user.roles or [])
        cache_key = cache.build_key(
            'menu:role_tree',
            {
                'role_id': role_id,
                'user_id': current_user.user.user_id,
                'is_admin': is_admin,
            },
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            return RoleMenuQueryModel(**cached)

        menu_repo = MenuRepository(query_db)
        if is_admin:
            menu_list_result = await menu_repo.find_all_active()
        else:
            menu_list_result = await menu_repo.find_menus_by_user(current_user.user.user_id)
        menu_tree_result = cls.list_to_tree(menu_list_result)
        role_repo = RoleRepository(query_db)
        role_menu_repo = RoleMenuRepository(query_db)
        role = await role_repo.find_by_id(role_id)
        role_menu_list = await role_menu_repo.find_by_role_id(role_id) if role else []
        checked_keys = [row.menu_id for row in role_menu_list]
        result = RoleMenuQueryModel(menus=menu_tree_result, checkedKeys=checked_keys)
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    @classmethod
    async def get_menu_list_services(
        cls, query_db: AsyncSession, page_object: MenuQueryModel, current_user: Optional[CurrentUserModel] = None
    ):
        """
        获取菜单列表信息service

        :param query_db: orm对象
        :param page_object: 分页查询参数对象
        :param current_user: 当前用户对象
        :return: 菜单列表信息对象
        """
        cache = get_query_cache()
        is_admin = bool(getattr(current_user.user, 'admin', False)) or 'admin' in (current_user.roles or [])
        cache_key = cache.build_key(
            'menu:list',
            {
                'user_id': current_user.user.user_id if not is_admin else None,
                'is_admin': is_admin,
                'menu_name': page_object.menu_name,
                'visible': page_object.visible,
                'status': page_object.status,
            },
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        menu_repo = MenuRepository(query_db)
        menu_list_result = await menu_repo.find_with_filters(
            user_id=current_user.user.user_id if not is_admin else None,
            menu_name=page_object.menu_name,
            visible=page_object.visible,
            status=page_object.status,
            is_admin=is_admin
        )
        result = CamelCaseUtil.transform_result(menu_list_result)
        await cache.set(cache_key, result, CacheConfig.query_cache_default_ttl)
        return result

    @classmethod
    async def check_menu_name_unique_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        校验菜单名称是否唯一service

        :param query_db: orm对象
        :param page_object: 菜单对象
        :return: 校验结果
        """
        menu_id = -1 if page_object.menu_id is None else page_object.menu_id
        menu_repo = MenuRepository(query_db)
        menu = await menu_repo.find_by_parent_and_name(
            parent_id=page_object.parent_id,
            menu_name=page_object.menu_name
        )
        if menu and menu.menu_id != menu_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    @transactional()
    async def add_menu_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        新增菜单信息service

        :param query_db: orm对象
        :param page_object: 新增菜单对象
        :return: 新增菜单校验结果
        """
        if not await cls.check_menu_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'新增菜单{page_object.menu_name}失败，菜单名称已存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=f'Menu name already exists: parent_id={page_object.parent_id}, menu_name={page_object.menu_name}'
            )
        elif page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
            raise ValidationException(
                user_message=f'新增菜单{page_object.menu_name}失败，地址必须以http(s)://开头',
                developer_message=f'Invalid menu path format: path={page_object.path}',
                field='path'
            )
        
        menu_repo = MenuRepository(query_db)
        db_menu = MenuDO(**page_object.model_dump())
        await menu_repo.add(db_menu)
        await cls._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_menu_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        编辑菜单信息service

        :param query_db: orm对象
        :param page_object: 编辑部门对象
        :return: 编辑菜单校验结果
        """
        edit_menu = page_object.model_dump(exclude_unset=True)
        menu_info = await cls.menu_detail_services(query_db, page_object.menu_id)
        if not menu_info.menu_id:
            raise ResourceNotFoundException(
                user_message='菜单不存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=f'Menu not found: menu_id={page_object.menu_id}'
            )
        
        if not await cls.check_menu_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'修改菜单{page_object.menu_name}失败，菜单名称已存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=f'Menu name already exists: parent_id={page_object.parent_id}, menu_name={page_object.menu_name}'
            )
        elif page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
            raise ValidationException(
                user_message=f'修改菜单{page_object.menu_name}失败，地址必须以http(s)://开头',
                developer_message=f'Invalid menu path format: path={page_object.path}',
                field='path'
            )
        elif page_object.menu_id == page_object.parent_id:
            raise ValidationException(
                user_message=f'修改菜单{page_object.menu_name}失败，上级菜单不能选择自己',
                developer_message=f'Menu cannot be its own parent: menu_id={page_object.menu_id}',
                field='parent_id'
            )
        
        menu_repo = MenuRepository(query_db)
        db_menu = await menu_repo.find_by_id(page_object.menu_id)
        if db_menu:
            for key, value in edit_menu.items():
                if hasattr(db_menu, key):
                    setattr(db_menu, key, value)
            await menu_repo.update(db_menu)
        await cls._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def delete_menu_services(cls, query_db: AsyncSession, page_object: DeleteMenuModel):
        """
        删除菜单信息service

        :param query_db: orm对象
        :param page_object: 删除菜单对象
        :return: 删除菜单校验结果
        """
        if not page_object.menu_ids:
            raise ValidationException(
                user_message='传入菜单id为空',
                developer_message='Menu IDs parameter is empty',
                field='menu_ids'
            )
        
        menu_repo = MenuRepository(query_db)
        menu_id_list = page_object.menu_ids.split(',')
        for menu_id in menu_id_list:
            if (await menu_repo.count_children(int(menu_id))) > 0:
                raise ResourceConflictException(
                    user_message='存在子菜单,不允许删除',
                    error_code=ErrorCode.MENU_HAS_CHILDREN,
                    developer_message=f'Menu has children: menu_id={menu_id}'
                )
            elif (await menu_repo.count_roles(int(menu_id))) > 0:
                raise ResourceConflictException(
                    user_message='菜单已分配,不允许删除',
                    error_code=ErrorCode.MENU_HAS_CHILDREN,
                    developer_message=f'Menu is assigned to roles: menu_id={menu_id}'
                )
            await menu_repo.delete_by_id(int(menu_id))
        await cls._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def menu_detail_services(cls, query_db: AsyncSession, menu_id: int):
        """
        获取菜单详细信息service

        :param query_db: orm对象
        :param menu_id: 菜单id
        :return: 菜单id对应的信息
        """
        cache = get_query_cache()
        cache_key = cache.build_key('menu:detail', {'menu_id': menu_id})
        cached = await cache.get(cache_key)
        if cached is not None:
            return MenuModel(**cached)

        menu_repo = MenuRepository(query_db)
        menu = await menu_repo.find_by_id(menu_id)
        if menu:
            result = MenuModel(**CamelCaseUtil.transform_result(menu))
        else:
            result = MenuModel(**dict())
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    @staticmethod
    async def _invalidate_menu_cache():
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:menu:*')

    @classmethod
    def list_to_tree(cls, permission_list: list) -> list:
        """
        工具方法：根据菜单列表信息生成树形嵌套数据

        :param permission_list: 菜单列表信息
        :return: 菜单树形嵌套数据
        """
        permission_list = [
            dict(id=item.menu_id, label=item.menu_name, parentId=item.parent_id) for item in permission_list
        ]
        # 转成id为key的字典
        mapping: dict = dict(zip([i['id'] for i in permission_list], permission_list))

        # 树容器
        container: list = []

        for d in permission_list:
            # 如果找不到父级项，则是根节点
            parent: dict = mapping.get(d['parentId'])
            if parent is None:
                container.append(d)
            else:
                children: list = parent.get('children')
                if not children:
                    children = []
                children.append(d)
                parent.update({'children': children})

        return container
