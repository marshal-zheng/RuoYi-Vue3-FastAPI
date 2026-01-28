from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
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
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel
from module_admin.repository import DeptRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional
from utils.query_cache import get_query_cache


class DeptService:
    """
    部门管理模块服务层
    """

    @classmethod
    async def get_dept_tree_services(cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门树信息service

        :param query_db: orm对象
        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        cache = get_query_cache()
        cache_key = cache.build_key(
            'dept:tree',
            {
                'dept_name': page_object.dept_name,
                'data_scope': str(data_scope_sql),
            },
        )
        async def _load():
            dept_repo = DeptRepository(query_db)
            dept_list_result = await dept_repo.find_all_for_tree(
                dept_name=page_object.dept_name,
                data_scope_sql=data_scope_sql
            )
            return cls.list_to_tree(dept_list_result)

        return await cache.get_or_set(
            cache_key,
            _load,
            CacheConfig.query_cache_default_ttl,
            CacheConfig.query_cache_lock_enabled,
        )

    @classmethod
    async def get_dept_for_edit_option_services(
        cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str
    ):
        """
        获取部门编辑部门树信息service

        :param query_db: orm对象
        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        cache = get_query_cache()
        cache_key = cache.build_key(
            'dept:edit_option',
            {
                'exclude_dept_id': page_object.dept_id,
                'data_scope': str(data_scope_sql),
            },
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        dept_repo = DeptRepository(query_db)
        dept_list_result = await dept_repo.find_for_edit_option(
            exclude_dept_id=page_object.dept_id,
            data_scope_sql=data_scope_sql
        )
        result = CamelCaseUtil.transform_result(dept_list_result)
        await cache.set(cache_key, result, CacheConfig.query_cache_default_ttl)
        return result

    @classmethod
    async def get_dept_list_services(cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门列表信息service

        :param query_db: orm对象
        :param page_object: 分页查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门列表信息对象
        """
        cache = get_query_cache()
        cache_key = cache.build_key(
            'dept:list',
            {
                'dept_id': page_object.dept_id,
                'status': page_object.status,
                'dept_name': page_object.dept_name,
                'data_scope': str(data_scope_sql),
            },
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        dept_repo = DeptRepository(query_db)
        dept_list_result = await dept_repo.find_with_filters(
            dept_id=page_object.dept_id,
            status=page_object.status,
            dept_name=page_object.dept_name,
            data_scope_sql=data_scope_sql
        )
        result = CamelCaseUtil.transform_result(dept_list_result)
        await cache.set(cache_key, result, CacheConfig.query_cache_default_ttl)
        return result

    @classmethod
    async def check_dept_data_scope_services(cls, query_db: AsyncSession, dept_id: int, data_scope_sql: str):
        """
        校验部门是否有数据权限service

        :param query_db: orm对象
        :param dept_id: 部门id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        dept_repo = DeptRepository(query_db)
        depts = await dept_repo.find_with_filters(dept_id=dept_id, data_scope_sql=data_scope_sql)
        if depts:
            return CrudResponseModel(is_success=True, message='校验通过')
        else:
            raise PermissionException(
                user_message='没有权限访问部门数据',
                developer_message=f'No permission to access dept data: dept_id={dept_id}'
            )

    @classmethod
    async def check_dept_name_unique_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        校验部门名称是否唯一service

        :param query_db: orm对象
        :param page_object: 部门对象
        :return: 校验结果
        """
        dept_id = -1 if page_object.dept_id is None else page_object.dept_id
        dept_repo = DeptRepository(query_db)
        dept = await dept_repo.find_by_parent_and_name(
            parent_id=page_object.parent_id,
            dept_name=page_object.dept_name
        )
        if dept and dept.dept_id != dept_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    @transactional()
    async def add_dept_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        新增部门信息service

        :param query_db: orm对象
        :param page_object: 新增部门对象
        :return: 新增部门校验结果
        """
        if not await cls.check_dept_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'新增部门{page_object.dept_name}失败，部门名称已存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
                developer_message=f'Dept name already exists: parent_id={page_object.parent_id}, dept_name={page_object.dept_name}'
            )
        dept_repo = DeptRepository(query_db)
        parent_info = await dept_repo.find_by_id(page_object.parent_id)
        if parent_info.status != CommonConstant.DEPT_NORMAL:
            raise ValidationException(
                user_message=f'部门{parent_info.dept_name}停用，不允许新增',
                developer_message=f'Parent dept is disabled: parent_id={page_object.parent_id}, status={parent_info.status}',
                field='parent_id'
            )
        page_object.ancestors = f'{parent_info.ancestors},{page_object.parent_id}'
        db_dept = SysDept(**page_object.model_dump())
        await dept_repo.add(db_dept)
        await cls._invalidate_dept_cache()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_dept_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        编辑部门信息service

        :param query_db: orm对象
        :param page_object: 编辑部门对象
        :return: 编辑部门校验结果
        """
        dept_repo = DeptRepository(query_db)
        if not await cls.check_dept_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'修改部门{page_object.dept_name}失败，部门名称已存在',
                error_code=ErrorCode.DEPT_NOT_FOUND,
                developer_message=f'Dept name already exists: parent_id={page_object.parent_id}, dept_name={page_object.dept_name}'
            )
        elif page_object.dept_id == page_object.parent_id:
            raise ValidationException(
                user_message=f'修改部门{page_object.dept_name}失败，上级部门不能是自己',
                developer_message=f'Dept cannot be its own parent: dept_id={page_object.dept_id}',
                field='parent_id'
            )
        elif (
            page_object.status == CommonConstant.DEPT_DISABLE
            and (await dept_repo.count_normal_children(page_object.dept_id)) > 0
        ):
            raise ValidationException(
                user_message=f'修改部门{page_object.dept_name}失败，该部门包含未停用的子部门',
                developer_message=f'Dept has active children: dept_id={page_object.dept_id}',
                field='status'
            )
        new_parent_dept = await dept_repo.find_by_id(page_object.parent_id)
        old_dept = await dept_repo.find_by_id(page_object.dept_id)
        
        if new_parent_dept and old_dept:
            new_ancestors = f'{new_parent_dept.ancestors},{new_parent_dept.dept_id}'
            old_ancestors = old_dept.ancestors
            page_object.ancestors = new_ancestors
            await cls.update_dept_children(query_db, page_object.dept_id, new_ancestors, old_ancestors)
        edit_dept = page_object.model_dump(exclude_unset=True)
        dept = await dept_repo.find_by_id(page_object.dept_id)
        if dept:
            for key, value in edit_dept.items():
                if hasattr(dept, key):
                    setattr(dept, key, value)
            await dept_repo.update(dept)
        if (
            page_object.status == CommonConstant.DEPT_NORMAL
            and page_object.ancestors
            and page_object.ancestors != 0
        ):
            await cls.update_parent_dept_status_normal(query_db, page_object)
        await cls._invalidate_dept_cache()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def delete_dept_services(cls, query_db: AsyncSession, page_object: DeleteDeptModel):
        """
        删除部门信息service

        :param query_db: orm对象
        :param page_object: 删除部门对象
        :return: 删除部门校验结果
        """
        if not page_object.dept_ids:
            raise ValidationException(
                user_message='传入部门id为空',
                developer_message='Dept IDs parameter is empty',
                field='dept_ids'
            )
        
        dept_repo = DeptRepository(query_db)
        dept_id_list = page_object.dept_ids.split(',')
        for dept_id in dept_id_list:
            if (await dept_repo.count_direct_children(int(dept_id))) > 0:
                raise ResourceConflictException(
                    user_message='存在下级部门,不允许删除',
                    error_code=ErrorCode.DEPT_HAS_CHILDREN,
                    developer_message=f'Dept has children: dept_id={dept_id}'
                )
            elif (await dept_repo.count_users(int(dept_id))) > 0:
                raise ResourceConflictException(
                    user_message='部门存在用户,不允许删除',
                    error_code=ErrorCode.DEPT_HAS_USERS,
                    developer_message=f'Dept has users: dept_id={dept_id}'
                )
            await dept_repo.soft_delete(int(dept_id), page_object.update_by)
        await cls._invalidate_dept_cache()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def dept_detail_services(cls, query_db: AsyncSession, dept_id: int):
        """
        获取部门详细信息service

        :param query_db: orm对象
        :param dept_id: 部门id
        :return: 部门id对应的信息
        """
        cache = get_query_cache()
        cache_key = cache.build_key('dept:detail', {'dept_id': dept_id})
        cached = await cache.get(cache_key)
        if cached is not None:
            return DeptModel(**cached)

        dept_repo = DeptRepository(query_db)
        dept = await dept_repo.find_active_by_id(dept_id)
        if dept:
            result = DeptModel(**CamelCaseUtil.transform_result(dept))
        else:
            result = DeptModel(**dict())
        await cache.set(cache_key, result.model_dump(by_alias=True), CacheConfig.query_cache_default_ttl)
        return result

    @staticmethod
    async def export_dept_list_services(dept_list: List):
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
            if item.get('status') == '0':
                item['status'] = '正常'
            elif item.get('status') == '1':
                item['status'] = '停用'
        return ExcelUtil.export_list2excel(dept_list, mapping_dict)

    @staticmethod
    async def _invalidate_dept_cache():
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:dept:*')

    @classmethod
    def list_to_tree(cls, permission_list: list) -> list:
        """
        工具方法：根据部门列表信息生成树形嵌套数据

        :param permission_list: 部门列表信息
        :return: 部门树形嵌套数据
        """
        permission_list = [
            dict(id=item.dept_id, label=item.dept_name, parentId=item.parent_id) for item in permission_list
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

    @classmethod
    async def replace_first(cls, original_str: str, old_str: str, new_str: str):
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

    @classmethod
    async def update_parent_dept_status_normal(cls, query_db: AsyncSession, dept: DeptModel):
        """
        更新父部门状态为正常

        :param query_db: orm对象
        :param dept: 部门对象
        :return:
        """
        dept_id_list = dept.ancestors.split(',')
        dept_repo = DeptRepository(query_db)
        await dept_repo.update_status_normal(list(map(int, dept_id_list)))

    @classmethod
    async def update_dept_children(cls, query_db: AsyncSession, dept_id: int, new_ancestors: str, old_ancestors: str):
        """
        更新子部门信息

        :param query_db: orm对象
        :param dept_id: 部门id
        :param new_ancestors: 新的祖先
        :param old_ancestors: 旧的祖先
        :return:
        """
        dept_repo = DeptRepository(query_db)
        children = await dept_repo.find_children(dept_id)
        update_children = []
        for child in children:
            child_ancestors = await cls.replace_first(child.ancestors, old_ancestors, new_ancestors)
            update_children.append({'dept_id': child.dept_id, 'ancestors': child_ancestors})
        if children:
            await dept_repo.update_children_ancestors(update_children)
