"""User service unit tests for the repository-based architecture."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config.constant import CommonConstant
from exceptions.exception import PermissionException
from module_admin.entity.vo.user_vo import UserModel
from modules.system.application.services.user_service import UserService


@pytest.mark.asyncio
async def test_check_user_allowed_blocks_admin_user():
    admin_user = UserModel(userId=1)
    service = UserService()

    with pytest.raises(PermissionException):
        await service.check_user_allowed_services(admin_user)


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
