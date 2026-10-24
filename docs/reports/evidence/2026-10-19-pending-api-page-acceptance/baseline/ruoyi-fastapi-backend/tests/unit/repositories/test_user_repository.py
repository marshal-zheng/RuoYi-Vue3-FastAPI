"""Management visibility must not determine whether an account can authenticate."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from exceptions.exception import AuthException
from module_admin.entity.do.user_do import UserDO
from modules.identity.application.services.login_service import LoginService
from modules.system.infrastructure.user_repository import UserRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'del_flag', 'management_visible', 'active_visible'),
    [
        ('0', '0', True, True),
        ('1', '0', True, False),
        ('0', '2', False, False),
        ('1', '2', False, False),
    ],
    ids=['enabled', 'disabled', 'deleted-enabled', 'deleted-disabled'],
)
async def test_related_user_visibility(db_session, status, del_flag, management_visible, active_visible):
    user = UserDO(
        user_name=f'visibility_{status}_{del_flag}',
        nick_name='Visibility regression',
        status=status,
        del_flag=del_flag,
    )
    db_session.add(user)
    await db_session.flush()
    repo = UserRepository(db_session)

    managed = await repo.get_user_with_relations(user.user_id)
    assert (managed['user_basic_info'] is not None) is management_visible
    if management_visible:
        assert managed['user_basic_info'].user_id == user.user_id
        assert managed['user_basic_info'].status == status

    active = await repo.get_user_with_relations(user.user_id, active_only=True)
    assert (active['user_basic_info'] is not None) is active_visible
    if active_visible:
        assert active['user_basic_info'].user_id == user.user_id


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['0', '1'], ids=['enabled', 'disabled'])
async def test_current_user_resolution_requires_enabled_account(db_session, monkeypatch, status):
    user = UserDO(
        user_name=f'token_visibility_{status}', nick_name='Token regression', status=status, password='test-password'
    )
    db_session.add(user)
    await db_session.flush()
    service = LoginService(query_db=db_session, user_repo=UserRepository(db_session))
    security = SimpleNamespace(
        verify_access_token=AsyncMock(return_value={'token_use': 'user_access', 'user_id': str(user.user_id)})
    )
    monkeypatch.setattr(service, '_resolve_security_service', lambda _context: security)

    if status == '1':
        with pytest.raises(AuthException):
            await service._resolve_current_user(None, 'already-issued-token')
    else:
        current = await service._resolve_current_user(None, 'already-issued-token')
        assert current.user.user_id == user.user_id
