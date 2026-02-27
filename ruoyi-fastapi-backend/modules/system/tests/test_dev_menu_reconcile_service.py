from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleMenuDO


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding='utf-8')


def _menu_payload(menu_id: int, name: str, *, managed: bool) -> dict:
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
        'managed_by_seed': managed,
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
async def test_load_target_menus_merges_overlay(tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    base_file = tmp_path / 'base' / 'menus.yaml'
    overlay_file = tmp_path / 'overlays' / 'dev.yaml'
    _write_yaml(base_file, {'menus': [_menu_payload(10, 'base-name', managed=True)]})
    _write_yaml(
        overlay_file,
        {'menus': [_menu_payload(10, 'overlay-name', managed=True), _menu_payload(20, 'new-menu', managed=True)]},
    )

    service = DevMenuReconcileService(query_db=None, base_menu_file=base_file, overlay_file=overlay_file)
    merged = service.load_target_menus()
    names = {item['menu_id']: item['menu_name'] for item in merged}

    assert names[10] == 'overlay-name'
    assert names[20] == 'new-menu'


@pytest.mark.asyncio
async def test_load_target_menus_overlay_partial_update_keeps_base_scope(tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    base_file = tmp_path / 'base' / 'menus.yaml'
    overlay_file = tmp_path / 'overlays' / 'dev.yaml'
    _write_yaml(base_file, {'menus': [_menu_payload(10, 'base-name', managed=True)]})
    _write_yaml(
        overlay_file,
        {'menus': [{'menu_id': 10, 'menu_name': 'overlay-name'}]},
    )

    service = DevMenuReconcileService(query_db=None, base_menu_file=base_file, overlay_file=overlay_file)
    merged = service.load_target_menus()
    menu = {item['menu_id']: item for item in merged}[10]

    assert menu['menu_name'] == 'overlay-name'
    assert menu['component'] == 'system/menu/10'
    assert menu['managed_by_seed'] == 1


@pytest.mark.asyncio
async def test_sync_once_upserts_and_prunes_managed_scope(test_db, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    # Existing managed menu: should update
    test_db.add(
        MenuDO(
            menu_id=10,
            menu_name='old-name',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='menu-10',
        )
    )
    # Existing managed menu not in target: should prune
    test_db.add(
        MenuDO(
            menu_id=30,
            menu_name='to-be-removed',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='menu-30',
        )
    )
    test_db.add(RoleMenuDO(role_id=2, menu_id=30))
    # Existing unmanaged menu: should remain untouched
    test_db.add(
        MenuDO(
            menu_id=99,
            menu_name='manual-menu',
            managed_by_seed=0,
            menu_type='C',
            status='0',
            visible='0',
            path='manual-99',
        )
    )
    await test_db.flush()

    base_file = tmp_path / 'base' / 'menus.yaml'
    overlay_file = tmp_path / 'overlays' / 'dev.yaml'
    _write_yaml(base_file, {'menus': [_menu_payload(10, 'updated-name', managed=True), _menu_payload(40, 'new-menu', managed=True)]})
    _write_yaml(overlay_file, {})

    service = DevMenuReconcileService(query_db=test_db, base_menu_file=base_file, overlay_file=overlay_file)
    report = await service.sync_once(trigger='manual', dry_run=False)

    assert report.success is True
    assert report.added == 1
    assert report.updated == 1
    assert report.deleted == 1
    assert report.role_menu_deleted == 1

    menus = (await test_db.execute(select(MenuDO.menu_id, MenuDO.menu_name, MenuDO.managed_by_seed))).all()
    menus_map = {row.menu_id: row for row in menus}
    assert menus_map[10].menu_name == 'updated-name'
    assert 30 not in menus_map
    assert 40 in menus_map and menus_map[40].managed_by_seed == 1
    assert 99 in menus_map and menus_map[99].managed_by_seed == 0


@pytest.mark.asyncio
async def test_sync_once_dry_run_reports_diff_without_writing(test_db, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    test_db.add(
        MenuDO(
            menu_id=10,
            menu_name='old-name',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='menu-10',
        )
    )
    test_db.add(
        MenuDO(
            menu_id=30,
            menu_name='to-be-removed',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='menu-30',
        )
    )
    test_db.add(RoleMenuDO(role_id=2, menu_id=30))
    await test_db.flush()

    base_file = tmp_path / 'base' / 'menus.yaml'
    overlay_file = tmp_path / 'overlays' / 'dev.yaml'
    _write_yaml(base_file, {'menus': [_menu_payload(10, 'updated-name', managed=True), _menu_payload(40, 'new-menu', managed=True)]})
    _write_yaml(overlay_file, {})

    service = DevMenuReconcileService(query_db=test_db, base_menu_file=base_file, overlay_file=overlay_file)
    report = await service.sync_once(trigger='manual', dry_run=True)

    assert report.success is True
    assert report.added == 1
    assert report.updated == 1
    assert report.deleted == 1
    assert report.role_menu_deleted == 1

    menu_rows = (await test_db.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
    role_menu_rows = (await test_db.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    menu_names = {row.menu_id: row.menu_name for row in menu_rows}
    role_menus = {(row.role_id, row.menu_id) for row in role_menu_rows}

    assert menu_names[10] == 'old-name'
    assert 30 in menu_names
    assert 40 not in menu_names
    assert (2, 30) in role_menus


@pytest.mark.asyncio
async def test_sync_once_rolls_back_when_apply_changes_raises(test_db, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    test_db.add(
        MenuDO(
            menu_id=10,
            menu_name='stable',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='menu-10',
        )
    )
    await test_db.flush()
    await test_db.commit()

    base_file = tmp_path / 'base' / 'menus.yaml'
    overlay_file = tmp_path / 'overlays' / 'dev.yaml'
    _write_yaml(base_file, {'menus': [_menu_payload(10, 'updated-name', managed=True)]})
    _write_yaml(overlay_file, {})

    service = DevMenuReconcileService(query_db=test_db, base_menu_file=base_file, overlay_file=overlay_file)

    async def failing_apply(*_args, **_kwargs) -> int:
        test_db.add(
            MenuDO(
                menu_id=500,
                menu_name='temp',
                managed_by_seed=1,
                menu_type='C',
                status='0',
                visible='0',
                path='menu-500',
            )
        )
        await test_db.flush()
        raise RuntimeError('boom')

    service._apply_changes = failing_apply  # type: ignore[method-assign]
    report = await service.sync_once(trigger='manual', dry_run=False)

    assert report.success is False
    assert report.error is not None
    assert 'boom' in report.error

    menu_rows = (await test_db.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
    menu_names = {row.menu_id: row.menu_name for row in menu_rows}
    assert menu_names[10] == 'stable'
    assert 500 not in menu_names
