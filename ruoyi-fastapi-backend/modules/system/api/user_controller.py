from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.env import UploadConfig
from config.error_codes import ErrorCode
from config.get_db import get_db
from container.dependencies import service_provider
from exceptions.exception import BusinessException, SystemException
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_role_write_vo import UserRolesAssignModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    ResetPasswordModel,
    ResetUserModel,
    UserPageQueryModel,
    UserRoleResponseModel,
)
from module_admin.entity.vo.user_write_vo import (
    UserCreateModel,
    UserProfileUpdateModel,
    UserStatusUpdateModel,
    UserUpdateModel,
)
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddUserCommand,
    AssignUserRolesCommand,
    DeleteUserCommand,
    EditUserCommand,
    ImportUsersCommand,
    ResetUserPasswordCommand,
)
from modules.system.application.mediator import Mediator
from modules.system.application.queries import (
    GetUserAuthRoleQuery,
    GetUserDeptTreeQuery,
    GetUserDetailQuery,
    GetUserListQuery,
    GetUserProfileQuery,
)
from modules.system.application.read_models.user_read_models import (
    UserDetailReadModel,
    UserPageReadModel,
    UserProfileReadModel,
)
from modules.system.application.services.user_service import UserService
from utils.common_util import bytes2file_response
from utils.http_contract_responses import ok_page_result, require_int_value
from utils.log_util import logger
from utils.pwd_util import PwdUtil
from utils.response_util import ResponseUtil
from utils.upload_util import UploadUtil
from utils.validation_util import ValidateFields

