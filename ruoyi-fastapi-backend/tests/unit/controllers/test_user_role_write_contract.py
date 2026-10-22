"""Operation-specific request boundaries, using the actual registered route models."""

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from exceptions.exception import PermissionException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel, EditUserModel, UserInfoModel
from modules.system.api import user_controller
from modules.system.api.role_controller import roleController
from modules.system.api.user_controller import userController
from modules.system.application.behaviors.command_behaviors import CommandValidationBehavior
from modules.system.application.commands import EditUserCommand
from modules.system.application.handlers.command.user_command_handlers import EditUserCommandHandler


def request_model(router, path, method='PUT'):
    route = next(route for route in router.routes if route.path == path and method in route.methods)
    return route.body_field.type_


@pytest.mark.parametrize(
    ('field', 'value'),
    [(field, value) for field in ('oldPassword', 'newPassword') for value in ('missing', None, '')],
)
def test_profile_password_requires_both_credentials(field, value):
    payload = {'oldPassword': 'Current123!', 'newPassword': 'Changed123!'}
    if value == 'missing':
        payload.pop(field)
    else:
        payload[field] = value

    with pytest.raises(ValidationError) as failure:
        request_model(userController, '/system/user/profile/updatePwd')(**payload)

    assert any(error['loc'] == (field,) for error in failure.value.errors())


CASES = [
    (
        userController,
        '/system/user/profile',
        'PUT',
        {'nickName': 'After'},
        [
            'userId',
            'userName',
            'deptId',
            'status',
            'delFlag',
            'password',
            'avatar',
            'roleIds',
            'postIds',
            'type',
            'createBy',
        ],
    ),
    (
        userController,
        '/system/user',
        'POST',
        {'userName': 'alice', 'nickName': 'Alice', 'password': 'admin123'},
        ['userId', 'delFlag', 'loginIp', 'avatar', 'type', 'createBy'],
    ),
    (
        userController,
        '/system/user',
        'PUT',
        {'userId': 42, 'userName': 'alice'},
        ['password', 'avatar', 'delFlag', 'loginIp', 'createBy', 'type', 'admin'],
    ),
    (
        userController,
        '/system/user/changeStatus',
        'PUT',
        {'userId': 42, 'status': '1'},
        ['nickName', 'deptId', 'roleIds', 'postIds', 'password', 'type', 'createBy'],
    ),
    (
        roleController,
        '/system/role',
        'POST',
        {'roleName': 'Ops', 'roleKey': 'ops', 'roleSort': 1},
        ['roleId', 'dataScope', 'deptIds', 'delFlag', 'type', 'createBy'],
    ),
    (
        roleController,
        '/system/role',
        'PUT',
        {'roleId': 42, 'roleName': 'Ops'},
        ['dataScope', 'deptIds', 'delFlag', 'createBy', 'type', 'admin'],
    ),
    (
        roleController,
        '/system/role/changeStatus',
        'PUT',
        {'roleId': 42, 'status': '1'},
        ['roleName', 'menuIds', 'dataScope', 'deptIds', 'type', 'createBy'],
    ),
    (
        roleController,
        '/system/role/dataScope',
        'PUT',
        {'roleId': 42, 'dataScope': '2'},
        ['roleName', 'roleKey', 'menuIds', 'status', 'type', 'createBy'],
    ),
]


@pytest.mark.parametrize(('router', 'path', 'method', 'valid', 'forbidden'), CASES)
def test_each_operation_rejects_inappropriate_fields(router, path, method, valid, forbidden):
    model = request_model(router, path, method)
    model.model_validate(valid)
    for field in forbidden:
        with pytest.raises(ValidationError) as caught:
            model.model_validate({**valid, field: None})
        assert any(error['type'] == 'extra_forbidden' for error in caught.value.errors()), field


@pytest.mark.parametrize(
    ('router', 'path', 'valid', 'required'),
    [
        (userController, '/system/user', {'userId': 42}, ['userId']),
        (userController, '/system/user/changeStatus', {'userId': 42, 'status': '1'}, ['userId', 'status']),
        (roleController, '/system/role', {'roleId': 42}, ['roleId']),
        (roleController, '/system/role/changeStatus', {'roleId': 42, 'status': '1'}, ['roleId', 'status']),
        (roleController, '/system/role/dataScope', {'roleId': 42, 'dataScope': '2'}, ['roleId', 'dataScope']),
    ],
)
def test_identity_and_required_action_fields_cannot_be_missing_or_null(router, path, valid, required):
    model = request_model(router, path)
    for field in required:
        for payload in [{key: value for key, value in valid.items() if key != field}, {**valid, field: None}]:
            with pytest.raises(ValidationError):
                model.model_validate(payload)


@pytest.mark.asyncio
async def test_profile_maps_only_requested_fields_and_never_replays_login_associations(monkeypatch):
    model = request_model(userController, '/system/user/profile')
    mediator = SimpleNamespace(send=AsyncMock(return_value=SimpleNamespace(data={'message': '更新成功'})))
    monkeypatch.setattr(user_controller, '_load_user_profile', AsyncMock(return_value={}))
    current = CurrentUserModel(
        permissions=[], roles=[], user=UserInfoModel(userId=42, userName='alice', roleIds='21', postIds='31', role=[])
    )
    await inspect.unwrap(user_controller.change_system_user_profile_info)(
        Request({'type': 'http', 'headers': []}),
        model.model_validate({'nickName': 'After'}),
        object(),
        current,
        mediator,
    )
    command = mediator.send.await_args.args[0]
    fields = command.user.model_fields_set
    assert command.user.user_id == current.user.user_id
    assert command.user.nick_name == 'After'
    assert command.user.type == 'profile'
    assert fields.isdisjoint({'role_ids', 'post_ids', 'role', 'password', 'dept_id', 'status', 'del_flag'})
    assert command.user.update_by == current.user.user_name


