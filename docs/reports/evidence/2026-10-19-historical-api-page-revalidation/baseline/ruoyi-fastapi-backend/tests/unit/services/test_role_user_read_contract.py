"""Role-side authorization lists retain the user's creation time through read projection."""

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from module_admin.entity.do.user_do import UserDO, UserRoleDO
from module_admin.entity.vo.user_vo import UserRolePageQueryModel
from modules.system.application.handlers.query.role_query_handlers import (
    GetRoleAllocatedUsersQueryHandler,
    GetRoleUnallocatedUsersQueryHandler,
)
from modules.system.application.queries.role_queries import (
    GetRoleAllocatedUsersQuery,
    GetRoleUnallocatedUsersQuery,
)
from modules.system.application.services.role_service import RoleService
from modules.system.infrastructure.user_repository import UserRepository
from utils.http_contract_responses import ok_page_result


@pytest.mark.parametrize('allocated', [True, False], ids=['allocated', 'unallocated'])
async def test_role_user_lists_include_user_creation_time(db_session, allocated):
    created_at = datetime(2026, 10, 17, 12, 34, 56)
    db_session.add(
        UserDO(
            user_id=42,
            user_name='authorization-user',
            nick_name='Authorization user',
            password='hash',
            create_time=created_at,
        )
    )
    if allocated:
        db_session.add(UserRoleDO(user_id=42, role_id=20))
    await db_session.flush()

    service = RoleService(AsyncMock(), AsyncMock(), AsyncMock(), UserRepository(db_session), db_session)
    handler_type = GetRoleAllocatedUsersQueryHandler if allocated else GetRoleUnallocatedUsersQueryHandler
    query_type = GetRoleAllocatedUsersQuery if allocated else GetRoleUnallocatedUsersQuery

    result = await handler_type(service).handle(
        query_type(query=UserRolePageQueryModel(roleId=20, page=1, pageSize=10))
    )

    assert result.total == 1
    assert result.items[0].user_id == 42
    response = ok_page_result(result)
    assert response.status_code == 200
    assert json.loads(response.body)['items'][0]['createTime'] == created_at.isoformat()
