from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.post_do import PostDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO
from scripts.internal.bootstrap_seed import SeedDataManager


@pytest.fixture
async def seed_manager() -> SeedDataManager:
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
        manager = SeedDataManager(env='dev')
        manager.session = session
        yield manager
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_all_bootstrap_only_skips_managed_reference_data(seed_manager: SeedDataManager) -> None:
    await seed_manager.seed_all()
    await seed_manager.session.flush()

    dept_ids = (await seed_manager.session.execute(select(DeptDO.dept_id))).scalars().all()
    post_ids = (await seed_manager.session.execute(select(PostDO.post_id))).scalars().all()
    role_ids = (await seed_manager.session.execute(select(RoleDO.role_id))).scalars().all()
    user_ids = (await seed_manager.session.execute(select(UserDO.user_id))).scalars().all()
    menu_ids = (await seed_manager.session.execute(select(MenuDO.menu_id))).scalars().all()
    role_menu_pairs = (await seed_manager.session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    dict_type_ids = (await seed_manager.session.execute(select(DictTypeDO.dict_id))).scalars().all()
    dict_data_codes = (await seed_manager.session.execute(select(DictDataDO.dict_code))).scalars().all()
    config_ids = (await seed_manager.session.execute(select(ConfigDO.config_id))).scalars().all()

    assert dept_ids
    assert post_ids
    assert role_ids == [1, 2]
    assert user_ids == [1, 2]
    assert menu_ids == []
    assert role_menu_pairs == []
    assert dict_type_ids == []
    assert dict_data_codes == []
    assert config_ids == []


@pytest.mark.asyncio
async def test_clear_data_preserves_managed_reference_data(seed_manager: SeedDataManager) -> None:
    await seed_manager.seed_all()

    seed_manager.session.add(
        MenuDO(
            menu_id=9000,
            menu_name='受管菜单',
            parent_id=0,
            order_num=1,
            path='managed',
            component='managed/index',
            menu_type='C',
            visible='0',
            status='0',
            perms='managed:list',
            icon='menu',
            managed_by_seed=1,
            remark='managed',
        )
    )
    seed_manager.session.add(
        RoleMenuDO(
            role_id=2,
            menu_id=9000,
        )
    )
    seed_manager.session.add(
        DictTypeDO(
            dict_id=9000,
            dict_name='受管字典',
            dict_type='managed_status',
            status='0',
            remark='managed',
        )
    )
    seed_manager.session.add(
        DictDataDO(
            dict_code=9000,
            dict_sort=1,
            dict_label='启用',
            dict_value='enabled',
            dict_type='managed_status',
            css_class='',
            list_class='success',
            is_default='Y',
            status='0',
            remark='managed',
        )
    )
    seed_manager.session.add(
        ConfigDO(
            config_id=9000,
            config_name='受管配置',
            config_key='managed.timeout',
            config_value='30',
            config_type='Y',
            remark='managed',
        )
    )
    await seed_manager.session.flush()

    await seed_manager.clear_data()
    await seed_manager.session.flush()

    remaining_roles = (await seed_manager.session.execute(select(RoleDO.role_id))).scalars().all()
    remaining_users = (await seed_manager.session.execute(select(UserDO.user_id))).scalars().all()
    remaining_depts = (await seed_manager.session.execute(select(DeptDO.dept_id))).scalars().all()
    remaining_posts = (await seed_manager.session.execute(select(PostDO.post_id))).scalars().all()
    remaining_menus = (await seed_manager.session.execute(select(MenuDO.menu_id))).scalars().all()
    remaining_role_menus = (await seed_manager.session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    remaining_dict_types = (await seed_manager.session.execute(select(DictTypeDO.dict_type))).scalars().all()
    remaining_configs = (await seed_manager.session.execute(select(ConfigDO.config_key))).scalars().all()

    assert remaining_roles == []
    assert remaining_users == []
    assert remaining_depts == []
    assert remaining_posts == []
    assert remaining_menus == [9000]
    assert remaining_role_menus == [(2, 9000)]
    assert remaining_dict_types == ['managed_status']
    assert remaining_configs == ['managed.timeout']
