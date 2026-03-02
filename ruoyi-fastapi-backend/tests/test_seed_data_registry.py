from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from modules.system.runtime.menu_registry_loader import MenuRegistryLoader
from scripts.seed_data import SeedDataManager


def _write_registry(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _menu_payload(menu_id: int, name: str) -> dict:
    return {
        'menu_id': menu_id,
        'menu_name': name,
        'parent_id': 0,
        'order_num': menu_id,
        'path': f'menu-{menu_id}',
        'component': f'system/menu/{menu_id}',
        'query': None,
        'route_name': '',
        'is_frame': 1,
        'is_cache': 0,
        'menu_type': 'C',
        'visible': '0',
        'status': '0',
        'perms': '',
        'icon': 'menu',
        'remark': '',
        'managed_by_seed': True,
    }


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
async def test_seed_entity_menus_uses_registry_source(seed_manager: SeedDataManager, tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu_payload(6100, 'RegistryMenu')],
            'role_grants': [],
        },
    )

    seed_manager.registry_path = registry_file
    seed_manager.menu_registry_loader = MenuRegistryLoader(registry_file)
    seed_manager._registry_payload = None

    await seed_manager.seed_entity('menus')
    await seed_manager.session.flush()

    rows = (await seed_manager.session.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
    menu_map = {row.menu_id: row.menu_name for row in rows}
    assert menu_map[6100] == 'RegistryMenu'


@pytest.mark.asyncio
async def test_seed_role_menus_maps_role_key_to_role_id(seed_manager: SeedDataManager, tmp_path: Path) -> None:
    seed_manager.session.add(
        RoleDO(
            role_id=71,
            role_name='Common',
            role_key='common',
            role_sort=1,
            status='0',
            del_flag='0',
        )
    )
    await seed_manager.session.flush()

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu_payload(6200, 'RegistryRoleMenu')],
            'role_grants': [{'role_key': 'common', 'menu_ids': [6200]}],
        },
    )

    seed_manager.registry_path = registry_file
    seed_manager.menu_registry_loader = MenuRegistryLoader(registry_file)
    seed_manager._registry_payload = None

    await seed_manager.seed_role_menus()
    await seed_manager.session.flush()

    rows = (await seed_manager.session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    assert {(row.role_id, row.menu_id) for row in rows} == {(71, 6200)}


@pytest.mark.asyncio
async def test_seed_role_menus_fails_for_missing_role_key(seed_manager: SeedDataManager, tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu_payload(6300, 'RegistryRoleMenu')],
            'role_grants': [{'role_key': 'missing', 'menu_ids': [6300]}],
        },
    )

    seed_manager.registry_path = registry_file
    seed_manager.menu_registry_loader = MenuRegistryLoader(registry_file)
    seed_manager._registry_payload = None

    with pytest.raises(ValueError, match='missing'):
        await seed_manager.seed_role_menus()