@pytest.mark.asyncio
async def test_ordinary_user_partial_edit_validates_only_supplied_fields():
    service = SimpleNamespace(
        check_user_allowed_services=AsyncMock(),
        edit_user_services=AsyncMock(return_value=CrudResponseModel(is_success=True, message='更新成功')),
    )
    handler = EditUserCommandHandler(service, AsyncMock(), AsyncMock())
    await handler.handle(EditUserCommand(query_db=object(), user=EditUserModel(userId=42, nickName='After')))
    service.edit_user_services.assert_awaited_once()


@pytest.mark.asyncio
async def test_profile_command_allows_admin_self_service_without_association_or_admin_edits():
    service = SimpleNamespace(
        check_user_allowed_services=AsyncMock(side_effect=AssertionError('admin profile rejected')),
        edit_user_services=AsyncMock(return_value=CrudResponseModel(is_success=True, message='更新成功')),
    )
    handler = EditUserCommandHandler(service, AsyncMock(), AsyncMock())
    await handler.handle(
        EditUserCommand(
            query_db=object(), user=EditUserModel(userId=1, userName='admin', nickName='After', type='profile')
        )
    )
    service.check_user_allowed_services.assert_not_awaited()
    service.edit_user_services.assert_awaited_once()


@pytest.mark.parametrize(
    ('router', 'path', 'method', 'valid', 'fields'),
    [
        (userController, '/system/user', 'POST', {'userName': 'alice', 'password': 'admin123'}, ['nickName']),
        (userController, '/system/user/profile', 'PUT', {}, ['nickName']),
        (userController, '/system/user', 'PUT', {'userId': 42}, ['userName', 'nickName']),
        (roleController, '/system/role', 'PUT', {'roleId': 42}, ['roleName', 'roleKey', 'roleSort', 'status']),
    ],
)
def test_non_null_persistence_fields_reject_explicit_null(router, path, method, valid, fields):
    model = request_model(router, path, method)
    for field in fields:
        with pytest.raises(ValidationError):
            model.model_validate({**valid, field: None})
        prop = model.model_json_schema(by_alias=True)['properties'][field]
        assert not any(option.get('type') == 'null' for option in prop.get('anyOf', []))


def test_user_creation_requires_a_nickname():
    model = request_model(userController, '/system/user', 'POST')
    with pytest.raises(ValidationError):
        model.model_validate({'userName': 'alice', 'password': 'admin123'})


@pytest.mark.parametrize(
    ('router', 'path', 'method', 'payload'),
    [
        (
            userController,
            '/system/user',
            'POST',
            {'userName': 'alice', 'nickName': 'Alice', 'password': 'admin123', 'email': 'invalid'},
        ),
        (userController, '/system/user', 'PUT', {'userId': 42, 'email': 'invalid'}),
        (userController, '/system/user/profile', 'PUT', {'email': 'invalid'}),
        (roleController, '/system/role', 'POST', {'roleName': '', 'roleKey': 'ops', 'roleSort': 1}),
        (roleController, '/system/role', 'PUT', {'roleId': 42, 'roleName': ''}),
    ],
)
def test_existing_field_rules_fail_as_input_validation_before_the_audit_wrapper(router, path, method, payload):
    with pytest.raises(ValidationError):
        request_model(router, path, method).model_validate(payload)


@pytest.mark.asyncio
@pytest.mark.parametrize('dept', ['omitted', 'null', 'outside'])
async def test_partial_user_edits_check_only_the_supplied_target_department(dept):
    service = SimpleNamespace(
        check_user_allowed_services=AsyncMock(),
        check_user_data_scope_services=AsyncMock(),
        edit_user_services=AsyncMock(return_value=CrudResponseModel(is_success=True, message='更新成功')),
    )
    dept_service = SimpleNamespace(
        check_dept_data_scope_services=AsyncMock(side_effect=PermissionException(user_message='无部门权限'))
    )
    handler = EditUserCommandHandler(service, dept_service, AsyncMock())
    payload = {'userId': 42, 'nickName': 'After'}
    if dept != 'omitted':
        payload['deptId'] = None if dept == 'null' else 999
    command = EditUserCommand(query_db=object(), user=EditUserModel(**payload), enforce_scope_checks=True)
    if dept == 'outside':
        with pytest.raises(PermissionException):
            await handler.handle(command)
        dept_service.check_dept_data_scope_services.assert_awaited_once()
        service.edit_user_services.assert_not_awaited()
    else:
        await handler.handle(command)
        dept_service.check_dept_data_scope_services.assert_not_awaited()
        service.edit_user_services.assert_awaited_once()
    service.check_user_data_scope_services.assert_awaited_once()


def test_command_pipeline_uses_partial_edit_validation_as_well_as_the_handler():
    command = EditUserCommand(query_db=object(), user=EditUserModel(userId=42, nickName='After'))
    CommandValidationBehavior._validate_request(command)
