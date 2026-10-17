"""Real repositories and SQL data scopes exercise authorization before any relation write."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import event, select

from exceptions.exception import PermissionException, ResourceNotFoundException
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.role_do import RoleDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from modules.system.application.commands.role_commands import (
    AddRoleUserCommand,
    BatchCancelRoleUserCommand,
    CancelRoleUserCommand,
)
from modules.system.application.commands.user_commands import AssignUserRolesCommand
from modules.system.application.handlers.command.role_command_handlers import (
    AddRoleUserCommandHandler,
    BatchCancelRoleUserCommandHandler,
    CancelRoleUserCommandHandler,
)
from modules.system.application.handlers.command.user_command_handlers import (
    AssignUserRolesCommandHandler,
)
from modules.system.application.services.role_service import RoleService
from modules.system.application.services.user_role_service import UserRoleService
from modules.system.application.services.user_service import UserService
from modules.system.infrastructure.role_repository import RoleRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository


@pytest.fixture
async def authorization(db_session):
    db_session.add_all([DeptDO(dept_id=7, dept_name='Inside'), DeptDO(dept_id=8, dept_name='Outside')])
    for uid, dept in [(1, 7), (42, 7), (43, 8), (44, 7), (45, 7)]:
        db_session.add(
            UserDO(
                user_id=uid,
                dept_id=dept,
                user_name=f'u{uid}',
                nick_name=f'u{uid}',
                password='hashedpassword',
                del_flag='2' if uid == 45 else '0',
            )
        )
    for rid in [1, 20, 21, 22]:
        db_session.add(
            RoleDO(
                role_id=rid, role_name=f'r{rid}', role_key=f'r{rid}', role_sort=rid, del_flag='2' if rid == 22 else '0'
            )
        )
    db_session.add_all([UserRoleDO(user_id=42, role_id=20), UserRoleDO(user_id=43, role_id=21)])
    await db_session.flush()
    user_service = UserService(query_db=db_session)
    role_service = RoleService(RoleRepository(db_session), AsyncMock(), AsyncMock(), AsyncMock(), db_session)
    service = UserRoleService(user_service, role_service)
    writes = []

    def record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().lower().startswith(('insert into sys_user_role', 'delete from sys_user_role')):
            writes.append(statement)

    event.listen(db_session.bind.sync_engine, 'before_cursor_execute', record)

    async def run(operation, payload, *, scoped=False, user_scope='True', role_scope='True'):
        command_type, handler, field = {
            'replace': (AssignUserRolesCommand, AssignUserRolesCommandHandler(service), 'user_role'),
            'grant': (AddRoleUserCommand, AddRoleUserCommandHandler(service), 'role_user'),
            'revoke': (CancelRoleUserCommand, CancelRoleUserCommandHandler(service), 'role_user'),
            'batch': (BatchCancelRoleUserCommand, BatchCancelRoleUserCommandHandler(service), 'role_user'),
        }[operation]
        model = command_type.model_fields[field].annotation
        return await handler.handle(
            command_type(
                query_db=db_session,
                **{field: model(**payload)},
                enforce_scope_checks=scoped,
                user_data_scope_sql=user_scope,
                role_data_scope_sql=role_scope,
            )
        )

    async def relations():
        return set((await db_session.execute(select(UserRoleDO.user_id, UserRoleDO.role_id))).all())

    yield run, relations, writes, db_session
    event.remove(db_session.bind.sync_engine, 'before_cursor_execute', record)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'operation,payload',
    [
        ('replace', {'userId': 999, 'roleIds': []}),
        ('replace', {'userId': 42, 'roleIds': [20, 999]}),
        ('replace', {'userId': 42, 'roleIds': [22]}),
        ('grant', {'roleId': 20, 'userIds': [44, 999]}),
        ('grant', {'roleId': 999, 'userIds': [44]}),
        ('grant', {'roleId': 20, 'userIds': [44, 45]}),
        ('revoke', {'roleId': 999, 'userId': 42}),
        ('revoke', {'roleId': 20, 'userId': 999}),
        ('batch', {'roleId': 20, 'userIds': [42, 999]}),
    ],
)
async def test_missing_or_deleted_party_rejected_before_writes(authorization, operation, payload):
    run, relations, writes, _ = authorization
    before = await relations()
    with pytest.raises(ResourceNotFoundException):
        await run(operation, payload)
    assert writes == []
    assert await relations() == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'operation,payload',
    [
        ('replace', {'userId': 1, 'roleIds': []}),
        ('grant', {'roleId': 20, 'userIds': [44, 1]}),
        ('revoke', {'roleId': 20, 'userId': 1}),
        ('batch', {'roleId': 20, 'userIds': [42, 1]}),
        ('replace', {'userId': 42, 'roleIds': [1]}),
        ('grant', {'roleId': 1, 'userIds': [44]}),
        ('revoke', {'roleId': 1, 'userId': 42}),
        ('batch', {'roleId': 1, 'userIds': [42]}),
    ],
)
async def test_protected_objects_rejected_even_with_unrestricted_data_scope(authorization, operation, payload):
    run, relations, writes, _ = authorization
    before = await relations()
    with pytest.raises(PermissionException):
        await run(operation, payload, scoped=True)
    assert writes == []
    assert await relations() == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'operation,payload',
    [
        ('replace', {'userId': 43, 'roleIds': [20]}),
        ('replace', {'userId': 42, 'roleIds': [21]}),
        ('grant', {'roleId': 20, 'userIds': [44, 43]}),
        ('grant', {'roleId': 21, 'userIds': [44]}),
        ('revoke', {'roleId': 20, 'userId': 43}),
        ('revoke', {'roleId': 21, 'userId': 42}),
        ('batch', {'roleId': 20, 'userIds': [42, 43]}),
        ('batch', {'roleId': 21, 'userIds': [42]}),
    ],
)
async def test_both_data_scopes_preflight_entire_batch(authorization, operation, payload):
    run, relations, writes, _ = authorization
    before = await relations()
    with pytest.raises(PermissionException):
        await run(operation, payload, scoped=True, user_scope=UserDO.dept_id == 7, role_scope=DeptDO.dept_id == 7)
    assert writes == []
    assert await relations() == before


@pytest.mark.asyncio
async def test_replacement_also_checks_roles_being_removed(authorization):
    run, relations, writes, _ = authorization
    await run('grant', {'roleId': 1, 'userIds': [42]})
    before = await relations()
    writes.clear()
    with pytest.raises(PermissionException):
        await run('replace', {'userId': 42, 'roleIds': []}, scoped=True)
    assert writes == []
    assert await relations() == before


@pytest.mark.asyncio
async def test_admin_assignment_incremental_idempotence_clear_and_targeted_revoke(authorization):
    run, relations, _, _ = authorization
    await run('grant', {'roleId': 1, 'userIds': [42, 42, 44]})
    await run('grant', {'roleId': 1, 'userIds': [42]})
    assert await relations() == {(42, 20), (43, 21), (42, 1), (44, 1)}
    await run('revoke', {'roleId': 1, 'userId': 42})
    assert await relations() == {(42, 20), (43, 21), (44, 1)}
    await run('replace', {'userId': 42, 'roleIds': [20, 21, 21]})
    assert await relations() == {(42, 20), (42, 21), (43, 21), (44, 1)}
    await run('replace', {'userId': 42, 'roleIds': []})
    await run('batch', {'roleId': 1, 'userIds': [42, 44, 44]})
    assert await relations() == {(43, 21)}


@pytest.mark.asyncio
async def test_write_failure_rolls_back_entire_batch(authorization, monkeypatch):
    run, relations, _, _ = authorization
    before = await relations()
    original = UserRoleRepository.add
    count = 0

    async def fail_second(self, entity):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError('second insert fails')
        return await original(self, entity)

    monkeypatch.setattr(UserRoleRepository, 'add', fail_second)
    with pytest.raises(RuntimeError, match='second insert'):
        await run('grant', {'roleId': 20, 'userIds': [44, 43]})
    assert await relations() == before
