import io
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import Request, UploadFile
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
from module_admin.entity.do.user_do import UserDO, UserPostDO, UserRoleDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
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
    UserRoleQueryModel,
    UserRoleResponseModel,
)
from modules.system.infrastructure.role_repository import RoleRepository
from modules.system.infrastructure.user_post_repository import UserPostRepository
from modules.system.infrastructure.user_repository import UserRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository
from ports import IConfigService, IDeptService, IUserPostRepository, IUserRepository, IUserRoleRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.page_util import PageResponseModel
from utils.pwd_util import PwdUtil
from utils.transaction_manager import transactional


def _normalize_user_import_row(row) -> dict[str, Any]:
    normalized = dict(row)
    sex_map = {'男': '0', '女': '1', '未知': '2'}
    status_map = {'正常': StatusEnum.NORMAL.value, '停用': StatusEnum.DISABLED.value}
    normalized['sex'] = sex_map.get(normalized.get('sex'), normalized.get('sex'))
    normalized['status'] = status_map.get(normalized.get('status'), normalized.get('status'))
    return normalized


def _build_import_success_result(
    *,
    row_number: int,
    user_name: str,
    action: str,
    item_id: int | str,
) -> dict[str, Any]:
    return {
        'itemId': item_id,
        'success': True,
        'rowNumber': row_number,
        'userName': user_name,
        'action': action,
    }


def _build_import_failure_result(
    *,
    row_number: int,
    user_name: str,
    item_id: int | str,
    exc: Exception,
) -> dict[str, Any]:
    return {
        'itemId': item_id,
        'success': False,
        'rowNumber': row_number,
        'userName': user_name or None,
        'error': {
            'errorCode': getattr(exc, 'error_code', None),
            'title': '导入失败',
            'detail': getattr(exc, 'user_message', None) or str(exc) or '用户导入失败',
        },
    }


