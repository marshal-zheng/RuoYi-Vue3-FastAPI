import io
import pandas as pd
from datetime import datetime
from fastapi import Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Union
from config.constant import CommonConstant
from exceptions.exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    AuthException,
)
from config.error_codes import ErrorCode
from module_admin.entity.do.user_do import UserDO, UserPostDO, UserRoleDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.transaction_manager import transactional
from module_admin.entity.vo.post_vo import PostPageQueryModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
    CrudUserRoleModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    ResetUserModel,
    SelectedRoleModel,
    UserDetailModel,
    UserInfoModel,
    UserModel,
    UserPageQueryModel,
    UserProfileModel,
    UserRoleModel,
    UserRoleQueryModel,
    UserRoleResponseModel,
)
from module_admin.repository import UserRepository, UserRoleRepository, UserPostRepository
from module_admin.service.config_service import ConfigService
from module_admin.service.dept_service import DeptService
from module_admin.service.post_service import PostService
from module_admin.service.role_service import RoleService
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.page_util import PageResponseModel
from utils.pwd_util import PwdUtil


class UserService:
    """
    用户管理模块服务层
    """

    @classmethod
    async def get_user_list_services(
        cls, query_db: AsyncSession, query_object: UserPageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        获取用户列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        user_repo = UserRepository(query_db)
        if is_page:
            query_result = await user_repo.paginate_with_dept(
                page=query_object.page_num,
                page_size=query_object.page_size,
                user_id=query_object.user_id,
                user_name=query_object.user_name,
                status=query_object.status,
                phonenumber=query_object.phonenumber,
                dept_id=query_object.dept_id,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql
            )
            user_list_result = PageResponseModel(
                **{
                    **query_result.model_dump(by_alias=True),
                    'rows': [{**row[0], 'dept': row[1]} for row in query_result.rows],
                }
            )
        else:
            query_result = await user_repo.paginate_with_dept(
                page=1,
                page_size=10000,
                user_id=query_object.user_id,
                user_name=query_object.user_name,
                status=query_object.status,
                phonenumber=query_object.phonenumber,
                dept_id=query_object.dept_id,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql
            )
            user_list_result = []
            rows = query_result.rows if hasattr(query_result, 'rows') else query_result
            if rows:
                user_list_result = [{**row[0], 'dept': row[1]} for row in rows]

        return user_list_result

    @classmethod
    async def check_user_allowed_services(cls, check_user: UserModel):
        """
        校验用户是否允许操作service

        :param check_user: 用户信息
        :return: 校验结果
        """
        if check_user.admin:
            raise AuthException(
                error_code=ErrorCode.ADMIN_USER_OPERATION_FORBIDDEN,
                message='不允许操作超级管理员用户'
            )
        else:
            return CrudResponseModel(is_success=True, message='校验通过')

    @classmethod
    async def check_user_data_scope_services(cls, query_db: AsyncSession, user_id: int, data_scope_sql: str):
        """
        校验用户数据权限service

        :param query_db: orm对象
        :param user_id: 用户id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        user_repo = UserRepository(query_db)
        users = await user_repo.paginate_with_dept(
            page=1,
            page_size=10000,
            user_id=user_id,
            data_scope_sql=data_scope_sql
        )
        rows = users.rows if hasattr(users, 'rows') else users
        if rows:
            return CrudResponseModel(is_success=True, message='校验通过')
        else:
            raise AuthException(
                error_code=ErrorCode.DATA_SCOPE_PERMISSION_DENIED,
                message='没有权限访问用户数据'
            )

    @classmethod
    async def check_user_name_unique_services(cls, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = UserRepository(query_db)
        return await cls._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_username,
            value=page_object.user_name,
        )

    @classmethod
    async def check_phonenumber_unique_services(cls, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户手机号是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = UserRepository(query_db)
        return await cls._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_phone,
            value=page_object.phonenumber,
        )

    @classmethod
    async def check_email_unique_services(cls, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户邮箱是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = UserRepository(query_db)
        return await cls._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_email,
            value=page_object.email,
        )

    @classmethod
    async def check_id_card_unique_services(cls, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户身份证号是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = UserRepository(query_db)
        return await cls._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_id_card,
            value=page_object.id_card,
        )

    @classmethod
    async def _check_unique(cls, page_object: UserModel, finder, value):
        user_id = -1 if page_object.user_id is None else page_object.user_id
        if not value:
            return CommonConstant.UNIQUE
        user = await finder(value)
        if user and user.user_id != user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    @transactional()
    async def add_user_services(cls, query_db: AsyncSession, page_object: AddUserModel):
        """
        新增用户信息service

        :param query_db: orm对象
        :param page_object: 新增用户对象
        :return: 新增用户校验结果
        """
        add_user = UserModel(**page_object.model_dump(by_alias=True))
        if not await cls.check_user_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_NAME_ALREADY_EXISTS,
                message=f'新增用户{page_object.user_name}失败，登录账号已存在'
            )
        elif page_object.phonenumber and not await cls.check_phonenumber_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
                message=f'新增用户{page_object.user_name}失败，手机号码已存在'
            )
        elif page_object.email and not await cls.check_email_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                message=f'新增用户{page_object.user_name}失败，邮箱账号已存在'
            )
        elif page_object.id_card and not await cls.check_id_card_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                message=f'新增用户{page_object.user_name}失败，身份证号已存在'
            )
        
        user_repo = UserRepository(query_db)
        db_user = UserDO(**add_user.model_dump(exclude={'admin'}))
        add_result = await user_repo.add(db_user)
        user_id = add_result.user_id
        if page_object.role_ids:
            user_role_repo = UserRoleRepository(query_db)
            for role in page_object.role_ids:
                db_user_role = UserRoleDO(user_id=user_id, role_id=role)
                await user_role_repo.add(db_user_role)
        if page_object.post_ids:
            user_post_repo = UserPostRepository(query_db)
            for post in page_object.post_ids:
                db_user_post = UserPostDO(user_id=user_id, post_id=post)
                await user_post_repo.add(db_user_post)
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_user_services(cls, query_db: AsyncSession, page_object: EditUserModel):
        """
        编辑用户信息service

        :param query_db: orm对象
        :param page_object: 编辑用户对象
        :return: 编辑用户校验结果
        """
        edit_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        if page_object.type != 'status' and page_object.type != 'avatar' and page_object.type != 'pwd':
            del edit_user['role_ids']
            del edit_user['post_ids']
            del edit_user['role']
        if page_object.type == 'status' or page_object.type == 'avatar' or page_object.type == 'pwd':
            del edit_user['type']
        user_info = await cls.user_detail_services(query_db, edit_user.get('user_id'))
        if not (user_info.data and user_info.data.user_id):
            raise ResourceNotFoundException(
                error_code=ErrorCode.USER_NOT_FOUND,
                message='用户不存在'
            )
        
        if page_object.type != 'status' and page_object.type != 'avatar' and page_object.type != 'pwd':
            if not await cls.check_user_name_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    error_code=ErrorCode.USER_NAME_ALREADY_EXISTS,
                    message=f'修改用户{page_object.user_name}失败，登录账号已存在'
                )
            elif page_object.phonenumber and not await cls.check_phonenumber_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
                    message=f'修改用户{page_object.user_name}失败，手机号码已存在'
                )
            elif page_object.email and not await cls.check_email_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                    message=f'修改用户{page_object.user_name}失败，邮箱账号已存在'
                )
            elif page_object.id_card and not await cls.check_id_card_unique_services(query_db, page_object):
                raise ResourceConflictException(
                    error_code=ErrorCode.RESOURCE_CONFLICT,
                    message=f'修改用户{page_object.user_name}失败，身份证号已存在'
                )
        
        user_repo = UserRepository(query_db)
        db_user = await user_repo.get_by_id(page_object.user_id)
        if db_user:
            for key, value in edit_user.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            await user_repo.update(db_user)
        if page_object.type != 'status' and page_object.type != 'avatar' and page_object.type != 'pwd':
            user_role_repo = UserRoleRepository(query_db)
            user_post_repo = UserPostRepository(query_db)
            await user_role_repo.delete_by_user_id(page_object.user_id)
            await user_post_repo.delete_by_user_id(page_object.user_id)
            if page_object.role_ids:
                for role in page_object.role_ids:
                    db_user_role = UserRoleDO(user_id=page_object.user_id, role_id=role)
                    await user_role_repo.add(db_user_role)
            if page_object.post_ids:
                for post in page_object.post_ids:
                    db_user_post = UserPostDO(user_id=page_object.user_id, post_id=post)
                    await user_post_repo.add(db_user_post)
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def delete_user_services(cls, query_db: AsyncSession, page_object: DeleteUserModel):
        """
        删除用户信息service

        :param query_db: orm对象
        :param page_object: 删除用户对象
        :return: 删除用户校验结果
        """
        if not page_object.user_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='user_ids',
                message='传入用户id为空'
            )
        
        user_repo = UserRepository(query_db)
        user_role_repo = UserRoleRepository(query_db)
        user_post_repo = UserPostRepository(query_db)
        user_id_list = page_object.user_ids.split(',')
        for user_id in user_id_list:
            await user_role_repo.delete_by_user_id(int(user_id))
            await user_post_repo.delete_by_user_id(int(user_id))
            await user_repo.soft_delete(int(user_id), page_object.update_by)
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def user_detail_services(cls, query_db: AsyncSession, user_id: Union[int, str]):
        """
        获取用户详细信息service

        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        posts = await PostService.get_post_list_services(query_db, PostPageQueryModel(**{}), is_page=False)
        roles = await RoleService.get_role_select_option_services(query_db)
        if user_id != '':
            user_repo = UserRepository(query_db)
            query_user = await user_repo.get_user_with_relations(user_id=user_id)
            if not query_user or not query_user.get('user_basic_info'):
                # 用户不存在，抛出 404 异常
                from exceptions.exception import ResourceNotFoundException
                from config.error_codes import ErrorCode
                raise ResourceNotFoundException(
                    user_message="用户不存在",
                    error_code=ErrorCode.USER_NOT_FOUND,
                    developer_message=f"User with id={user_id} not found in database"
                )
            user_post_info = query_user.get('user_post_info') or []
            user_role_info = query_user.get('user_role_info') or []
            post_ids = ','.join([str(row.post_id) for row in user_post_info])
            post_ids_list = [row.post_id for row in user_post_info]
            role_ids = ','.join([str(row.role_id) for row in user_role_info])
            role_ids_list = [row.role_id for row in user_role_info]

            return UserDetailModel(
                data=UserInfoModel(
                    **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                    postIds=post_ids,
                    roleIds=role_ids,
                    dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                    role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
                ),
                postIds=post_ids_list,
                posts=posts,
                roleIds=role_ids_list,
                roles=roles,
            )

        return UserDetailModel(posts=posts, roles=roles)

    @classmethod
    async def user_profile_services(cls, query_db: AsyncSession, user_id: int):
        """
        获取用户个人详细信息service

        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        user_repo = UserRepository(query_db)
        query_user = await user_repo.get_user_with_relations(user_id=user_id)
        if not query_user or not query_user.get('user_basic_info'):
            return UserProfileModel(data=None, postGroup='', roleGroup='')
        user_post_info = query_user.get('user_post_info') or []
        user_role_info = query_user.get('user_role_info') or []
        post_ids = ','.join([str(row.post_id) for row in user_post_info])
        post_group = ','.join([row.post_name for row in user_post_info])
        role_ids = ','.join([str(row.role_id) for row in user_role_info])
        role_group = ','.join([row.role_name for row in user_role_info])

        return UserProfileModel(
            data=UserInfoModel(
                **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                postIds=post_ids,
                roleIds=role_ids,
                dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
            ),
            postGroup=post_group,
            roleGroup=role_group,
        )

    @classmethod
    @transactional()
    async def reset_user_services(cls, query_db: AsyncSession, page_object: ResetUserModel):
        """
        重置用户密码service

        :param query_db: orm对象
        :param page_object: 重置用户对象
        :return: 重置用户校验结果
        """
        reset_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        user_repo = UserRepository(query_db)
        if page_object.old_password:
            user = (await user_repo.get_user_with_relations(user_id=page_object.user_id)).get('user_basic_info')
            if not PwdUtil.verify_password(page_object.old_password, user.password):
                raise AuthException(
                    error_code=ErrorCode.INVALID_PASSWORD,
                    message='修改密码失败，旧密码错误'
                )
            elif PwdUtil.verify_password(page_object.password, user.password):
                raise ValidationException(
                    error_code=ErrorCode.INVALID_INPUT,
                    field='password',
                    message='新密码不能与旧密码相同'
                )
            else:
                del reset_user['old_password']
        if page_object.sms_code and page_object.session_id:
            del reset_user['sms_code']
            del reset_user['session_id']
        
        reset_user['password'] = PwdUtil.get_password_hash(page_object.password)
        db_user = await user_repo.get_by_id(page_object.user_id)
        if db_user:
            for key, value in reset_user.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            await user_repo.update(db_user)
        return CrudResponseModel(is_success=True, message='重置成功')

    @classmethod
    @transactional()
    async def batch_import_user_services(
        cls,
        request: Request,
        query_db: AsyncSession,
        file: UploadFile,
        update_support: bool,
        current_user: CurrentUserModel,
        user_data_scope_sql: str,
        dept_data_scope_sql: str,
    ):
        """
        批量导入用户service

        :param request: Request对象
        :param query_db: orm对象
        :param file: 用户导入文件对象
        :param update_support: 用户存在时是否更新
        :param current_user: 当前用户对象
        :param user_data_scope_sql: 用户数据权限sql
        :param dept_data_scope_sql: 部门数据权限sql
        :return: 批量导入用户结果
        """
        header_dict = {
            '部门编号': 'dept_id',
            '登录名称': 'user_name',
            '用户名称': 'nick_name',
            '用户邮箱': 'email',
            '手机号码': 'phonenumber',
            '用户性别': 'sex',
            '帐号状态': 'status',
        }
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        await file.close()
        df.rename(columns=header_dict, inplace=True)
        add_error_result = []
        count = 0
        user_repo = UserRepository(query_db)
        
        for index, row in df.iterrows():
            count = count + 1
            if row['sex'] == '男':
                row['sex'] = '0'
            if row['sex'] == '女':
                row['sex'] = '1'
            if row['sex'] == '未知':
                row['sex'] = '2'
            if row['status'] == '正常':
                row['status'] = '0'
            if row['status'] == '停用':
                row['status'] = '1'
            add_user = UserModel(
                deptId=row['dept_id'],
                userName=row['user_name'],
                password=PwdUtil.get_password_hash(
                    await ConfigService.query_config_list_from_cache_services(
                        request.app.state.redis, 'sys.user.initPassword'
                    )
                ),
                nickName=row['nick_name'],
                email=row['email'],
                phonenumber=str(row['phonenumber']),
                sex=row['sex'],
                status=row['status'],
                createBy=current_user.user.user_name,
                createTime=datetime.now(),
                updateBy=current_user.user.user_name,
                updateTime=datetime.now(),
            )
            user_info = await user_repo.find_by_username(row['user_name'])
            if user_info:
                if update_support:
                    edit_user_model = UserModel(
                        userId=user_info.user_id,
                        deptId=row['dept_id'],
                        userName=row['user_name'],
                        nickName=row['nick_name'],
                        email=row['email'],
                        phonenumber=str(row['phonenumber']),
                        sex=row['sex'],
                        status=row['status'],
                        updateBy=current_user.user.user_name,
                        updateTime=datetime.now(),
                    )
                    edit_user_model.validate_fields()
                    await cls.check_user_allowed_services(edit_user_model)
                    if not current_user.user.admin:
                        await cls.check_user_data_scope_services(
                            query_db, edit_user_model.user_id, user_data_scope_sql
                        )
                        await DeptService.check_dept_data_scope_services(
                            query_db, edit_user_model.dept_id, dept_data_scope_sql
                        )
                    edit_user = edit_user_model.model_dump(exclude_unset=True)
                    db_user = await user_repo.get_by_id(user_info.user_id)
                    if db_user:
                        for key, value in edit_user.items():
                            if hasattr(db_user, key):
                                setattr(db_user, key, value)
                        await user_repo.update(db_user)
                else:
                    add_error_result.append(f"{count}.用户账号{row['user_name']}已存在")
            else:
                add_user.validate_fields()
                if not current_user.user.admin:
                    await DeptService.check_dept_data_scope_services(
                        query_db, add_user.dept_id, dept_data_scope_sql
                    )
                db_user = UserDO(**add_user.model_dump(exclude={'admin'}))
                await user_repo.add(db_user)
        return CrudResponseModel(is_success=True, message='\n'.join(add_error_result))

    @staticmethod
    async def get_user_import_template_services():
        """
        获取用户导入模板service

        :return: 用户导入模板excel的二进制数据
        """
        header_list = ['部门编号', '登录名称', '用户名称', '用户邮箱', '手机号码', '用户性别', '帐号状态']
        selector_header_list = ['用户性别', '帐号状态']
        option_list = [{'用户性别': ['男', '女', '未知']}, {'帐号状态': ['正常', '停用']}]
        binary_data = ExcelUtil.get_excel_template(
            header_list=header_list, selector_header_list=selector_header_list, option_list=option_list
        )

        return binary_data

    @staticmethod
    async def export_user_list_services(user_list: List):
        """
        导出用户信息service

        :param user_list: 用户信息列表
        :return: 用户信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'userId': '用户编号',
            'userName': '用户名称',
            'nickName': '用户昵称',
            'deptName': '部门',
            'email': '邮箱地址',
            'phonenumber': '手机号码',
            'sex': '性别',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in user_list:
            item['deptName'] = item.get('dept').get('deptName')
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('sex') == '0':
                item['sex'] = '男'
            elif item.get('sex') == '1':
                item['sex'] = '女'
            else:
                item['sex'] = '未知'
        binary_data = ExcelUtil.export_list2excel(user_list, mapping_dict)

        return binary_data

    @classmethod
    async def get_user_role_allocated_list_services(cls, query_db: AsyncSession, page_object: UserRoleQueryModel):
        """
        根据用户id获取已分配角色列表

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 已分配角色列表
        """
        user_repo = UserRepository(query_db)
        query_user = await user_repo.get_user_with_relations(page_object.user_id)
        post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
        role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
        user = UserInfoModel(
            **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
            postIds=post_ids,
            roleIds=role_ids,
            dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
            role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
        )
        query_role_list = [
            SelectedRoleModel(**row) for row in await RoleService.get_role_select_option_services(query_db)
        ]
        for model_a in query_role_list:
            for model_b in user.role:
                if model_a.role_id == model_b.role_id:
                    model_a.flag = True
        result = UserRoleResponseModel(roles=query_role_list, user=user)

        return result

    @classmethod
    @transactional()
    async def add_user_role_services(cls, query_db: AsyncSession, page_object: CrudUserRoleModel):
        """
        新增用户关联角色信息service

        :param query_db: orm对象
        :param page_object: 新增用户关联角色对象
        :return: 新增用户关联角色校验结果
        """
        user_role_repo = UserRoleRepository(query_db)
        if page_object.user_id and page_object.role_ids:
            role_id_list = page_object.role_ids.split(',')
            await user_role_repo.delete_by_user_id(page_object.user_id)
            for role_id in role_id_list:
                db_user_role = UserRoleDO(user_id=page_object.user_id, role_id=int(role_id))
                await user_role_repo.add(db_user_role)
            return CrudResponseModel(is_success=True, message='分配成功')
        elif page_object.user_id and not page_object.role_ids:
            await user_role_repo.delete_by_user_id(page_object.user_id)
            return CrudResponseModel(is_success=True, message='分配成功')
        elif page_object.user_ids and page_object.role_id:
            user_id_list = page_object.user_ids.split(',')
            for user_id in user_id_list:
                user_role = await cls.detail_user_role_services(
                    query_db, UserRoleModel(userId=user_id, roleId=page_object.role_id)
                )
                if user_role:
                    continue
                else:
                    db_user_role = UserRoleDO(user_id=int(user_id), role_id=page_object.role_id)
                    await user_role_repo.add(db_user_role)
            return CrudResponseModel(is_success=True, message='新增成功')
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='不满足新增条件'
            )

    @classmethod
    @transactional()
    async def delete_user_role_services(cls, query_db: AsyncSession, page_object: CrudUserRoleModel):
        """
        删除用户关联角色信息service

        :param query_db: orm对象
        :param page_object: 删除用户关联角色对象
        :return: 删除用户关联角色校验结果
        """
        if not ((page_object.user_id and page_object.role_id) or (page_object.user_ids and page_object.role_id)):
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='传入用户角色关联信息为空'
            )
        
        user_role_repo = UserRoleRepository(query_db)
        if page_object.user_id and page_object.role_id:
            await user_role_repo.delete_by_user_and_role(page_object.user_id, page_object.role_id)
            return CrudResponseModel(is_success=True, message='删除成功')
        elif page_object.user_ids and page_object.role_id:
            user_id_list = page_object.user_ids.split(',')
            for user_id in user_id_list:
                await user_role_repo.delete_by_user_and_role(int(user_id), page_object.role_id)
            return CrudResponseModel(is_success=True, message='删除成功')
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='不满足删除条件'
            )

    @classmethod
    async def detail_user_role_services(cls, query_db: AsyncSession, page_object: UserRoleModel):
        """
        获取用户关联角色详细信息service

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 用户关联角色详细信息
        """
        user_role_repo = UserRoleRepository(query_db)
        user_role = await user_role_repo.find_by_user_and_role(page_object.user_id, page_object.role_id)

        return user_role
