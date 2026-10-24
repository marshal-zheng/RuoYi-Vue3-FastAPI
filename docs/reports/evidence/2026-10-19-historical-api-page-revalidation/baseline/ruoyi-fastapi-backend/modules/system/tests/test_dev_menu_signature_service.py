from __future__ import annotations

import pytest

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
async def test_db() -> AsyncSession:
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(LegacyBaseModel.metadata.create_all)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_signature_is_deterministic_for_same_data(test_db) -> None:
    from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService

    test_db.add(
        UserDO(
            user_id=200,
            user_name='dev-user',
            nick_name='dev-user',
            password='test',
            status='0',
            del_flag='0',
        )
    )
    test_db.add(
        RoleDO(
            role_id=300,
            role_name='dev-role',
            role_key='dev',
            role_sort=1,
            status='0',
            del_flag='0',
        )
    )
    test_db.add(UserRoleDO(user_id=200, role_id=300))
    test_db.add(
        MenuDO(
            menu_id=400,
            menu_name='menu-a',
            parent_id=0,
            order_num=1,
            path='menu-a',
            component='system/menu/a',
            menu_type='C',
            status='0',
            visible='0',
            perms='system:menu:a',
        )
    )
    test_db.add(RoleMenuDO(role_id=300, menu_id=400))
    await test_db.flush()

    service = DevMenuSignatureService(query_db=test_db)
    signature_first = await service.get_user_signature(200)
    signature_second = await service.get_user_signature(200)

    assert signature_first == signature_second
    assert len(signature_first) == 64


@pytest.mark.asyncio
async def test_user_signature_changes_when_permission_graph_changes(test_db) -> None:
    from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService

    test_db.add(
        UserDO(
            user_id=201,
            user_name='dev-user-2',
            nick_name='dev-user-2',
            password='test',
            status='0',
            del_flag='0',
        )
    )
    test_db.add(
        RoleDO(
            role_id=301,
            role_name='dev-role-2',
            role_key='dev2',
            role_sort=1,
            status='0',
            del_flag='0',
        )
    )
    test_db.add(UserRoleDO(user_id=201, role_id=301))
    test_db.add(
        MenuDO(
            menu_id=401,
            menu_name='menu-b',
            parent_id=0,
            order_num=1,
            path='menu-b',
            component='system/menu/b',
            menu_type='C',
            status='0',
            visible='0',
            perms='system:menu:b',
        )
    )
    test_db.add(RoleMenuDO(role_id=301, menu_id=401))
    await test_db.flush()

    service = DevMenuSignatureService(query_db=test_db)
    signature_before = await service.get_user_signature(201)

    test_db.add(
        MenuDO(
            menu_id=402,
            menu_name='menu-c',
            parent_id=0,
            order_num=2,
            path='menu-c',
            component='system/menu/c',
            menu_type='C',
            status='0',
            visible='0',
            perms='system:menu:c',
        )
    )
    test_db.add(RoleMenuDO(role_id=301, menu_id=402))
    await test_db.flush()

    signature_after = await service.get_user_signature(201)
    assert signature_before != signature_after