class UserService:
    """
    用户管理模块服务层
    """

    def __init__(
        self,
        query_db: AsyncSession | None = None,
        config_service: IConfigService | None = None,
        dept_service: IDeptService | None = None,
        user_repo_factory: Callable[[AsyncSession], IUserRepository] | None = None,
        user_role_repo_factory: Callable[[AsyncSession], IUserRoleRepository] | None = None,
        user_post_repo_factory: Callable[[AsyncSession], IUserPostRepository] | None = None,
    ):
        self.query_db = query_db
        self.config_service = config_service
        self.dept_service = dept_service
        self._user_repo_factory = user_repo_factory or UserRepository
        self._user_role_repo_factory = user_role_repo_factory or UserRoleRepository
        self._user_post_repo_factory = user_post_repo_factory or UserPostRepository

    def _require_config_service(self) -> IConfigService:
        if self.config_service is None:
            raise RuntimeError('config_service dependency is not configured')
        return self.config_service

    def _require_dept_service(self) -> IDeptService:
        if self.dept_service is None:
            raise RuntimeError('dept_service dependency is not configured')
        return self.dept_service

    def _user_repo(self, query_db: AsyncSession) -> IUserRepository:
        return self._user_repo_factory(query_db)

    def _user_role_repo(self, query_db: AsyncSession) -> IUserRoleRepository:
        return self._user_role_repo_factory(query_db)

    def _user_post_repo(self, query_db: AsyncSession) -> IUserPostRepository:
        return self._user_post_repo_factory(query_db)

    async def get_user_list_services(
        self, query_db: AsyncSession, query_object: UserPageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        获取用户列表信息service
        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        user_repo = self._user_repo(query_db)
        if is_page:
            query_result = await user_repo.paginate_with_dept(
                page=query_object.page,
                page_size=query_object.page_size,
                user_id=query_object.user_id,
                user_name=query_object.user_name,
                status=query_object.status,
                phonenumber=query_object.phonenumber,
                dept_id=query_object.dept_id,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                data_scope_sql=data_scope_sql,
            )
            user_list_result = PageResponseModel(
                **{
                    **query_result.model_dump(by_alias=True),
                    'items': [{**row[0], 'dept': row[1]} for row in query_result.items],
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
                data_scope_sql=data_scope_sql,
            )
            user_list_result = []
            items = query_result.items if hasattr(query_result, 'items') else query_result
            if items:
                user_list_result = [{**row[0], 'dept': row[1]} for row in items]
        return user_list_result

    async def check_user_allowed_services(self, check_user: UserModel):
        """
        校验用户是否允许操作service
        :param check_user: 用户信息
        :return: 校验结果
        """
        if check_user.admin:
            raise PermissionException(
                error_code=ErrorCode.ADMIN_USER_OPERATION_FORBIDDEN, user_message='不允许操作超级管理员用户'
            )
        else:
            return CrudResponseModel(is_success=True, message='校验通过')

    async def check_user_data_scope_services(self, query_db: AsyncSession, user_id: int, data_scope_sql: str):
        """
        校验用户数据权限service
        :param query_db: orm对象
        :param user_id: 用户id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        user_repo = self._user_repo(query_db)
        users = await user_repo.paginate_with_dept(
            page=1, page_size=10000, user_id=user_id, data_scope_sql=data_scope_sql
        )
        items = users.items if hasattr(users, 'items') else users
        if items:
            return CrudResponseModel(is_success=True, message='校验通过')
        else:
            raise PermissionException(
                error_code=ErrorCode.DATA_SCOPE_PERMISSION_DENIED, user_message='没有权限访问用户数据'
            )

    async def check_user_name_unique_services(self, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户名是否唯一service
        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = self._user_repo(query_db)
        return await self._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_username,
            value=page_object.user_name,
        )

    async def check_phonenumber_unique_services(self, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户手机号是否唯一service
        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = self._user_repo(query_db)
        return await self._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_phone,
            value=page_object.phonenumber,
        )

    async def check_email_unique_services(self, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户邮箱是否唯一service
        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = self._user_repo(query_db)
        return await self._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_email,
            value=page_object.email,
        )

    async def check_id_card_unique_services(self, query_db: AsyncSession, page_object: UserModel):
        """
        校验用户身份证号是否唯一service
        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_repo = self._user_repo(query_db)
        return await self._check_unique(
            page_object=page_object,
            finder=user_repo.find_by_id_card,
            value=page_object.id_card,
        )

    async def _check_unique(self, page_object: UserModel, finder, value):
        user_id = -1 if page_object.user_id is None else page_object.user_id
        if not value:
            return CommonConstant.UNIQUE
        user = await finder(value)
        if user and user.user_id != user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_user_services(self, query_db: AsyncSession, page_object: AddUserModel):
        """
        新增用户信息service
        :param query_db: orm对象
        :param page_object: 新增用户对象
        :return: 新增用户校验结果
        """
        add_user = UserModel(**page_object.model_dump(by_alias=True))
        if not await self.check_user_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_NAME_ALREADY_EXISTS,
                user_message=f'新增用户{page_object.user_name}失败，登录账号已存在',
            )
        elif page_object.phonenumber and not await self.check_phonenumber_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
                user_message=f'新增用户{page_object.user_name}失败，手机号码已存在',
            )
        elif page_object.email and not await self.check_email_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                user_message=f'新增用户{page_object.user_name}失败，邮箱账号已存在',
            )
        elif page_object.id_card and not await self.check_id_card_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                user_message=f'新增用户{page_object.user_name}失败，身份证号已存在',
            )
        user_repo = self._user_repo(query_db)
        db_user = UserDO(**add_user.model_dump(exclude={'admin'}))
        add_result = await user_repo.add(db_user)
        user_id = add_result.user_id
        if page_object.role_ids:
            user_role_repo = self._user_role_repo(query_db)
            for role in page_object.role_ids:
                db_user_role = UserRoleDO(user_id=user_id, role_id=role)
                await user_role_repo.add(db_user_role)
        if page_object.post_ids:
            user_post_repo = self._user_post_repo(query_db)
            for post in page_object.post_ids:
                db_user_post = UserPostDO(user_id=user_id, post_id=post)
                await user_post_repo.add(db_user_post)
        return CrudResponseModel(is_success=True, message='新增成功', result={'userId': user_id})

    async def _check_edit_user_uniqueness(self, query_db: AsyncSession, page_object: EditUserModel):
        if not await self.check_user_name_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_NAME_ALREADY_EXISTS,
                user_message=f'修改用户{page_object.user_name}失败，登录账号已存在',
            )
        elif page_object.phonenumber and not await self.check_phonenumber_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
                user_message=f'修改用户{page_object.user_name}失败，手机号码已存在',
            )
        elif page_object.email and not await self.check_email_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                user_message=f'修改用户{page_object.user_name}失败，邮箱账号已存在',
            )
        elif page_object.id_card and not await self.check_id_card_unique_services(query_db, page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                user_message=f'修改用户{page_object.user_name}失败，身份证号已存在',
            )

    @transactional()
    async def edit_user_services(self, query_db: AsyncSession, page_object: EditUserModel):
        """
        编辑用户信息service
        :param query_db: orm对象
        :param page_object: 编辑用户对象
        :return: 编辑用户校验结果
        关联字段未提供时保留, 提供空数组或 None 时清空。
        """
        is_general_edit = page_object.type not in {'status', 'avatar', 'pwd', 'login'}
        edit_fields = {
            'dept_id',
            'user_name',
            'nick_name',
            'email',
            'phonenumber',
            'id_card',
            'sex',
            'status',
            'remark',
        }
        operation_fields = {
            'profile': {'nick_name', 'email', 'phonenumber', 'sex'},
            'status': {'status'},
            'avatar': {'avatar'},
            'pwd': {'password'},
            'login': {'login_date', 'login_ip'},
        }
        writable = operation_fields.get(page_object.type, edit_fields) | {'update_by', 'update_time'}
        edit_user = page_object.model_dump(exclude_unset=True, include=writable)
        user_repo = self._user_repo(query_db)
        db_user = await user_repo.get_by_id(page_object.user_id)
        if not db_user:
            raise ResourceNotFoundException(error_code=ErrorCode.USER_NOT_FOUND, user_message='用户不存在')
        if is_general_edit:
            await self._check_edit_user_uniqueness(query_db, page_object)
        for key, value in edit_user.items():
            if hasattr(db_user, key):
                setattr(db_user, key, value)
        await user_repo.update(db_user)
        if page_object.type != 'profile' and is_general_edit and 'role_ids' in page_object.model_fields_set:
            user_role_repo = self._user_role_repo(query_db)
            await user_role_repo.delete_by_user_id(page_object.user_id)
            for role in page_object.role_ids or []:
                db_user_role = UserRoleDO(user_id=page_object.user_id, role_id=role)
                await user_role_repo.add(db_user_role)
        if page_object.type != 'profile' and is_general_edit and 'post_ids' in page_object.model_fields_set:
            user_post_repo = self._user_post_repo(query_db)
            await user_post_repo.delete_by_user_id(page_object.user_id)
            for post in page_object.post_ids or []:
                db_user_post = UserPostDO(user_id=page_object.user_id, post_id=post)
                await user_post_repo.add(db_user_post)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_user_services(self, query_db: AsyncSession, page_object: DeleteUserModel):
        """
        删除用户信息service
        :param query_db: orm对象
        :param page_object: 删除用户对象
        :return: 删除用户校验结果
        """
        if not page_object.user_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='user_ids', user_message='传入用户id为空'
            )
        user_repo = self._user_repo(query_db)
        user_role_repo = self._user_role_repo(query_db)
        user_post_repo = self._user_post_repo(query_db)
        user_id_list = page_object.user_ids.split(',')
        for user_id in user_id_list:
            await user_role_repo.delete_by_user_id(int(user_id))
            await user_post_repo.delete_by_user_id(int(user_id))
            await user_repo.soft_delete(int(user_id), page_object.update_by)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def user_detail_services(
        self,
        query_db: AsyncSession,
        user_id: int | str,
        posts: list | None = None,
        roles: list | None = None,
    ):
        """
        获取用户详细信息service
        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        post_options = posts or []
        role_options = roles or []
        if user_id != '':
            user_repo = self._user_repo(query_db)
            query_user = await user_repo.get_user_with_relations(user_id=user_id)
            if not query_user or not query_user.get('user_basic_info'):
                # 用户不存在，抛出 404 异常
                raise ResourceNotFoundException(
                    user_message='用户不存在',
                    error_code=ErrorCode.USER_NOT_FOUND,
                    developer_message=f'User with id={user_id} not found in database',
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
                posts=post_options,
                roleIds=role_ids_list,
                roles=role_options,
            )
        return UserDetailModel(posts=post_options, roles=role_options)

    async def user_profile_services(self, query_db: AsyncSession, user_id: int):
        """
        获取用户个人详细信息service
        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        user_repo = self._user_repo(query_db)
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

    @transactional()
    async def reset_user_services(self, query_db: AsyncSession, page_object: ResetUserModel):
        """
        重置用户密码service
        :param query_db: orm对象
        :param page_object: 重置用户对象
        :return: 重置用户校验结果
        """
        reset_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        user_repo = self._user_repo(query_db)
        if page_object.old_password:
            user = (await user_repo.get_user_with_relations(user_id=page_object.user_id)).get('user_basic_info')
            if not PwdUtil.verify_password(page_object.old_password, user.password):
                raise ValidationException(
                    error_code=ErrorCode.INVALID_PASSWORD, field='oldPassword', user_message='修改密码失败，旧密码错误'
                )
            elif PwdUtil.verify_password(page_object.password, user.password):
                raise ValidationException(
                    error_code=ErrorCode.INVALID_INPUT, field='password', user_message='新密码不能与旧密码相同'
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

    @transactional()
    async def batch_import_user_services(
        self,
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
        results: list[dict[str, Any]] = []
        succeeded = 0
        failed = 0
        user_repo = self._user_repo(query_db)
        config_service = self._require_config_service()
        dept_service = self._require_dept_service()
        for index, row in df.iterrows():
            row_number = int(index) + 1
            row_data = _normalize_user_import_row(row)
            user_name = str(row_data.get('user_name') or '').strip()
            item_id = user_name or row_number
            try:
                add_user = UserModel(
                    deptId=row_data['dept_id'],
                    userName=row_data['user_name'],
                    password=PwdUtil.get_password_hash(
                        await config_service.query_config_list_from_cache_services(
                            request.app.state.redis, 'sys.user.initPassword'
                        )
                    ),
                    nickName=row_data['nick_name'],
                    email=row_data['email'],
                    phonenumber=str(row_data['phonenumber']),
                    sex=row_data['sex'],
                    status=row_data['status'],
                    createBy=current_user.user.user_name,
                    createTime=datetime.now(),
                    updateBy=current_user.user.user_name,
                    updateTime=datetime.now(),
                )
                user_info = await user_repo.find_by_username(row_data['user_name'])
                if user_info:
                    if not update_support:
                        raise ValidationException(
                            user_message=f'用户账号{row_data["user_name"]}已存在',
                            error_code=ErrorCode.USER_ALREADY_EXISTS,
                            field='user_name',
                        )
                    edit_user_model = UserModel(
                        userId=user_info.user_id,
                        deptId=row_data['dept_id'],
                        userName=row_data['user_name'],
                        nickName=row_data['nick_name'],
                        email=row_data['email'],
                        phonenumber=str(row_data['phonenumber']),
                        sex=row_data['sex'],
                        status=row_data['status'],
                        updateBy=current_user.user.user_name,
                        updateTime=datetime.now(),
                    )
                    edit_user_model.validate_fields()
                    await self.check_user_allowed_services(edit_user_model)
                    if not current_user.user.admin:
                        await self.check_user_data_scope_services(
                            query_db,
                            edit_user_model.user_id,
                            user_data_scope_sql,
                        )
                        await dept_service.check_dept_data_scope_services(edit_user_model.dept_id, dept_data_scope_sql)
                    edit_user = edit_user_model.model_dump(exclude_unset=True)
                    db_user = await user_repo.get_by_id(user_info.user_id)
                    if db_user:
                        for key, value in edit_user.items():
                            if hasattr(db_user, key):
                                setattr(db_user, key, value)
                        await user_repo.update(db_user)
                    results.append(
                        _build_import_success_result(
                            row_number=row_number,
                            user_name=row_data['user_name'],
                            action='updated',
                            item_id=user_info.user_id,
                        )
                    )
                    succeeded += 1
                else:
                    add_user.validate_fields()
                    if not current_user.user.admin:
                        await dept_service.check_dept_data_scope_services(add_user.dept_id, dept_data_scope_sql)
                    db_user = UserDO(**add_user.model_dump(exclude={'admin'}))
                    await user_repo.add(db_user)
                    results.append(
                        _build_import_success_result(
                            row_number=row_number,
                            user_name=row_data['user_name'],
                            action='created',
                            item_id=row_data['user_name'],
                        )
                    )
                    succeeded += 1
            except Exception as exc:
                failed += 1
                results.append(
                    _build_import_failure_result(
                        row_number=row_number,
                        user_name=user_name,
                        item_id=item_id,
                        exc=exc,
                    )
                )

        return CrudResponseModel(
            is_success=True,
            message='导入完成',
            result={
                'results': results,
                'summary': {
                    'total': len(results),
                    'succeeded': succeeded,
                    'failed': failed,
                },
            },
        )

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
    async def export_user_list_services(user_list: list):
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
            if item.get('status') == StatusEnum.NORMAL.value:
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

    async def get_user_role_allocated_list_services(self, query_db: AsyncSession, page_object: UserRoleQueryModel):
        """
        根据用户id获取已分配角色列表
        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 已分配角色列表
        """
        user_repo = self._user_repo(query_db)
        query_user = await user_repo.get_user_with_relations(page_object.user_id)
        if query_user.get('user_basic_info') is None:
            raise ResourceNotFoundException(error_code=ErrorCode.USER_NOT_FOUND, user_message='用户不存在')
        relations = await self._user_role_repo(query_db).find_by_user_id(page_object.user_id)
        assigned_ids = {row.role_id for row in relations}
        available_roles = await RoleRepository(query_db).find_for_user_authorization(page_object.user_id)
        assigned_roles = [row for row in available_roles if row.role_id in assigned_ids]
        post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
        role_ids = ','.join(str(role_id) for role_id in sorted(assigned_ids))
        user = UserInfoModel(
            **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
            postIds=post_ids,
            roleIds=role_ids,
            dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
            role=CamelCaseUtil.transform_result(assigned_roles),
        )
        query_role_list = [
            SelectedRoleModel(**CamelCaseUtil.transform_result(row), flag=row.role_id in assigned_ids)
            for row in available_roles
        ]
        result = UserRoleResponseModel(roles=query_role_list, user=user)
        return result