userController = APIRouter(prefix='/system/user', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_user_detail(
    request: Request,
    *,
    user_id: int | str | Literal[''],
    query_db: AsyncSession,
    mediator: Mediator,
    data_scope_sql: str = '',
    require_scope_check: bool = False,
):
    user_detail_query = GetUserDetailQuery(
        query_db=query_db,
        user_id=user_id,
        data_scope_sql=data_scope_sql,
        require_scope_check=require_scope_check,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(user_detail_query)


async def _load_user_profile(
    request: Request,
    *,
    query_db: AsyncSession,
    user_id: int,
    mediator: Mediator,
):
    profile_query = GetUserProfileQuery(
        query_db=query_db,
        user_id=user_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(profile_query)


@userController.get('/deptTree', dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))])
async def get_system_dept_tree(
    request: Request,
    data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    dept_tree_query = GetUserDeptTreeQuery(
        data_scope_sql=data_scope_sql,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    dept_query_result = await mediator.query(dept_tree_query)
    logger.info('获取成功')

    return ResponseUtil.ok_collection(items=dept_query_result)


@userController.get(
    '/list', response_model=UserPageReadModel, dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))]
)
async def get_system_user_list(
    request: Request,
    user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    user_list_query = GetUserListQuery(
        query_db=query_db,
        query=user_page_query,
        data_scope_sql=data_scope_sql,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    user_page_query_result = await mediator.query(user_list_query)
    logger.info('获取成功')

    return ok_page_result(user_page_query_result)


@userController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:user:add'))])
@ValidateFields(validate_model='add_user')
@Log(title='用户管理', business_type=BusinessType.INSERT)
async def add_system_user(
    request: Request,
    add_user: UserCreateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    dept_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    role_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_user = AddUserModel(**add_user.model_dump(exclude_unset=True))
    add_user.password = PwdUtil.get_password_hash(add_user.password)
    add_user.create_by = current_user.user.user_name
    add_user.create_time = datetime.now()
    add_user.update_by = current_user.user.user_name
    add_user.update_time = datetime.now()
    add_command = AddUserCommand(
        query_db=query_db,
        user=add_user,
        enforce_scope_checks=not current_user.user.admin,
        dept_data_scope_sql=dept_data_scope_sql,
        role_data_scope_sql=role_data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    user_id = require_int_value(add_result.data, 'userId', 'user_id', contract_name='system.user.create')
    resource = await _load_user_detail(
        request,
        user_id=user_id,
        query_db=query_db,
        data_scope_sql=dept_data_scope_sql,
        require_scope_check=not current_user.user.admin,
        mediator=mediator,
    )
    location = ResponseUtil.build_absolute_location(request, f'/system/user/{user_id}')
    return ResponseUtil.created_resource(resource, location=location)


@userController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@ValidateFields(validate_model='edit_user')
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def edit_system_user(
    request: Request,
    edit_user: UserUpdateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('UserDO')),
    dept_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    role_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_user = EditUserModel(**edit_user.model_dump(exclude_unset=True))
    edit_user.update_by = current_user.user.user_name
    edit_user.update_time = datetime.now()
    edit_command = EditUserCommand(
        query_db=query_db,
        user=edit_user,
        enforce_scope_checks=not current_user.user.admin,
        user_data_scope_sql=user_data_scope_sql,
        dept_data_scope_sql=dept_data_scope_sql,
        role_data_scope_sql=role_data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_user_detail(
        request,
        user_id=edit_user.user_id,
        query_db=query_db,
        data_scope_sql=user_data_scope_sql,
        require_scope_check=not current_user.user.admin,
        mediator=mediator,
    )
    return ResponseUtil.ok_resource(resource)


@userController.delete('/{user_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:user:remove'))])
@Log(title='用户管理', business_type=BusinessType.DELETE)
async def delete_system_user(
    request: Request,
    user_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    user_id_list = user_ids.split(',') if user_ids else []
    if user_id_list and current_user.user.user_id in list(map(int, user_id_list)):
        logger.warning('当前登录用户不能删除')
        raise BusinessException(
            user_message='当前登录用户不能删除', error_code=ErrorCode.USER_NOT_FOUND, http_status=400
        )
    delete_user = DeleteUserModel(userIds=user_ids, updateBy=current_user.user.user_name, updateTime=datetime.now())
    delete_command = DeleteUserCommand(
        query_db=query_db,
        delete_user=delete_user,
        enforce_scope_checks=not current_user.user.admin,
        user_data_scope_sql=data_scope_sql,
        current_user_id=current_user.user.user_id,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@userController.put('/resetPwd', dependencies=[Depends(CheckUserInterfaceAuth('system:user:resetPwd'))])
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def reset_system_user_pwd(
    request: Request,
    reset_user: EditUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_user = EditUserModel(
        userId=reset_user.user_id,
        password=PwdUtil.get_password_hash(reset_user.password),
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='pwd',
    )
    edit_command = EditUserCommand(
        query_db=query_db,
        user=edit_user,
        enforce_scope_checks=not current_user.user.admin,
        user_data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    return ResponseUtil.no_content()


@userController.put('/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def change_system_user_status(
    request: Request,
    change_user: UserStatusUpdateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_user = EditUserModel(
        userId=change_user.user_id,
        status=change_user.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    edit_command = EditUserCommand(
        query_db=query_db,
        user=edit_user,
        enforce_scope_checks=not current_user.user.admin,
        user_data_scope_sql=data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_user_detail(
        request,
        user_id=change_user.user_id,
        query_db=query_db,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
        mediator=mediator,
    )
    return ResponseUtil.ok_resource(resource)


@userController.get('/profile', response_model=UserProfileReadModel)
async def query_detail_system_user_profile(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    profile_user_result = await _load_user_profile(
        request,
        query_db=query_db,
        user_id=current_user.user.user_id,
        mediator=mediator,
    )
    logger.info(f'获取user_id为{current_user.user.user_id}的信息成功')

    return ResponseUtil.ok_resource(profile_user_result)


@userController.get(
    '/{user_id}',
    response_model=UserDetailReadModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))],
)
@userController.get(
    '/', response_model=UserDetailReadModel, dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))]
)
async def query_detail_system_user(
    request: Request,
    user_id: int | Literal[''] | None = '',
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_user_result = await _load_user_detail(
        request,
        user_id=user_id,
        query_db=query_db,
        data_scope_sql=data_scope_sql,
        require_scope_check=bool(user_id and not current_user.user.admin),
        mediator=mediator,
    )
    logger.info(f'获取user_id为{user_id}的信息成功')

    return ResponseUtil.ok_resource(detail_user_result)


@userController.post('/profile/avatar')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def change_system_user_profile_avatar(
    request: Request,
    avatarfile: bytes = File(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    if avatarfile:
        relative_path = (
            f'avatar/{datetime.now().strftime("%Y")}/{datetime.now().strftime("%m")}/{datetime.now().strftime("%d")}'
        )
        dir_path = Path(UploadConfig.UPLOAD_PATH) / relative_path
        with suppress(FileExistsError):
            dir_path.mkdir(parents=True)
        avatar_name = (
            f'avatar_{datetime.now().strftime("%Y%m%d%H%M%S")}'
            f'{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.png'
        )
        avatar_path = dir_path / avatar_name
        with avatar_path.open('wb') as f:
            f.write(avatarfile)
        edit_user = EditUserModel(
            userId=current_user.user.user_id,
            avatar=f'{UploadConfig.UPLOAD_PREFIX}/{relative_path}/{avatar_name}',
            updateBy=current_user.user.user_name,
            updateTime=datetime.now(),
            type='avatar',
        )
        edit_command = EditUserCommand(
            query_db=query_db,
            user=edit_user,
            operator=current_user.user.user_name,
            trace_id=request.headers.get('x-trace-id'),
            request_id=request.headers.get('x-request-id'),
        )
        edit_result = await mediator.send(edit_command)
        message = edit_result.data.get('message') if edit_result.data else '更新成功'
        logger.info(message)

        return ResponseUtil.ok_resource({'imgUrl': edit_user.avatar})

    raise SystemException(
        user_message='上传图片失败, 请重试', developer_message='Avatar upload failed: file is None or empty'
    )


@userController.put('/profile')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def change_system_user_profile_info(
    request: Request,
    user_info: UserProfileUpdateModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_user = EditUserModel(
        **user_info.model_dump(exclude_unset=True),
        userId=current_user.user.user_id,
        userName=current_user.user.user_name,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='profile',
    )
    edit_command = EditUserCommand(
        query_db=query_db,
        user=edit_user,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    profile_user_result = await _load_user_profile(
        request,
        query_db=query_db,
        user_id=current_user.user.user_id,
        mediator=mediator,
    )
    return ResponseUtil.ok_resource(profile_user_result)


@userController.put('/profile/updatePwd')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def reset_system_user_password(
    request: Request,
    reset_password: ResetPasswordModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    reset_user = ResetUserModel(
        userId=current_user.user.user_id,
        oldPassword=reset_password.old_password,
        password=reset_password.new_password,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
    )
    reset_command = ResetUserPasswordCommand(
        query_db=query_db,
        reset_user=reset_user,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    reset_result = await mediator.send(reset_command)
    message = reset_result.data.get('message') if reset_result.data else '重置成功'
    logger.info(message)

    return ResponseUtil.no_content()


@userController.post('/importData', dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
@Log(title='用户管理', business_type=BusinessType.IMPORT)
async def batch_import_system_user(
    request: Request,
    file: UploadFile = File(...),
    update_support: bool = Query(alias='updateSupport'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('UserDO')),
    dept_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    import_command = ImportUsersCommand(
        request=request,
        query_db=query_db,
        file=file,
        update_support=update_support,
        current_user=current_user,
        user_data_scope_sql=user_data_scope_sql,
        dept_data_scope_sql=dept_data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    import_result = await mediator.send(import_command)
    logger.info('导入完成')

    result = import_result.data or {'results': [], 'summary': {'total': 0, 'succeeded': 0, 'failed': 0}}
    return ResponseUtil.batch_result(
        results=result.get('results', []),
        summary=result.get('summary', {'total': 0, 'succeeded': 0, 'failed': 0}),
    )


@userController.post('/importTemplate', dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
async def export_system_user_template(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(service_provider('user_service')),
):
    user_import_template_result = await user_service.get_user_import_template_services()
    logger.info('获取成功')

    return ResponseUtil.streaming(data=bytes2file_response(user_import_template_result))


@userController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:user:export'))])
@Log(title='用户管理', business_type=BusinessType.EXPORT)
async def export_system_user_list(
    request: Request,
    user_page_query: UserPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    user_service: UserService = Depends(service_provider('user_service')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    user_list_query = GetUserListQuery(
        query_db=query_db,
        query=user_page_query,
        data_scope_sql=data_scope_sql,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    user_query_result = await mediator.query(user_list_query)
    user_rows = [row.model_dump(by_alias=True) for row in user_query_result.items]
    user_export_result = await user_service.export_user_list_services(user_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(user_export_result))


@userController.get(
    '/authRole/{user_id}',
    response_model=UserRoleResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))],
)
async def get_system_allocated_role_list(
    request: Request,
    user_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    data_scope_sql: str = Depends(GetDataScope('UserDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    auth_role_query = GetUserAuthRoleQuery(
        query_db=query_db,
        user_id=user_id,
        data_scope_sql=data_scope_sql,
        require_scope_check=not current_user.user.admin,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    user_role_allocated_query_result = await mediator.query(auth_role_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(user_role_allocated_query_result)


@userController.put(
    '/authRole',
    status_code=204,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))],
)
@Log(title='用户管理', business_type=BusinessType.GRANT)
async def update_system_role_user(
    request: Request,
    user_role: UserRolesAssignModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('UserDO')),
    role_data_scope_sql: str = Depends(GetDataScope('DeptDO')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    assign_command = AssignUserRolesCommand(
        query_db=query_db,
        user_role=user_role,
        enforce_scope_checks=not current_user.user.admin,
        user_data_scope_sql=user_data_scope_sql,
        role_data_scope_sql=role_data_scope_sql,
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    assign_result = await mediator.send(assign_command)
    message = assign_result.data.get('message') if assign_result.data else '分配成功'
    logger.info(message)

    return ResponseUtil.no_content()
