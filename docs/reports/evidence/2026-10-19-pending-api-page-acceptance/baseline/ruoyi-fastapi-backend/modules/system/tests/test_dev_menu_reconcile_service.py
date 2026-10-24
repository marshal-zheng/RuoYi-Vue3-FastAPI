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


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _menu_payload(menu_id: int, name: str, *, managed: bool = True) -> dict:
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


def _registry_payload(menus: list[dict], role_grants: list[dict] | None = None) -> dict:
    return {
        'version': '1',
        'menus': menus,
        'role_grants': role_grants or [],
    }


def _role_payload(role_id: int, role_key: str) -> RoleDO:
    return RoleDO(
        role_id=role_id,
        role_name=role_key,
        role_key=role_key,
        role_sort=role_id,
        status='0',
        del_flag='0',
    )


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
async def test_sync_once_upserts_and_prunes_managed_scope(test_db, tmp_path: Path) -> None:
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

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(registry_file, _registry_payload([_menu_payload(10, 'updated-name'), _menu_payload(40, 'new-menu')]))

    service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)
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

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(registry_file, _registry_payload([_menu_payload(10, 'updated-name'), _menu_payload(40, 'new-menu')]))

    service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)
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

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(registry_file, _registry_payload([_menu_payload(10, 'updated-name')]))

    service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)

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


@pytest.mark.asyncio
async def test_sync_once_reconciles_declared_role_menus_for_managed_scope(test_db, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    test_db.add(_role_payload(role_id=2, role_key='common'))
    test_db.add(_role_payload(role_id=3, role_key='auditor'))

    test_db.add(
        MenuDO(
            menu_id=600,
            menu_name='根目录',
            managed_by_seed=1,
            menu_type='M',
            status='0',
            visible='0',
            path='root-menu',
        )
    )
    test_db.add(
        MenuDO(
            menu_id=601,
            menu_name='子菜单',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='child-menu',
        )
    )
    test_db.add(
        MenuDO(
            menu_id=602,
            menu_name='陈旧菜单',
            managed_by_seed=1,
            menu_type='C',
            status='0',
            visible='0',
            path='stale',
        )
    )
    test_db.add(RoleMenuDO(role_id=2, menu_id=600))
    test_db.add(RoleMenuDO(role_id=2, menu_id=602))
    test_db.add(RoleMenuDO(role_id=3, menu_id=602))
    await test_db.flush()

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(
        registry_file,
            _registry_payload(
                [
                    _menu_payload(600, '根目录'),
                    _menu_payload(601, '子菜单'),
                    _menu_payload(602, '陈旧菜单'),
                ],
                role_grants=[
                    {
                        'role_key': 'common',
                        'menu_ids': [600, 601],
                    }
                ],
            ),
    )

    service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)
    report = await service.sync_once(trigger='manual', dry_run=False)

    assert report.success is True
    assert report.role_menu_deleted == 2

    role_menu_rows = (await test_db.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    role_menus = {(row.role_id, row.menu_id) for row in role_menu_rows}
    assert (2, 600) in role_menus
    assert (2, 601) in role_menus
    assert (2, 602) not in role_menus
    assert (3, 602) not in role_menus


@pytest.mark.asyncio
async def test_sync_once_fails_when_role_key_is_missing(test_db, tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    registry_file = tmp_path / 'menus.registry.yaml'
    _write_yaml(
        registry_file,
        _registry_payload(
            [_menu_payload(600, '根目录')],
            role_grants=[{'role_key': 'missing-role', 'menu_ids': [600]}],
        ),
    )

    service = DevMenuReconcileService(query_db=test_db, registry_file=registry_file)
    report = await service.sync_once(trigger='manual', dry_run=False)

    assert report.success is False
    assert report.error is not None
    assert 'missing-role' in report.error


@pytest.mark.asyncio
async def test_sync_once_commits_when_using_standalone_session(tmp_path: Path) -> None:
    from modules.system.runtime.dev_menu_reconcile_service import DevMenuReconcileService

    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(LegacyBaseModel.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)
    session = session_maker()
    try:
        registry_file = tmp_path / 'menus.registry.yaml'
        _write_yaml(registry_file, _registry_payload([_menu_payload(600, '根目录')]))

        service = DevMenuReconcileService(query_db=session, registry_file=registry_file)
        report = await service.sync_once(trigger='runtime_startup', dry_run=False)
        assert report.success is True
    finally:
        await session.close()

    async with session_maker() as verify_session:
        menu_rows = (await verify_session.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
        menu_names = {row.menu_id: row.menu_name for row in menu_rows}
        assert menu_names[600] == '根目录'

    await engine.dispose()
