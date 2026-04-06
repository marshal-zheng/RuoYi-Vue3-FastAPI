from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from scripts.internal.db_workflow.managed_data_applier import ManagedDataApplier
from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataTargetState
from scripts.internal.db_workflow.managed_data_planner import (
    ManagedDataCurrentState,
    ManagedDataManagedScope,
    ManagedDataOperation,
    ManagedDataPlan,
    ManagedDataPlanner,
)


def _menu_target(menu_id: int, name: str) -> dict[str, Any]:
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
    }


def _dict_type_target(dict_id: int, dict_type: str, dict_name: str) -> dict[str, Any]:
    return {
        'dict_id': dict_id,
        'dict_name': dict_name,
        'dict_type': dict_type,
        'status': '0',
        'remark': '',
    }


def _dict_data_target(dict_code: int, dict_type: str, dict_value: str, dict_label: str) -> dict[str, Any]:
    return {
        'dict_code': dict_code,
        'dict_sort': 1,
        'dict_label': dict_label,
        'dict_value': dict_value,
        'dict_type': dict_type,
        'css_class': '',
        'list_class': 'success',
        'is_default': 'Y',
        'status': '0',
        'remark': '',
    }


def _config_target(config_id: int, config_key: str, config_value: str) -> dict[str, Any]:
    return {
        'config_id': config_id,
        'config_name': '设备默认超时',
        'config_key': config_key,
        'config_value': config_value,
        'config_type': 'Y',
        'remark': '',
    }


def _managed_target_state() -> ManagedDataTargetState:
    return ManagedDataTargetState(
        menus={
            10: _menu_target(10, 'updated-menu'),
            40: _menu_target(40, 'new-menu'),
        },
        role_grants={
            'common': (10, 40),
            'auditor': (10,),
        },
        dict_types={
            'sys_device_status': _dict_type_target(1, 'sys_device_status', '设备状态'),
        },
        dict_data={
            ('sys_device_status', 'enabled'): _dict_data_target(1, 'sys_device_status', 'enabled', '启用'),
        },
        configs={
            'device.default.timeout': _config_target(1, 'device.default.timeout', '30'),
        },
    )


def _planner_current_state() -> ManagedDataCurrentState:
    return ManagedDataCurrentState(
        menus_by_id={
            10: {**_menu_target(10, 'old-menu'), 'managed_by_seed': 1},
            30: {**_menu_target(30, 'legacy-menu'), 'managed_by_seed': 1},
            99: {**_menu_target(99, 'manual-menu'), 'managed_by_seed': 0},
        },
        role_menu_pairs={(2, 30)},
        dict_types_by_id={
            1: _dict_type_target(1, 'sys_device_status', '旧设备状态'),
            9: _dict_type_target(9, 'legacy_type', '历史字典'),
        },
        dict_type_ids_by_key={
            'sys_device_status': 1,
            'legacy_type': 9,
        },
        dict_data_by_code={
            1: _dict_data_target(1, 'sys_device_status', 'enabled', '旧启用'),
            9: _dict_data_target(9, 'legacy_type', 'legacy', '历史值'),
        },
        dict_data_codes_by_business_key={
            ('sys_device_status', 'enabled'): 1,
            ('legacy_type', 'legacy'): 9,
        },
        configs_by_id={
            1: _config_target(1, 'device.default.timeout', '60'),
            9: _config_target(9, 'legacy.config', 'legacy'),
        },
        config_ids_by_key={
            'device.default.timeout': 1,
            'legacy.config': 9,
        },
        managed_scope=ManagedDataManagedScope(
            menu_ids=frozenset({10, 30}),
            role_menu_pairs=frozenset({(2, 30)}),
            dict_type_ids=frozenset({1, 9}),
            dict_data_codes=frozenset({1, 9}),
            config_ids=frozenset({1, 9}),
        ),
    )


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


def test_planner_builds_normalized_operations_for_full_diff() -> None:
    planner = ManagedDataPlanner()

    plan = planner.plan(
        current_state=_planner_current_state(),
        target_state=_managed_target_state(),
        role_key_to_id={'common': 2, 'auditor': 3},
    )

    assert plan.operation_count == 13
    assert plan.count(op_type='upsert-row', entity_type='sys_menu') == 2
    assert plan.count(op_type='upsert-row', entity_type='sys_dict_type') == 1
    assert plan.count(op_type='upsert-row', entity_type='sys_dict_data') == 1
    assert plan.count(op_type='upsert-row', entity_type='sys_config') == 1
    assert plan.count(op_type='ensure-link', entity_type='sys_role_menu') == 3
    assert plan.count(op_type='remove-link', entity_type='sys_role_menu') == 1
    assert plan.count(op_type='delete-row', entity_type='sys_menu') == 1
    assert plan.count(op_type='delete-row', entity_type='sys_dict_type') == 1
    assert plan.count(op_type='delete-row', entity_type='sys_dict_data') == 1
    assert plan.count(op_type='delete-row', entity_type='sys_config') == 1

    operation_keys = {operation.object_key for operation in plan.operations}
    assert 'sys_menu:30' in operation_keys
    assert 'sys_role_menu:2:30' in operation_keys
    assert 'sys_menu:99' not in operation_keys


