"""User service unit tests for the repository-based architecture."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from common.remark_document_v1 import plain_to_remark
from config.constant import CommonConstant
from config.error_codes import ErrorCode, ErrorType
from exceptions.exception import PermissionException, ValidationException
from module_admin.entity.do.user_do import UserDO, UserPostDO, UserRoleDO
from module_admin.entity.vo.user_vo import EditUserModel, ResetUserModel, UserModel
from modules.system.application.behaviors.command_behaviors import CommandValidationBehavior
from modules.system.application.commands import ResetUserPasswordCommand
from modules.system.application.handlers.command.user_command_handlers import ResetUserPasswordCommandHandler
from modules.system.application.services.user_service import UserService
from modules.system.infrastructure.user_post_repository import UserPostRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository
from utils.pwd_util import PwdUtil


@pytest.mark.asyncio
async def test_check_user_allowed_blocks_admin_user():
    admin_user = UserModel(userId=1)
    service = UserService()

    with pytest.raises(PermissionException) as failure:
        await service.check_user_allowed_services(admin_user)

    assert failure.value.http_status == 403
    assert failure.value.error_code == ErrorCode.ADMIN_USER_OPERATION_FORBIDDEN
    assert failure.value.error_type == ErrorType.AUTHORIZATION


@pytest.mark.asyncio
async def test_user_data_scope_denial_is_authorization_failure():
    repository = SimpleNamespace(paginate_with_dept=AsyncMock(return_value=[]))
    service = UserService(user_repo_factory=lambda _: repository)

    with pytest.raises(PermissionException) as failure:
        await service.check_user_data_scope_services(None, 42, 'self-only-scope')

    assert failure.value.http_status == 403
    assert failure.value.error_code == ErrorCode.DATA_SCOPE_PERMISSION_DENIED
    assert failure.value.error_type == ErrorType.AUTHORIZATION
    repository.paginate_with_dept.assert_awaited_once_with(
        page=1, page_size=10000, user_id=42, data_scope_sql='self-only-scope'
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('through_pipeline', [False, True])
async def test_wrong_old_password_is_field_validation_without_writing(through_pipeline):
    password_hash = PwdUtil.get_password_hash('Current123!')
    user = SimpleNamespace(password=password_hash)
    repository = SimpleNamespace(
        get_user_with_relations=AsyncMock(return_value={'user_basic_info': user}),
        get_by_id=AsyncMock(),
        update=AsyncMock(),
    )
    service = UserService(user_repo_factory=lambda _: repository)
    payload = ResetUserModel(userId=42, oldPassword='Incorrect123!', password='Changed123!')

    with pytest.raises(ValidationException) as failure:
        if through_pipeline:
            command = ResetUserPasswordCommand(query_db=None, reset_user=payload)
            handler = ResetUserPasswordCommandHandler(service)
            await CommandValidationBehavior().handle(command, lambda: handler.handle(command))
        else:
            await service.reset_user_services(None, payload)

    assert failure.value.http_status == 422
    assert failure.value.error_code == ErrorCode.INVALID_PASSWORD
    assert failure.value.error_type == ErrorType.VALIDATION
    assert failure.value.extra['field'] == 'oldPassword'
    assert user.password == password_hash
    repository.get_user_with_relations.assert_awaited_once_with(user_id=42)
    repository.get_by_id.assert_not_awaited()
    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_sms_reset_command_keeps_separate_old_password_semantics():
    user = SimpleNamespace(user_id=42, password='before')
    repository = SimpleNamespace(
        get_user_with_relations=AsyncMock(),
        get_by_id=AsyncMock(return_value=user),
        update=AsyncMock(),
    )
    service = UserService(user_repo_factory=lambda _: repository)
    payload = ResetUserModel(userId=42, password='Changed123!', smsCode='verified', sessionId='sms-session')
    command = ResetUserPasswordCommand(query_db=None, reset_user=payload)
    handler = ResetUserPasswordCommandHandler(service)

    result = await CommandValidationBehavior().handle(command, lambda: handler.handle(command))

    assert result.success
    assert PwdUtil.verify_password('Changed123!', user.password)
    repository.get_user_with_relations.assert_not_awaited()
    repository.update.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_check_unique_returns_true_when_value_missing():
    page_object = UserModel(userId=2)
    service = UserService()

    result = await service._check_unique(page_object, AsyncMock(return_value=None), None)

    assert result is CommonConstant.UNIQUE


@pytest.mark.asyncio
async def test_check_unique_returns_false_when_conflict_found():
    page_object = UserModel(userId=2)
    finder = AsyncMock(return_value=SimpleNamespace(user_id=3))
    service = UserService()

    result = await service._check_unique(page_object, finder, 'duplicate')

    assert result is CommonConstant.NOT_UNIQUE


def test_user_service_contract_methods_exist():
    assert callable(UserService.get_user_list_services)
    assert callable(UserService.add_user_services)
    assert callable(UserService.edit_user_services)
    assert callable(UserService.delete_user_services)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'updates', 'expected_roles', 'expected_posts'),
    [
        pytest.param('0', {'roleIds': [21], 'postIds': [31]}, [21], [31], id='form-without-role-display'),
        pytest.param('1', {}, [20], [30], id='omitted-relations-preserve'),
        pytest.param('0', {'roleIds': [21]}, [21], [30], id='replace-only-roles'),
        pytest.param('1', {'postIds': [31]}, [20], [31], id='replace-only-posts'),
        pytest.param('0', {'roleIds': [], 'postIds': [], 'role': [{'roleId': 999}]}, [], [], id='empty-clears'),
        pytest.param('1', {'roleIds': None, 'postIds': None, 'role': None}, [], [], id='explicit-null-clears'),
    ],
)
async def test_general_user_edit_optional_relations(db_session, status, updates, expected_roles, expected_posts):
    user = UserDO(
        user_name='optional_edit',
        nick_name='Before',
        status=status,
        remark=plain_to_remark('Keep this value', identity_key='user:fixture:remark'),
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add_all([UserRoleDO(user_id=user.user_id, role_id=20), UserPostDO(user_id=user.user_id, post_id=30)])
    await db_session.flush()

    result = await UserService().edit_user_services(
        db_session,
        EditUserModel(userId=user.user_id, userName=user.user_name, nickName='After', **updates),
    )

    await db_session.refresh(user)
    assert result.is_success
    assert user.nick_name == 'After'
    assert user.status == status
    assert user.remark == plain_to_remark('Keep this value', identity_key='user:fixture:remark')
    assert (
        sorted(row.role_id for row in await UserRoleRepository(db_session).find_by_user_id(user.user_id))
        == expected_roles
    )
    assert (
        sorted(row.post_id for row in await UserPostRepository(db_session).find_by_user_id(user.user_id))
        == expected_posts
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('edit_type', 'updates', 'field', 'expected'),
    [
        ('status', {'status': '1'}, 'status', '1'),
        ('avatar', {'avatar': '/new-avatar.png'}, 'avatar', '/new-avatar.png'),
        ('pwd', {'password': 'new-password-hash'}, 'password', 'new-password-hash'),
    ],
)
async def test_special_user_edits_preserve_relations(db_session, edit_type, updates, field, expected):
    user = UserDO(user_name='special_edit', nick_name='Unchanged', status='0')
    db_session.add(user)
    await db_session.flush()
    db_session.add_all([UserRoleDO(user_id=user.user_id, role_id=20), UserPostDO(user_id=user.user_id, post_id=30)])
    await db_session.flush()

    await UserService().edit_user_services(
        db_session,
        EditUserModel(userId=user.user_id, type=edit_type, roleIds=[], postIds=[], **updates),
    )

    await db_session.refresh(user)
    assert getattr(user, field) == expected
    assert user.nick_name == 'Unchanged'
    assert [row.role_id for row in await UserRoleRepository(db_session).find_by_user_id(user.user_id)] == [20]
    assert [row.post_id for row in await UserPostRepository(db_session).find_by_user_id(user.user_id)] == [30]
