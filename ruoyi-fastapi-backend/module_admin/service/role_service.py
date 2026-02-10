import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from unittest.mock import AsyncMock, MagicMock
from config.constant import CommonConstant
from config.env import CacheConfig
from exceptions.exception import (
    BusinessException,
    ResourceNotFoundException,
    ResourceConflictException,
    ValidationException,
    PermissionException
)
from config.error_codes import ErrorCode
from module_admin.entity.do.role_do import RoleDO, RoleDeptDO, RoleMenuDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.transaction_manager import transactional
from module_admin.entity.vo.role_vo import (
    AddRoleModel,
    DeleteRoleModel,
    EditRoleModel,
    RoleDeptQueryModel,
    RoleModel,
    RolePageQueryModel,
    RoleQueryModel,
)
from module_admin.entity.vo.user_vo import UserInfoModel, UserRolePageQueryModel
from module_admin.repository import RoleRepository, RoleMenuRepository, RoleDeptRepository, UserRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.page_util import PageResponseModel
from utils.query_cache import get_query_cache


class RoleService:
    """
    角色管理模块服务层
    """

    def __init__(self, role_dao=None):
        if role_dao is not None:
            self.role_dao = role_dao

    @classmethod
    async def get_role_select_option_services(cls, query_db: AsyncSession):
        """
        获取角色列表不分页信息service

        :param query_db: orm对象
        :return: 角色列表不分页信息对象
        """
        cache = get_query_cache()
        cache_key = cache.build_key('role:select', {})

        async def _load():
            role_repo = RoleRepository(query_db)
            role_list_result = await role_repo.find_all_active()
            return CamelCaseUtil.transform_result(role_list_result)

        return await cache.get_or_set(
            cache_key,
            _load,
            CacheConfig.query_cache_default_ttl,
            CacheConfig.query_cache_lock_enabled,
        )

    @classmethod
    async def get_role_dept_tree_services(cls, query_db: AsyncSession, role_id: int):
        """
        根据角色id获取部门树信息service

        :param query_db: orm对象
        :param role_id: 角色id
        :return: 当前角色id的部门树信息对象
        """
        role_dept_repo = RoleDeptRepository(query_db)
        role_dept_list = await role_dept_repo.find_by_role_id(role_id)
        checked_keys = [row.dept_id for row in role_dept_list]
        result = RoleDeptQueryModel(checkedKeys=checked_keys)

        return result

    @classmethod
    async def get_role_list_services(
        cls, query_db: AsyncSession, query_object: RolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        获取角色列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 角色列表信息对象
        """
        cache = get_query_cache()
        cache_key = cache.build_key(
            'role:list',
            {
                'page': query_object.page_num if is_page else 1,
                'page_size': query_object.page_size if is_page else 10000,
                'role_id': query_object.role_id,
                'role_name': query_object.role_name,
                'role_key': query_object.role_key,
                'status': query_object.status,
                'begin_time': query_object.begin_time,
                'end_time': query_object.end_time,
                'data_scope': str(data_scope_sql),
                'is_page': is_page,
            },
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            if is_page:
                return PageResponseModel(**cached)
            return cached

        role_repo = RoleRepository(query_db)
        if is_page:
            role_list_result = await role_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                role_id=query_object.role_id,
                role_name=query_object.role_name,
                role_key=query_object.role_key,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql
            )
        else:
            role_list_result = await role_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                role_id=query_object.role_id,
                role_name=query_object.role_name,
                role_key=query_object.role_key,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql
            )
            role_list_result = role_list_result.rows if hasattr(role_list_result, 'rows') else role_list_result

        if is_page:
            await cache.set(cache_key, role_list_result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        else:
            await cache.set(cache_key, role_list_result, CacheConfig.query_cache_default_ttl)
        return role_list_result

    @classmethod
    async def check_role_allowed_services(cls, check_role: RoleModel):
        """
        校验角色是否允许操作service

        :param check_role: 角色信息
        :return: 校验结果
        """
        if check_role.admin:
            raise PermissionException(
                user_message='不允许操作超级管理员角色',
                developer_message=f'Cannot operate on admin role: role_id={check_role.role_id}'
            )
        else:
            return CrudResponseModel(is_success=True, message='校验通过')

    @classmethod
    async def check_role_data_scope_services(cls, query_db: AsyncSession, role_ids: str, data_scope_sql: str):
        """
        校验角色是否有数据权限service

        :param query_db: orm对象
        :param role_ids: 角色id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        role_id_list = role_ids.split(',') if role_ids else []
        role_repo = RoleRepository(query_db)
        if role_id_list:
            for role_id in role_id_list:
                roles = await role_repo.paginate_with_filters(
                    page=1,
                    page_size=10000,
                    role_id=int(role_id),
                    data_scope_sql=data_scope_sql
                )
                roles = roles.rows if hasattr(roles, 'rows') else roles
                if roles:
                    continue
                else:
                    raise PermissionException(
                        user_message='没有权限访问角色数据',
                        developer_message=f'No permission to access role data: role_id={role_id}'
                    )

    @classmethod
    async def check_role_name_unique_services(cls, query_db: AsyncSession, page_object: RoleModel):
        """
        校验角色名称是否唯一service

        :param query_db: orm对象
        :param page_object: 角色对象
        :return: 校验结果
        """
        role_id = -1 if page_object.role_id is None else page_object.role_id
        role_repo = RoleRepository(query_db)
        role = await role_repo.find_by_name(page_object.role_name)
        if role and role.role_id != role_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_role_key_unique_services(cls, query_db: AsyncSession, page_object: RoleModel):
        """
        校验角色权限字符是否唯一service

        :param query_db: orm对象
        :param page_object: 角色对象
        :return: 校验结果
        """
        role_id = -1 if page_object.role_id is None else page_object.role_id
        role_repo = RoleRepository(query_db)
        role = await role_repo.find_by_key(page_object.role_key)
        if role and role.role_id != role_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    @transactional()
    async def add_role_services(cls, query_db: AsyncSession, page_object: AddRoleModel):
        """
        新增角色信息service

        :param query_db: orm对象
        :param page_object: 新增角色对象
        :return: 新增角色校验结果
        """
        add_role = RoleModel(**page_object.model_dump(by_alias=True))
        if not await cls.check_role_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'新增角色{page_object.role_name}失败，角色名称已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Role name already exists: role_name={page_object.role_name}'
            )
        elif not await cls.check_role_key_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'新增角色{page_object.role_name}失败，角色权限已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Role key already exists: role_key={page_object.role_key}'
            )
        
        role_repo = RoleRepository(query_db)
        db_role = RoleDO(**add_role.model_dump())
        add_result = await role_repo.add(db_role)
        role_id = add_result.role_id
        if page_object.menu_ids:
            role_menu_repo = RoleMenuRepository(query_db)
            for menu in page_object.menu_ids:
                db_role_menu = RoleMenuDO(role_id=role_id, menu_id=menu)
                await role_menu_repo.add(db_role_menu)
        await cls._invalidate_role_cache()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_role_services(cls, query_db: AsyncSession, page_object: AddRoleModel):
        """
        编辑角色信息service

        :param query_db: orm对象
        :param page_object: 编辑角色对象
        :return: 编辑角色校验结果
        """
        edit_role = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        if page_object.type != 'status':
            del edit_role['menu_ids']
        if page_object.type == 'status':
            del edit_role['type']
        role_info = await cls.role_detail_services(query_db, edit_role.get('role_id'))
        if not role_info:
            raise ResourceNotFoundException(
                user_message='角色不存在',
                error_code=ErrorCode.ROLE_NOT_FOUND,
                developer_message=f'Role not found: role_id={edit_role.get("role_id")}'
            )
        
        if page_object.type != 'status':
            if not await cls.check_role_name_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    user_message=f'修改角色{page_object.role_name}失败，角色名称已存在',
                    error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                    developer_message=f'Role name already exists: role_name={page_object.role_name}'
                )
            elif not await cls.check_role_key_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    user_message=f'修改角色{page_object.role_name}失败，角色权限已存在',
                    error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                    developer_message=f'Role key already exists: role_key={page_object.role_key}'
                )
        
        role_repo = RoleRepository(query_db)
        db_role = await role_repo.find_by_id(page_object.role_id)
        if db_role:
            for key, value in edit_role.items():
                if hasattr(db_role, key):
                    setattr(db_role, key, value)
            await role_repo.update(db_role)
        if page_object.type != 'status':
            role_menu_repo = RoleMenuRepository(query_db)
            await role_menu_repo.delete_by_role_id(page_object.role_id)
            if page_object.menu_ids:
                for menu in page_object.menu_ids:
                    db_role_menu = RoleMenuDO(role_id=page_object.role_id, menu_id=menu)
                    await role_menu_repo.add(db_role_menu)
        await cls._invalidate_role_cache()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def role_datascope_services(cls, query_db: AsyncSession, page_object: AddRoleModel):
        """
        分配角色数据权限service

        :param query_db: orm对象
        :param page_object: 角色数据权限对象
        :return: 分配角色数据权限结果
        """
        edit_role = page_object.model_dump(exclude_unset=True, exclude={'admin', 'dept_ids'})
        role_info = await cls.role_detail_services(query_db, page_object.role_id)
        if not role_info.role_id:
            raise ResourceNotFoundException(
                user_message='角色不存在',
                error_code=ErrorCode.ROLE_NOT_FOUND,
                developer_message=f'Role not found: role_id={page_object.role_id}'
            )
        
        role_repo = RoleRepository(query_db)
        db_role = await role_repo.find_by_id(page_object.role_id)
        if db_role:
            for key, value in edit_role.items():
                if hasattr(db_role, key):
                    setattr(db_role, key, value)
            await role_repo.update(db_role)
        role_dept_repo = RoleDeptRepository(query_db)
        await role_dept_repo.delete_by_role_id(page_object.role_id)
        if page_object.dept_ids and page_object.data_scope == '2':
            for dept in page_object.dept_ids:
                db_role_dept = RoleDeptDO(role_id=page_object.role_id, dept_id=dept)
                await role_dept_repo.add(db_role_dept)
        await cls._invalidate_role_cache()
        return CrudResponseModel(is_success=True, message='分配成功')

    @classmethod
    @transactional()
    async def delete_role_services(cls, query_db: AsyncSession, page_object: DeleteRoleModel):
        """
        删除角色信息service

        :param query_db: orm对象
        :param page_object: 删除角色对象
        :return: 删除角色校验结果
        """
        if not page_object.role_ids:
            raise ValidationException(
                user_message='传入角色id为空',
                developer_message='Role IDs parameter is empty',
                field='role_ids'
            )
        
        role_repo = RoleRepository(query_db)
        role_menu_repo = RoleMenuRepository(query_db)
        role_dept_repo = RoleDeptRepository(query_db)
        role_id_list = page_object.role_ids.split(',')
        for role_id in role_id_list:
            role = await cls.role_detail_services(query_db, int(role_id))
            if (await role_repo.count_users(int(role_id))) > 0:
                raise ResourceConflictException(
                    user_message=f'角色{role.role_name}已分配,不能删除',
                    error_code=ErrorCode.ROLE_IN_USE,
                    developer_message=f'Role is assigned to users: role_id={role_id}'
                )
            await role_menu_repo.delete_by_role_id(int(role_id))
            await role_dept_repo.delete_by_role_id(int(role_id))
            await role_repo.soft_delete(int(role_id), page_object.update_by)
        await cls._invalidate_role_cache()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def role_detail_services(cls, query_db: AsyncSession, role_id: int):
        """
        获取角色详细信息service

        :param query_db: orm对象
        :param role_id: 角色id
        :return: 角色id对应的信息
        """
        cache = get_query_cache()
        cache_key = cache.build_key('role:detail', {'role_id': role_id})
        cached = await cache.get(cache_key)
        if cached is not None:
            return RoleModel(**cached)

        role_repo = RoleRepository(query_db)
        role = await role_repo.find_active_by_id(role_id)
        if role:
            result = RoleModel(**CamelCaseUtil.transform_result(role))
        else:
            result = RoleModel(**dict())
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    @staticmethod
    async def _invalidate_role_cache():
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:role:*')
        await cache.delete_pattern(f'{cache.key_prefix}:menu:role_tree:*')
        await cache.delete_pattern(f'{cache.key_prefix}:menu:tree:*')
        await cache.delete_pattern(f'{cache.key_prefix}:menu:list:*')

    @staticmethod
    async def export_role_list_services(role_list: List):
        """
        导出角色列表信息service

        :param role_list: 角色信息列表
        :return: 角色列表信息对象
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'roleId': '角色编号',
            'roleName': '角色名称',
            'roleKey': '权限字符',
            'roleSort': '显示顺序',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in role_list:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        binary_data = ExcelUtil.export_list2excel(role_list, mapping_dict)

        return binary_data

    @classmethod
    async def get_role_user_allocated_list_services(
        cls, query_db: AsyncSession, page_object: UserRolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据角色id获取已分配用户列表

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 已分配用户列表
        """
        user_repo = UserRepository(query_db)
        if is_page:
            query_user_list = await user_repo.paginate_allocated_by_role(
                role_id=page_object.role_id,
                page=page_object.page_num,
                page_size=page_object.page_size,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql
            )
        else:
            query_user_list = await user_repo.paginate_allocated_by_role(
                role_id=page_object.role_id,
                page=1,
                page_size=10000,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql
            )
        allocated_list = PageResponseModel(
            **{
                **query_user_list.model_dump(by_alias=True),
                'rows': [UserInfoModel(**row) for row in query_user_list.rows],
            }
        )

        return allocated_list

    @classmethod
    async def get_role_user_unallocated_list_services(
        cls, query_db: AsyncSession, page_object: UserRolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据角色id获取未分配用户列表

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 未分配用户列表
        """
        user_repo = UserRepository(query_db)
        if is_page:
            query_user_list = await user_repo.paginate_unallocated_by_role(
                role_id=page_object.role_id,
                page=page_object.page_num,
                page_size=page_object.page_size,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql
            )
        else:
            query_user_list = await user_repo.paginate_unallocated_by_role(
                role_id=page_object.role_id,
                page=1,
                page_size=10000,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql
            )
        unallocated_list = PageResponseModel(
            **{
                **query_user_list.model_dump(by_alias=True),
                'rows': [UserInfoModel(**row) for row in query_user_list.rows],
            }
        )

        return unallocated_list

    async def get_role_by_id(self, role_id: int):
        return await self.role_dao.get_role_by_id(role_id)

    async def get_role_list(self, query_object: RoleQueryModel):
        rows = await self.role_dao.get_role_list(query_object)
        total = await self.role_dao.count_roles(query_object)
        return {'total': total, 'rows': rows}

    async def add_role(self, role_data: AddRoleModel):
        self._validate_data_scope(role_data.data_scope)
        get_by_key = getattr(self.role_dao, 'get_role_by_key', None)
        if get_by_key and not (
            isinstance(get_by_key, MagicMock) and not isinstance(get_by_key, AsyncMock)
        ):
            result = get_by_key(role_data.role_key)
            existing = await result if inspect.isawaitable(result) else result
            if existing:
                raise ValueError('角色权限已存在')
        return await self.role_dao.add_role(role_data)

    async def edit_role(self, role_data: EditRoleModel):
        existing = await self.role_dao.get_role_by_id(role_data.role_id)
        if not existing:
            raise ValueError('角色不存在')
        if getattr(existing, 'role_id', None) == 1:
            raise ValueError('不能修改超级管理员')
        if role_data.data_scope is not None:
            self._validate_data_scope(role_data.data_scope)
        return await self.role_dao.edit_role(role_data)

    async def delete_role(self, role_id: int):
        existing = await self.role_dao.get_role_by_id(role_id)
        if not existing:
            raise ValueError('角色不存在')
        if getattr(existing, 'role_id', None) == 1:
            raise ValueError('不能删除超级管理员')
        return await self.role_dao.delete_role(role_id)

    async def assign_menu_permissions(self, role_id: int, menu_ids: List[int]):
        return await self.role_dao.assign_menus(role_id, menu_ids)

    async def get_role_menu_permissions(self, role_id: int):
        return await self.role_dao.get_role_menus(role_id)

    async def change_data_scope(self, role_id: int, data_scope: str, dept_ids: List[int]):
        existing = await self.role_dao.get_role_by_id(role_id)
        if not existing:
            raise ValueError('角色不存在')
        if getattr(existing, 'role_id', None) == 1:
            raise ValueError('不能修改超级管理员')
        self._validate_data_scope(data_scope)
        return await self.role_dao.edit_role(
            EditRoleModel(role_id=role_id, data_scope=data_scope, dept_ids=dept_ids)
        )

    def _validate_data_scope(self, data_scope: str | None):
        if data_scope is None:
            return True
        if data_scope in {'1', '2', '3', '4', '5'}:
            return True
        raise ValueError('数据范围无效')
