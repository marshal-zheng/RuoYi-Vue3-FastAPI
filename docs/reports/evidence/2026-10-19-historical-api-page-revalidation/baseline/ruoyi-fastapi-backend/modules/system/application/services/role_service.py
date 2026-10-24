from sqlalchemy.ext.asyncio import AsyncSession

from config.constant import CommonConstant
from config.error_codes import ErrorCode
from exceptions.exception import (
    PermissionException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.do.role_do import RoleDeptDO, RoleDO, RoleMenuDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.role_vo import (
    AddRoleModel,
    DeleteRoleModel,
    RoleDeptQueryModel,
    RoleModel,
    RolePageQueryModel,
)
from module_admin.entity.vo.user_vo import UserInfoModel, UserRolePageQueryModel
from ports import IRoleDeptRepository, IRoleMenuRepository, IRoleRepository, IUserRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.page_util import PageResponseModel
from utils.transaction_manager import transactional


class RoleService:
    """
    角色管理模块服务层
    """

    def __init__(
        self,
        role_repo: IRoleRepository,
        role_menu_repo: IRoleMenuRepository,
        role_dept_repo: IRoleDeptRepository,
        user_repo: IUserRepository,
        query_db: AsyncSession,
    ):
        self.role_repo = role_repo
        self.role_menu_repo = role_menu_repo
        self.role_dept_repo = role_dept_repo
        self.user_repo = user_repo
        self.query_db = query_db

    async def get_role_select_option_services(self):
        """
        获取角色列表不分页信息service

        :return: 角色列表不分页信息对象
        """
        role_list_result = await self.role_repo.find_all_active()
        return CamelCaseUtil.transform_result(role_list_result)

    async def get_role_dept_tree_services(self, role_id: int):
        """
        根据角色id获取部门树信息service

        :param role_id: 角色id
        :return: 当前角色id的部门树信息对象
        """
        role_dept_list = await self.role_dept_repo.find_by_role_id(role_id)
        checked_keys = [row.dept_id for row in role_dept_list]
        return RoleDeptQueryModel(checkedKeys=checked_keys)

    async def get_role_list_services(
        self, query_object: RolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        获取角色列表信息service

        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 角色列表信息对象
        """
        if is_page:
            role_list_result = await self.role_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                role_id=query_object.role_id,
                role_name=query_object.role_name,
                role_key=query_object.role_key,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql,
            )
        else:
            role_list_result = await self.role_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                role_id=query_object.role_id,
                role_name=query_object.role_name,
                role_key=query_object.role_key,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql,
            )
            role_list_result = role_list_result.items if hasattr(role_list_result, 'items') else role_list_result

        return role_list_result

    async def check_role_allowed_services(self, check_role: RoleModel):
        """
        校验角色是否允许操作service

        :param check_role: 角色信息
        :return: 校验结果
        """
        if check_role.admin:
            raise PermissionException(
                user_message='不允许操作超级管理员角色',
                developer_message=f'Cannot operate on admin role: role_id={check_role.role_id}',
            )
        return CrudResponseModel(is_success=True, message='校验通过')

    async def check_role_data_scope_services(self, role_ids: str, data_scope_sql: str):
        """
        校验角色是否有数据权限service

        :param role_ids: 角色id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        role_id_list = role_ids.split(',') if role_ids else []
        if role_id_list:
            for role_id in role_id_list:
                roles = await self.role_repo.paginate_with_filters(
                    page=1,
                    page_size=10000,
                    role_id=int(role_id),
                    data_scope_sql=data_scope_sql,
                )
                roles = roles.items if hasattr(roles, 'items') else roles
                if roles:
                    continue
                raise PermissionException(
                    user_message='没有权限访问角色数据',
                    developer_message=f'No permission to access role data: role_id={role_id}',
                )

    async def check_role_name_unique_services(self, page_object: RoleModel):
        """
        校验角色名称是否唯一service

        :param page_object: 角色对象
        :return: 校验结果
        """
        role_id = -1 if page_object.role_id is None else page_object.role_id
        role = await self.role_repo.find_by_name(page_object.role_name)
        if role and role.role_id != role_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    async def check_role_key_unique_services(self, page_object: RoleModel):
        """
        校验角色权限字符是否唯一service

        :param page_object: 角色对象
        :return: 校验结果
        """
        role_id = -1 if page_object.role_id is None else page_object.role_id
        role = await self.role_repo.find_by_key(page_object.role_key)
        if role and role.role_id != role_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_role_services(self, page_object: AddRoleModel):
        """
        新增角色信息service

        :param page_object: 新增角色对象
        :return: 新增角色校验结果
        """
        add_role = RoleModel(**page_object.model_dump(by_alias=True))
        if not await self.check_role_name_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增角色{page_object.role_name}失败，角色名称已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Role name already exists: role_name={page_object.role_name}',
            )
        if not await self.check_role_key_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增角色{page_object.role_name}失败，角色权限已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Role key already exists: role_key={page_object.role_key}',
            )

        db_role = RoleDO(**add_role.model_dump(exclude={'admin'}))
        add_result = await self.role_repo.add(db_role)
        role_id = add_result.role_id
        if page_object.menu_ids:
            for menu in page_object.menu_ids:
                db_role_menu = RoleMenuDO(role_id=role_id, menu_id=menu)
                await self.role_menu_repo.add(db_role_menu)
        return CrudResponseModel(is_success=True, message='新增成功', result={'roleId': role_id})

    @transactional()
    async def edit_role_services(self, page_object: AddRoleModel):
        """
        编辑角色信息service

        :param page_object: 编辑角色对象
        :return: 编辑角色校验结果
        """
        writable = (
            {'status'}
            if page_object.type == 'status'
            else {'role_name', 'role_key', 'role_sort', 'status', 'menu_check_strictly', 'remark'}
        )
        edit_role = page_object.model_dump(
            exclude_unset=True, include=writable | {'role_id', 'update_by', 'update_time'}
        )
        await self.role_detail_services(edit_role.get('role_id'))

        if page_object.type != 'status':
            if not await self.check_role_name_unique_services(page_object):
                raise ResourceConflictException(
                    user_message=f'修改角色{page_object.role_name}失败，角色名称已存在',
                    error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                    developer_message=f'Role name already exists: role_name={page_object.role_name}',
                )
            if not await self.check_role_key_unique_services(page_object):
                raise ResourceConflictException(
                    user_message=f'修改角色{page_object.role_name}失败，角色权限已存在',
                    error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                    developer_message=f'Role key already exists: role_key={page_object.role_key}',
                )

        db_role = await self.role_repo.find_by_id(page_object.role_id)
        if db_role:
            for key, value in edit_role.items():
                if hasattr(db_role, key):
                    setattr(db_role, key, value)
            await self.role_repo.update(db_role)
        if page_object.type != 'status' and 'menu_ids' in page_object.model_fields_set:
            await self.role_menu_repo.delete_by_role_id(page_object.role_id)
            if page_object.menu_ids:
                for menu in page_object.menu_ids:
                    db_role_menu = RoleMenuDO(role_id=page_object.role_id, menu_id=menu)
                    await self.role_menu_repo.add(db_role_menu)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def role_datascope_services(self, page_object: AddRoleModel):
        """
        分配角色数据权限service

        :param page_object: 角色数据权限对象
        :return: 分配角色数据权限结果
        """
        edit_role = page_object.model_dump(
            exclude_unset=True,
            include={'role_id', 'data_scope', 'dept_check_strictly', 'update_by', 'update_time'},
        )
        await self.role_detail_services(page_object.role_id)

        db_role = await self.role_repo.find_by_id(page_object.role_id)
        if db_role:
            for key, value in edit_role.items():
                if hasattr(db_role, key):
                    setattr(db_role, key, value)
            await self.role_repo.update(db_role)
        if 'dept_ids' in page_object.model_fields_set:
            await self.role_dept_repo.delete_by_role_id(page_object.role_id)
            if page_object.dept_ids and db_role.data_scope == '2':
                for dept in page_object.dept_ids:
                    db_role_dept = RoleDeptDO(role_id=page_object.role_id, dept_id=dept)
                    await self.role_dept_repo.add(db_role_dept)
        return CrudResponseModel(is_success=True, message='分配成功')

    @transactional()
    async def delete_role_services(self, page_object: DeleteRoleModel):
        """
        删除角色信息service

        :param page_object: 删除角色对象
        :return: 删除角色校验结果
        """
        if not page_object.role_ids:
            raise ValidationException(
                user_message='传入角色id为空',
                developer_message='Role IDs parameter is empty',
                field='role_ids',
            )

        role_id_list = page_object.role_ids.split(',')
        for role_id in role_id_list:
            role_id_value = int(role_id)
            role = await self.role_detail_services(role_id_value)
            if (await self.role_repo.count_users(role_id_value)) > 0:
                raise ResourceConflictException(
                    user_message=f'角色{role.role_name}已分配,不能删除',
                    error_code=ErrorCode.ROLE_IN_USE,
                    developer_message=f'Role is assigned to users: role_id={role_id_value}',
                )
            await self.role_menu_repo.delete_by_role_id(role_id_value)
            await self.role_dept_repo.delete_by_role_id(role_id_value)
            await self.role_repo.soft_delete(role_id_value, page_object.update_by)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def role_detail_services(self, role_id: int):
        """
        获取角色详细信息service

        :param role_id: 角色id
        :return: 角色id对应的信息
        """
        # Management details must remain available after disabling a role.
        role = await self.role_repo.find_by_id(role_id)
        if role:
            result = RoleModel(**CamelCaseUtil.transform_result(role))
        else:
            raise ResourceNotFoundException(
                user_message='角色不存在',
                error_code=ErrorCode.ROLE_NOT_FOUND,
                developer_message=f'role_id={role_id} not found',
            )
        return result

    @staticmethod
    async def export_role_list_services(role_list: list):
        """
        导出角色列表信息service

        :param role_list: 角色信息列表
        :return: 角色列表信息对象
        """
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
            if item.get('status') == StatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        binary_data = ExcelUtil.export_list2excel(role_list, mapping_dict)

        return binary_data

    async def get_role_user_allocated_list_services(
        self,
        page_object: UserRolePageQueryModel,
        data_scope_sql: str,
        is_page: bool = False,
    ):
        """
        根据角色id获取已分配用户列表

        :param page_object: 用户关联角色对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 已分配用户列表
        """
        if is_page:
            query_user_list = await self.user_repo.paginate_allocated_by_role(
                role_id=page_object.role_id,
                page=page_object.page,
                page_size=page_object.page_size,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql,
            )
        else:
            query_user_list = await self.user_repo.paginate_allocated_by_role(
                role_id=page_object.role_id,
                page=1,
                page_size=10000,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql,
            )
        allocated_list = PageResponseModel(
            **{
                **query_user_list.model_dump(by_alias=True),
                'items': [UserInfoModel(**row[0], dept=row[1]) for row in query_user_list.items],
            }
        )

        return allocated_list

    async def get_role_user_unallocated_list_services(
        self,
        page_object: UserRolePageQueryModel,
        data_scope_sql: str,
        is_page: bool = False,
    ):
        """
        根据角色id获取未分配用户列表

        :param page_object: 用户关联角色对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 未分配用户列表
        """
        if is_page:
            query_user_list = await self.user_repo.paginate_unallocated_by_role(
                role_id=page_object.role_id,
                page=page_object.page,
                page_size=page_object.page_size,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql,
            )
        else:
            query_user_list = await self.user_repo.paginate_unallocated_by_role(
                role_id=page_object.role_id,
                page=1,
                page_size=10000,
                user_name=page_object.user_name,
                phonenumber=page_object.phonenumber,
                data_scope_sql=data_scope_sql,
            )
        unallocated_list = PageResponseModel(
            **{
                **query_user_list.model_dump(by_alias=True),
                'items': [UserInfoModel(**row[0], dept=row[1]) for row in query_user_list.items],
            }
        )

        return unallocated_list
