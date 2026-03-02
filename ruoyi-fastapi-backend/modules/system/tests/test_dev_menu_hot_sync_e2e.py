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
from module_admin.entity.do.user_do import UserDO, UserRoleDO


def _write_yaml(path: Path, payload: dict) -> None:
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
        'perms': f'system:menu:{menu_id}',
        'icon': 'menu',
        'remark': '',
        'managed_by_seed': True,
    }


def _registry_payload(menus: list[dict], role_key: str, menu_ids: list[int]) -> dict:
    return {
        'version': '1',
        'menus': menus,
        'role_grants': [
            {
                'role_key': role_key,
                'menu_ids': menu_ids,
            }
        ],
    }


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
async def test_menu_sync_and_signature_change_flow(test_db: AsyncSession, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService
    from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService

    user_id = 8200
    role_id = 8300
    role_key = 'dev-e2e'
    old_menu_id = 8400
    new_menu_id = 8500

    test_db.add(
        UserDO(
            user_id=user_id,
            user_name='dev-e2e',
            nick_name='dev-e2e',
            password='test',
            status='0',
            del_flag='0',
        )
    )
    test_db.add(
        RoleDO(
            role_id=role_id,
            role_name='dev-e2e-role',
            role_key=role_key,
            role_sort=1,
            status='0',
            del_flag='0',
        )
    )
    test_db.add(UserRoleDO(user_id=user_id, role_id=role_id))
    test_db.add(RoleMenuDO(role_id=role_id, menu_id=old_menu_id))
    await test_db.flush()

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(registry_file, _registry_payload([_menu_payload(old_menu_id, 'old-menu')], role_key, [old_menu_id]))

    reconcile_service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)
    signature_service = DevMenuSignatureService(query_db=test_db)

    first_report = await reconcile_service.sync_once(trigger='startup', dry_run=False)
    assert first_report.success is True

    signature_before = await signature_service.get_user_signature(user_id)

    _write_yaml(registry_file, _registry_payload([_menu_payload(new_menu_id, 'new-menu')], role_key, [new_menu_id]))
    second_report = await reconcile_service.sync_once(trigger='file_change', dry_run=False)
    assert second_report.success is True
    assert second_report.deleted == 1
    assert second_report.role_menu_deleted == 1

    signature_after = await signature_service.get_user_signature(user_id)

    menu_ids = {
        row.menu_id
        for row in (await test_db.execute(select(MenuDO.menu_id))).all()
    }
    role_menu_pairs = {
        (row.role_id, row.menu_id)
        for row in (await test_db.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    }

    assert old_menu_id not in menu_ids
    assert new_menu_id in menu_ids
    assert (role_id, old_menu_id) not in role_menu_pairs
    assert (role_id, new_menu_id) in role_menu_pairs
    assert signature_before != signature_after