@pytest.mark.asyncio
async def test_applier_load_current_state_requires_metadata_scope_for_prune(test_db: AsyncSession) -> None:
    test_db.add(MenuDO(**_menu_target(30, 'legacy-menu'), managed_by_seed=1))
    await test_db.commit()

    current_state = await ManagedDataApplier(test_db).load_current_state()

    assert current_state.managed_scope.menu_ids == frozenset()


def test_planner_rejects_missing_role_key() -> None:
    planner = ManagedDataPlanner()

    with pytest.raises(ValueError, match='role_key not found'):
        planner.plan(
            current_state=_planner_current_state(),
            target_state=_managed_target_state(),
            role_key_to_id={'common': 2},
        )


def test_planner_rejects_config_business_key_conflict() -> None:
    planner = ManagedDataPlanner()
    current_state = _planner_current_state()
    current_state.configs_by_id[8] = _config_target(8, 'device.default.timeout', '15')
    current_state.config_ids_by_key['device.default.timeout'] = 8

    with pytest.raises(ValueError, match=r'config_key "device\.default\.timeout" already exists'):
        planner.plan(
            current_state=current_state,
            target_state=_managed_target_state(),
            role_key_to_id={'common': 2, 'auditor': 3},
        )


def test_planner_tolerates_duplicate_dict_data_business_key_when_expected_code_exists() -> None:
    planner = ManagedDataPlanner()
    current_state = _planner_current_state()
    current_state.dict_data_by_code[1] = _dict_data_target(1, 'sys_device_status', 'enabled', '启用')
    current_state.dict_data_by_code[11] = _dict_data_target(11, 'sys_device_status', 'enabled', '启用')
    current_state.dict_data_codes_by_business_key[('sys_device_status', 'enabled')] = 11
    current_state = replace(
        current_state,
        managed_scope=ManagedDataManagedScope(
            menu_ids=current_state.managed_scope.menu_ids,
            role_menu_pairs=current_state.managed_scope.role_menu_pairs,
            dict_type_ids=current_state.managed_scope.dict_type_ids,
            dict_data_codes=frozenset({1, 9, 11}),
            config_ids=current_state.managed_scope.config_ids,
        ),
    )

    plan = planner.plan(
        current_state=current_state,
        target_state=_managed_target_state(),
        role_key_to_id={'common': 2, 'auditor': 3},
    )

    delete_operations = {
        operation.object_key
        for operation in plan.operations
        if operation.op_type == 'delete-row' and operation.entity_type == 'sys_dict_data'
    }
    upsert_operations = {
        operation.object_key
        for operation in plan.operations
        if operation.op_type == 'upsert-row' and operation.entity_type == 'sys_dict_data'
    }

    assert 'sys_dict_data:11' in delete_operations
    assert 'sys_dict_data:1' not in upsert_operations


