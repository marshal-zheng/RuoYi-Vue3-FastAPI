from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.constant import CommonConstant, MenuConstant
from config.env import CacheConfig
from config.error_codes import ErrorCode
from exceptions.exception import ResourceConflictException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuModel, MenuQueryModel
from module_admin.entity.vo.role_vo import RoleMenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from ports import IMenuRepository, IRoleMenuRepository, IRoleRepository
from utils.common_util import CamelCaseUtil
from utils.query_cache import get_query_cache
from utils.string_util import StringUtil
from utils.transaction_manager import transactional


class MenuService:
    """
    菜单管理模块服务层
    """

    def __init__(
        self,
        menu_repo: IMenuRepository,
        role_repo: IRoleRepository,
        role_menu_repo: IRoleMenuRepository,
        query_db: AsyncSession,
    ):
        self.menu_repo = menu_repo
        self.role_repo = role_repo
        self.role_menu_repo = role_menu_repo
        self.query_db = query_db

    async def get_menu_tree_services(self, current_user: Optional[CurrentUserModel] = None):
        """
        获取菜单树信息service

        :param current_user: 当前用户对象
        :return: 菜单树信息对象
        """
        if current_user is None:
            raise ValidationException(
                user_message='当前用户不能为空',
                developer_message='Current user is required for menu tree query',
                field='current_user',
            )

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
            if is_admin:
                menu_list_result = await self.menu_repo.find_all_active()
            else:
                menu_list_result = await self.menu_repo.find_menus_by_user(current_user.user.user_id)
            return self.list_to_tree(menu_list_result)

        return await cache.get_or_set(
            cache_key,
            _load,
            CacheConfig.query_cache_default_ttl,
            CacheConfig.query_cache_lock_enabled,
        )

    async def get_role_menu_tree_services(self, role_id: int, current_user: Optional[CurrentUserModel] = None):
        """
        根据角色id获取菜单树信息service

        :param role_id: 角色id
        :param current_user: 当前用户对象
        :return: 当前角色id的菜单树信息对象
        """
        if current_user is None:
            raise ValidationException(
                user_message='当前用户不能为空',
                developer_message='Current user is required for role menu tree query',
                field='current_user',
            )

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

        if is_admin:
            menu_list_result = await self.menu_repo.find_all_active()
        else:
            menu_list_result = await self.menu_repo.find_menus_by_user(current_user.user.user_id)
        menu_tree_result = self.list_to_tree(menu_list_result)

        role = await self.role_repo.find_by_id(role_id)
        role_menu_list = await self.role_menu_repo.find_by_role_id(role_id) if role else []
        checked_keys = [row.menu_id for row in role_menu_list]
        result = RoleMenuQueryModel(menus=menu_tree_result, checkedKeys=checked_keys)
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    async def get_menu_list_services(
        self,
        page_object: MenuQueryModel,
        current_user: Optional[CurrentUserModel] = None,
    ):
        """
        获取菜单列表信息service

        :param page_object: 分页查询参数对象
        :param current_user: 当前用户对象
        :return: 菜单列表信息对象
        """
        if current_user is None:
            raise ValidationException(
                user_message='当前用户不能为空',
                developer_message='Current user is required for menu list query',
                field='current_user',
            )

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

        menu_list_result = await self.menu_repo.find_with_filters(
            user_id=current_user.user.user_id if not is_admin else None,
            menu_name=page_object.menu_name,
            visible=page_object.visible,
            status=page_object.status,
            is_admin=is_admin,
        )
        result = CamelCaseUtil.transform_result(menu_list_result)
        await cache.set(cache_key, result, CacheConfig.query_cache_default_ttl)
        return result

    async def check_menu_name_unique_services(self, page_object: MenuModel):
        """
        校验菜单名称是否唯一service

        :param page_object: 菜单对象
        :return: 校验结果
        """
        menu_id = -1 if page_object.menu_id is None else page_object.menu_id
        menu = await self.menu_repo.find_by_parent_and_name(parent_id=page_object.parent_id, menu_name=page_object.menu_name)
        if menu and menu.menu_id != menu_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_menu_services(self, page_object: MenuModel):
        """
        新增菜单信息service

        :param page_object: 新增菜单对象
        :return: 新增菜单校验结果
        """
        if not await self.check_menu_name_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增菜单{page_object.menu_name}失败，菜单名称已存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=(
                    f'Menu name already exists: parent_id={page_object.parent_id}, '
                    f'menu_name={page_object.menu_name}'
                ),
            )

        if page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
            raise ValidationException(
                user_message=f'新增菜单{page_object.menu_name}失败，地址必须以http(s)://开头',
                developer_message=f'Invalid menu path format: path={page_object.path}',
                field='path',
            )

        db_menu = MenuDO(**page_object.model_dump())
        await self.menu_repo.add(db_menu)
        await self._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def edit_menu_services(self, page_object: MenuModel):
        """
        编辑菜单信息service

        :param page_object: 编辑部门对象
        :return: 编辑菜单校验结果
        """
        edit_menu = page_object.model_dump(exclude_unset=True)
        menu_info = await self.menu_detail_services(page_object.menu_id)
        if not menu_info.menu_id:
            raise ResourceNotFoundException(
                user_message='菜单不存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=f'Menu not found: menu_id={page_object.menu_id}',
            )

        if not await self.check_menu_name_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'修改菜单{page_object.menu_name}失败，菜单名称已存在',
                error_code=ErrorCode.MENU_NOT_FOUND,
                developer_message=(
                    f'Menu name already exists: parent_id={page_object.parent_id}, '
                    f'menu_name={page_object.menu_name}'
                ),
            )

        if page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
            raise ValidationException(
                user_message=f'修改菜单{page_object.menu_name}失败，地址必须以http(s)://开头',
                developer_message=f'Invalid menu path format: path={page_object.path}',
                field='path',
            )

        if page_object.menu_id == page_object.parent_id:
            raise ValidationException(
                user_message=f'修改菜单{page_object.menu_name}失败，上级菜单不能选择自己',
                developer_message=f'Menu cannot be its own parent: menu_id={page_object.menu_id}',
                field='parent_id',
            )

        db_menu = await self.menu_repo.find_by_id(page_object.menu_id)
        if db_menu:
            for key, value in edit_menu.items():
                if hasattr(db_menu, key):
                    setattr(db_menu, key, value)
            await self.menu_repo.update(db_menu)
        await self._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_menu_services(self, page_object: DeleteMenuModel):
        """
        删除菜单信息service

        :param page_object: 删除菜单对象
        :return: 删除菜单校验结果
        """
        if not page_object.menu_ids:
            raise ValidationException(
                user_message='传入菜单id为空',
                developer_message='Menu IDs parameter is empty',
                field='menu_ids',
            )

        menu_id_list = page_object.menu_ids.split(',')
        for menu_id in menu_id_list:
            menu_id_value = int(menu_id)
            if (await self.menu_repo.count_children(menu_id_value)) > 0:
                raise ResourceConflictException(
                    user_message='存在子菜单,不允许删除',
                    error_code=ErrorCode.MENU_HAS_CHILDREN,
                    developer_message=f'Menu has children: menu_id={menu_id_value}',
                )
            if (await self.menu_repo.count_roles(menu_id_value)) > 0:
                raise ResourceConflictException(
                    user_message='菜单已分配,不允许删除',
                    error_code=ErrorCode.MENU_HAS_CHILDREN,
                    developer_message=f'Menu is assigned to roles: menu_id={menu_id_value}',
                )
            await self.menu_repo.delete_by_id(menu_id_value)
        await self._invalidate_menu_cache()
        return CrudResponseModel(is_success=True, message='删除成功')

    async def menu_detail_services(self, menu_id: int):
        """
        获取菜单详细信息service

        :param menu_id: 菜单id
        :return: 菜单id对应的信息
        """
        cache = get_query_cache()
        cache_key = cache.build_key('menu:detail', {'menu_id': menu_id})
        cached = await cache.get(cache_key)
        if cached is not None:
            return MenuModel(**cached)

        menu = await self.menu_repo.find_by_id(menu_id)
        if menu:
            result = MenuModel(**CamelCaseUtil.transform_result(menu))
        else:
            result = MenuModel(**{})
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    @staticmethod
    async def _invalidate_menu_cache():
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:menu:*')

    @staticmethod
    def list_to_tree(permission_list: list) -> list:
        """
        工具方法：根据菜单列表信息生成树形嵌套数据

        :param permission_list: 菜单列表信息
        :return: 菜单树形嵌套数据
        """
        permission_list = [
            {'id': item.menu_id, 'label': item.menu_name, 'parentId': item.parent_id}
            for item in permission_list
        ]
        mapping = {item['id']: item for item in permission_list}
        container: list = []

        for item in permission_list:
            parent = mapping.get(item['parentId'])
            if parent is None:
                container.append(item)
                continue

            children = parent.get('children') or []
            children.append(item)
            parent.update({'children': children})

        return container
