from sqlalchemy.ext.asyncio import AsyncSession

from config.constant import CommonConstant
from config.error_codes import ErrorCode
from exceptions.exception import (
    PermissionException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel
from modules.system.infrastructure.dept_repository import DeptRepository  # noqa: F401 - test patch target
from ports import IDeptRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class DeptService:
    """
    部门管理模块服务层

    读取沿用当前数据库事务的可见性, 不发布跨事务的 Redis 结果缓存。
    """

    def __init__(self, dept_repo: IDeptRepository, query_db: AsyncSession):
        self.query_db = query_db
        self.dept_repo = dept_repo

    async def get_dept_tree_services(self, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门树信息service

        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        dept_list_result = await self.dept_repo.find_all_for_tree(
            dept_name=page_object.dept_name, data_scope_sql=data_scope_sql
        )
        return self.list_to_tree(dept_list_result)

    async def get_dept_for_edit_option_services(self, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门编辑部门树信息service

        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        dept_list_result = await self.dept_repo.find_for_edit_option(
            exclude_dept_id=page_object.dept_id, data_scope_sql=data_scope_sql
        )
        return CamelCaseUtil.transform_result(dept_list_result)

    async def get_dept_list_services(self, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门列表信息service

        :param page_object: 分页查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门列表信息对象
        """
        dept_list_result = await self.dept_repo.find_with_filters(
            dept_id=page_object.dept_id,
            status=page_object.status,
            dept_name=page_object.dept_name,
            data_scope_sql=data_scope_sql,
        )
        return CamelCaseUtil.transform_result(dept_list_result)

    async def check_dept_data_scope_services(self, dept_id: int, data_scope_sql: str):
        """
        校验部门是否有数据权限service

        :param dept_id: 部门id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        depts = await self.dept_repo.find_with_filters(dept_id=dept_id, data_scope_sql=data_scope_sql)
        if depts:
            return CrudResponseModel(is_success=True, message='校验通过')
        else:
            raise PermissionException(
                user_message='没有权限访问部门数据',
                developer_message=f'No permission to access dept data: dept_id={dept_id}',
            )

    async def check_dept_name_unique_services(self, page_object: DeptModel):
        """
        校验部门名称是否唯一service

        :param page_object: 部门对象
        :return: 校验结果
        """
        dept_id = -1 if page_object.dept_id is None else page_object.dept_id
        dept = await self.dept_repo.find_by_parent_and_name(
            parent_id=page_object.parent_id, dept_name=page_object.dept_name
        )
        if dept and dept.dept_id != dept_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    async def _resolve_parent_ancestors(
        self,
        parent_id: int,
        *,
        dept_id: int | None = None,
        enforce_data_scope: bool = False,
        data_scope_sql='True',
        creating: bool = False,
    ) -> str:
        """Validate placement against real parent links; 0 is the virtual root."""
        if parent_id == 0:
            if enforce_data_scope:
                raise PermissionException(user_message='没有权限将部门设置为根部门')
            return '0'

        parent = await self.dept_repo.find_by_id(parent_id)
        if parent is None:
            raise ResourceNotFoundException(
                user_message='上级部门不存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
                developer_message=f'Parent dept not found: parent_id={parent_id}',
            )
        if enforce_data_scope:
            await self.check_dept_data_scope_services(parent_id, data_scope_sql)
        if creating and parent.status != CommonConstant.DEPT_NORMAL:
            raise ValidationException(user_message=f'部门{parent.dept_name}停用，不允许新增', field='parent_id')

        # Stored ancestors are derived data, not a trustworthy cycle check.
        chain = []
        visited = {dept_id} if dept_id is not None else set()
        while parent is not None:
            if parent.dept_id in visited:
                raise ValidationException(
                    user_message='上级部门不能是自己或下级部门, 部门层级不能成环', field='parent_id'
                )
            visited.add(parent.dept_id)
            chain.append(parent.dept_id)
            if parent.parent_id == 0:
                break
            parent = await self.dept_repo.find_by_id(parent.parent_id)
            if parent is None:
                raise ResourceNotFoundException(user_message='上级部门不存在', error_code=ErrorCode.DEPT_NOT_FOUND)
        return ','.join(map(str, [0, *reversed(chain)]))

    async def _check_ancestor_activation_scope(self, ancestors: str | None, data_scope_sql):
        # Unchanged normal parents need no extra permission; only an actual status change does.
        for ancestor_id in (ancestors or '').split(','):
            if not ancestor_id or ancestor_id == '0':
                continue
            ancestor = await self.dept_repo.find_by_id(int(ancestor_id))
            if ancestor is None:
                raise ResourceNotFoundException(user_message='上级部门不存在', error_code=ErrorCode.DEPT_NOT_FOUND)
            if ancestor.status != CommonConstant.DEPT_NORMAL:
                await self.check_dept_data_scope_services(ancestor.dept_id, data_scope_sql)

    @transactional()
    async def add_dept_services(self, page_object: DeptModel, *, enforce_data_scope=False, data_scope_sql='True'):
        """Create with server-owned identity, ancestry, and deletion state."""
        ancestors = await self._resolve_parent_ancestors(
            page_object.parent_id,
            enforce_data_scope=enforce_data_scope,
            data_scope_sql=data_scope_sql,
            creating=True,
        )
        unique_query = DeptModel(parent_id=page_object.parent_id, dept_name=page_object.dept_name)
        if not await self.check_dept_name_unique_services(unique_query):
            raise ResourceConflictException(
                user_message=f'新增部门{page_object.dept_name}失败，部门名称已存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
            )
        fields = {
            'parent_id',
            'dept_name',
            'order_num',
            'leader',
            'phone',
            'email',
            'status',
            'create_by',
            'create_time',
            'update_by',
            'update_time',
        }
        db_dept = DeptDO(**page_object.model_dump(include=fields, exclude_unset=True), ancestors=ancestors)
        add_result = await self.dept_repo.add(db_dept)
        return CrudResponseModel(is_success=True, message='新增成功', result={'deptId': add_result.dept_id})

    @transactional()
    async def edit_dept_services(self, page_object: DeptModel, *, enforce_data_scope=False, data_scope_sql='True'):
        """Validate before updating the target and its subtree in one transaction."""
        dept = await self.dept_repo.find_by_id(page_object.dept_id)
        if dept is None:
            raise ResourceNotFoundException(user_message='部门不存在', error_code=ErrorCode.DEPT_NOT_FOUND)
        fields = {
            'parent_id',
            'dept_name',
            'order_num',
            'leader',
            'phone',
            'email',
            'status',
            'update_by',
            'update_time',
        }
        changes = page_object.model_dump(include=fields, exclude_unset=True)
        parent_id = changes.get('parent_id', dept.parent_id)
        if parent_id != dept.parent_id:
            changes['ancestors'] = await self._resolve_parent_ancestors(
                parent_id,
                dept_id=dept.dept_id,
                enforce_data_scope=enforce_data_scope,
                data_scope_sql=data_scope_sql,
            )
        elif parent_id == dept.dept_id:
            raise ValidationException(user_message='上级部门不能是自己', field='parent_id')

        effective = DeptModel(
            dept_id=dept.dept_id, parent_id=parent_id, dept_name=changes.get('dept_name', dept.dept_name)
        )
        if not await self.check_dept_name_unique_services(effective):
            raise ResourceConflictException(
                user_message=f'修改部门{effective.dept_name}失败，部门名称已存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
            )
        if changes.get('status') == CommonConstant.DEPT_DISABLE and await self.dept_repo.count_normal_children(
            dept.dept_id
        ):
            raise ValidationException(
                user_message=f'修改部门{effective.dept_name}失败，该部门包含未停用的子部门', field='status'
            )
        enable_ancestors = changes.get('status', dept.status) == CommonConstant.DEPT_NORMAL and (
            'ancestors' in changes or changes.get('status') == CommonConstant.DEPT_NORMAL
        )
        if enable_ancestors and enforce_data_scope:
            await self._check_ancestor_activation_scope(changes.get('ancestors', dept.ancestors), data_scope_sql)
        if 'ancestors' in changes:
            await self.update_dept_children(dept.dept_id, changes['ancestors'], dept.ancestors)
        for key, value in changes.items():
            setattr(dept, key, value)
        await self.dept_repo.update(dept)
        if enable_ancestors:
            await self.update_parent_dept_status_normal(DeptModel(ancestors=dept.ancestors))
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_dept_services(self, page_object: DeleteDeptModel):
        """
        删除部门信息service

        :param page_object: 删除部门对象
        :return: 删除部门校验结果
        """
        if not page_object.dept_ids:
            raise ValidationException(
                user_message='传入部门id为空', developer_message='Dept IDs parameter is empty', field='dept_ids'
            )

        dept_id_list = page_object.dept_ids.split(',')
        for dept_id in dept_id_list:
            if (await self.dept_repo.count_direct_children(int(dept_id))) > 0:
                raise ResourceConflictException(
                    user_message='存在下级部门,不允许删除',
                    error_code=ErrorCode.DEPT_HAS_CHILDREN,
                    developer_message=f'Dept has children: dept_id={dept_id}',
                )
            elif (await self.dept_repo.count_users(int(dept_id))) > 0:
                raise ResourceConflictException(
                    user_message='部门存在用户,不允许删除',
                    error_code=ErrorCode.DEPT_HAS_USERS,
                    developer_message=f'Dept has users: dept_id={dept_id}',
                )
            await self.dept_repo.soft_delete(int(dept_id), page_object.update_by)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def dept_detail_services(self, dept_id: int):
        """
        获取部门详细信息service

        :param dept_id: 部门id
        :return: 部门id对应的信息
        """
        dept = await self.dept_repo.find_active_by_id(dept_id)
        if dept:
            result = DeptModel(**CamelCaseUtil.transform_result(dept))
        else:
            raise ResourceNotFoundException(
                user_message='部门不存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
                developer_message=f'dept_id={dept_id} not found',
            )
        return result

    @staticmethod
    async def export_dept_list_services(dept_list: list):
        """
        导出部门信息service

        :param dept_list: 部门信息列表
        :return: 部门信息对应excel的二进制数据
        """
        mapping_dict = {
            'deptId': '部门编号',
            'parentId': '上级部门',
            'ancestors': '祖级列表',
            'deptName': '部门名称',
            'orderNum': '显示顺序',
            'leader': '负责人',
            'phone': '联系电话',
            'email': '邮箱',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
        }

        for item in dept_list:
            if item.get('status') == CommonConstant.DEPT_NORMAL:
                item['status'] = '正常'
            elif item.get('status') == CommonConstant.DEPT_DISABLE:
                item['status'] = '停用'
        return ExcelUtil.export_list2excel(dept_list, mapping_dict)

    @staticmethod
    def list_to_tree(permission_list: list) -> list:
        """
        工具方法：根据部门列表信息生成树形嵌套数据

        :param permission_list: 部门列表信息
        :return: 部门树形嵌套数据
        """
        permission_list = [
            {'id': item.dept_id, 'label': item.dept_name, 'parentId': item.parent_id} for item in permission_list
        ]
        # 转成id为key的字典
        mapping: dict = dict(zip([i['id'] for i in permission_list], permission_list, strict=False))

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

    @staticmethod
    async def replace_first(original_str: str, old_str: str, new_str: str):
        """
        工具方法：替换字符串

        :param original_str: 需要替换的原始字符串
        :param old_str: 用于匹配的字符串
        :param new_str: 替换的字符串
        :return: 替换后的字符串
        """
        if original_str.startswith(old_str):
            return original_str.replace(old_str, new_str, 1)
        else:
            return original_str

    async def update_parent_dept_status_normal(self, dept: DeptModel):
        """
        更新父部门状态为正常

        :param dept: 部门对象
        :return:
        """
        dept_id_list = [int(dept_id) for dept_id in (dept.ancestors or '').split(',') if dept_id and dept_id != '0']
        if dept_id_list:
            await self.dept_repo.update_status_normal(dept_id_list)

    async def update_dept_children(self, dept_id: int, new_ancestors: str, old_ancestors: str):
        """
        更新子部门信息

        :param dept_id: 部门id
        :param new_ancestors: 新的祖先
        :param old_ancestors: 旧的祖先
        :return:
        """
        children = await self.dept_repo.find_children(dept_id)
        update_children = []
        for child in children:
            child_ancestors = await self.replace_first(child.ancestors, old_ancestors, new_ancestors)
            update_children.append({'dept_id': child.dept_id, 'ancestors': child_ancestors})
        if children:
            await self.dept_repo.update_children_ancestors(update_children)