@pytest.mark.asyncio
async def test_applier_dry_run_apply_and_reapply_are_idempotent(test_db: AsyncSession) -> None:
    test_db.add_all(
        [
            _role_payload(2, 'common'),
            _role_payload(3, 'auditor'),
            MenuDO(**_menu_target(10, 'old-menu'), managed_by_seed=1),
            MenuDO(**_menu_target(30, 'legacy-menu'), managed_by_seed=1),
            MenuDO(**_menu_target(99, 'manual-menu'), managed_by_seed=0),
            RoleMenuDO(role_id=2, menu_id=30),
            RoleMenuDO(role_id=2, menu_id=99),
            DictTypeDO(**_dict_type_target(1, 'sys_device_status', '旧设备状态')),
            DictTypeDO(**_dict_type_target(9, 'legacy_type', '历史字典')),
            DictDataDO(**_dict_data_target(1, 'sys_device_status', 'enabled', '旧启用')),
            DictDataDO(**_dict_data_target(9, 'legacy_type', 'legacy', '历史值')),
            ConfigDO(**_config_target(1, 'device.default.timeout', '60')),
            ConfigDO(**_config_target(9, 'legacy.config', 'legacy')),
        ]
    )
    await test_db.commit()

    managed_scope = ManagedDataManagedScope(
        menu_ids=frozenset({10, 30}),
        role_menu_pairs=frozenset({(2, 30)}),
        dict_type_ids=frozenset({1, 9}),
        dict_data_codes=frozenset({1, 9}),
        config_ids=frozenset({1, 9}),
    )
    applier = ManagedDataApplier(test_db)
    planner = ManagedDataPlanner()
    plan = planner.plan(
        current_state=await applier.load_current_state(managed_scope),
        target_state=_managed_target_state(),
        role_key_to_id={'common': 2, 'auditor': 3},
    )

    dry_run_report = await applier.apply_plan(plan, dry_run=True, managed_scope=managed_scope)

    assert dry_run_report.dry_run is True
    assert dry_run_report.applied_operations == 0
    assert dry_run_report.skipped_operations == plan.operation_count

    menu_names_before = {
        row.menu_id: row.menu_name
        for row in (await test_db.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
    }
    assert menu_names_before[10] == 'old-menu'
    assert 30 in menu_names_before
    assert 40 not in menu_names_before

    apply_report = await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)

    assert apply_report.dry_run is False
    assert apply_report.applied_operations == plan.operation_count
    assert apply_report.skipped_operations == 0

    menu_names_after = {
        row.menu_id: row.menu_name
        for row in (await test_db.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
    }
    assert menu_names_after[10] == 'updated-menu'
    assert 30 not in menu_names_after
    assert menu_names_after[40] == 'new-menu'
    assert menu_names_after[99] == 'manual-menu'

    role_menu_pairs = {
        (row.role_id, row.menu_id)
        for row in (await test_db.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
    }
    assert role_menu_pairs == {(2, 10), (2, 40), (2, 99), (3, 10)}

    dict_type_rows = {
        row.dict_id: (row.dict_type, row.dict_name)
        for row in (await test_db.execute(select(DictTypeDO))).scalars().all()
    }
    assert dict_type_rows == {1: ('sys_device_status', '设备状态')}

    dict_data_rows = {
        row.dict_code: (row.dict_type, row.dict_value, row.dict_label)
        for row in (await test_db.execute(select(DictDataDO))).scalars().all()
    }
    assert dict_data_rows == {1: ('sys_device_status', 'enabled', '启用')}

    config_rows = {
        row.config_id: (row.config_key, row.config_value)
        for row in (await test_db.execute(select(ConfigDO))).scalars().all()
    }
    assert config_rows == {1: ('device.default.timeout', '30')}

    reapply_report = await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)

    assert reapply_report.applied_operations == 0
    assert reapply_report.skipped_operations == plan.operation_count


@pytest.mark.asyncio
async def test_applier_rejects_unmanaged_prune_before_write(test_db: AsyncSession) -> None:
    test_db.add(DictTypeDO(**_dict_type_target(5, 'manual_type', '人工字典')))
    await test_db.commit()

    plan = ManagedDataPlan(
        operations=(
            ManagedDataOperation(
                op_type='delete-row',
                entity_type='sys_dict_type',
                object_key='sys_dict_type:5',
                match_fields={'dict_id': 5},
                values={},
            ),
        )
    )

    applier = ManagedDataApplier(test_db)
    with pytest.raises(ValueError, match='cannot prune unmanaged dict_type dict_id=5'):
        await applier.apply_plan(plan, dry_run=True)

    remaining = (await test_db.execute(select(DictTypeDO.dict_id))).scalars().all()
    assert remaining == [5]


@pytest.mark.asyncio
async def test_applier_prunes_duplicate_dict_data_business_key_when_expected_code_exists(test_db: AsyncSession) -> None:
    test_db.add_all(
        [
            _role_payload(2, 'common'),
            _role_payload(3, 'auditor'),
            DictTypeDO(**_dict_type_target(1, 'sys_device_status', '设备状态')),
            DictDataDO(**_dict_data_target(1, 'sys_device_status', 'enabled', '启用')),
            DictDataDO(**_dict_data_target(11, 'sys_device_status', 'enabled', '启用')),
        ]
    )
    await test_db.commit()

    managed_scope = ManagedDataManagedScope(
        dict_type_ids=frozenset({1}),
        dict_data_codes=frozenset({1, 11}),
    )
    applier = ManagedDataApplier(test_db)
    planner = ManagedDataPlanner()

    target_state = ManagedDataTargetState(
        menus={},
        role_grants={},
        dict_types={'sys_device_status': _dict_type_target(1, 'sys_device_status', '设备状态')},
        dict_data={('sys_device_status', 'enabled'): _dict_data_target(1, 'sys_device_status', 'enabled', '启用')},
        configs={},
    )

    plan = planner.plan(
        current_state=await applier.load_current_state(managed_scope),
        target_state=target_state,
        role_key_to_id={'common': 2, 'auditor': 3},
    )
    report = await applier.apply_plan(plan, dry_run=False, managed_scope=managed_scope)

    remaining_rows = {
        row.dict_code: (row.dict_type, row.dict_value)
        for row in (await test_db.execute(select(DictDataDO))).scalars().all()
    }

    assert report.applied_operations == 1
    assert remaining_rows == {1: ('sys_device_status', 'enabled')}
