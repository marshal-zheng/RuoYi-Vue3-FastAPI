from unittest.mock import AsyncMock

import pytest

from modules.system.application.services.common_service import CommonService


@pytest.mark.asyncio
async def test_get_table_names_uses_injected_repository():
    fake_repo = AsyncMock()
    expected = [
        {'label': '系统用户表 (sys_user)', 'value': 'sys_user'},
        {'label': '系统角色表 (sys_role)', 'value': 'sys_role'},
    ]
    fake_repo.list_sys_tables.return_value = expected
    service = CommonService(common_repo=fake_repo)

    result = await service.get_table_names_services()

    assert result == expected
    fake_repo.list_sys_tables.assert_awaited_once()
