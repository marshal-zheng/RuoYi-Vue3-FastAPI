from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.database import Base
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.db_workflow_do import DbWorkflowArtifactDO, DbWorkflowObjectDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from scripts.internal.db_workflow.capability_models import (
    CapabilityCompilationChecksums,
    CapabilityResourceState,
    CompiledCapabilityState,
    ModuleCapabilityDeclaration,
)
from scripts.internal.db_workflow.deploy_release_service import _execute_release_deploy_async
from scripts.internal.db_workflow.managed_data_planner import ManagedDataOperation, ManagedDataPlan
from scripts.internal.db_workflow.release_bundle_service import (
    ReleaseBundleService,
    build_managed_data_payload,
    build_managed_object_snapshot,
    build_release_manifest_payload,
)

if TYPE_CHECKING:
    from pathlib import Path

from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataTargetState, ReleasePlanSelection


def _menu_target(menu_id: int, name: str, parent_id: int = 0, menu_type: str = 'C') -> dict[str, object]:
    return {
        'menu_id': menu_id,
        'menu_name': name,
        'parent_id': parent_id,
        'order_num': menu_id,
        'path': f'menu-{menu_id}',
        'component': None if menu_type == 'M' else f'system/menu/{menu_id}',
        'query': None,
        'route_name': '',
        'is_frame': 1,
        'is_cache': 0,
        'menu_type': menu_type,
        'visible': '0',
        'status': '0',
        'perms': '' if menu_type == 'M' else f'system:menu:{menu_id}',
        'icon': 'menu',
        'remark': '',
    }


def _target_state() -> ManagedDataTargetState:
    return ManagedDataTargetState(
        menus={
            1: _menu_target(1, '系统管理', menu_type='M'),
            100: _menu_target(100, '参数配置', parent_id=1),
        },
        role_grants={'common': (100,)},
        dict_types={
            'sys_device_status': {
                'dict_id': 1,
                'dict_name': '设备状态',
                'dict_type': 'sys_device_status',
                'status': '0',
                'remark': '',
            }
        },
        dict_data={
            ('sys_device_status', 'enabled'): {
                'dict_code': 1,
                'dict_sort': 1,
                'dict_label': '启用',
                'dict_value': 'enabled',
                'dict_type': 'sys_device_status',
                'css_class': '',
                'list_class': 'success',
                'is_default': 'Y',
                'status': '0',
                'remark': '',
            }
        },
        configs={
            'device.default.timeout': {
                'config_id': 1,
                'config_name': '设备默认超时',
                'config_key': 'device.default.timeout',
                'config_value': '30',
                'config_type': 'Y',
                'remark': '',
            }
        },
    )


def _release_selection() -> ReleasePlanSelection:
    return ReleasePlanSelection(
        version='2',
        release_key='2026-04-device-config',
        menu_ids=(100,),
        role_grants={'common': (100,)},
        dict_types=('sys_device_status',),
        config_keys=('device.default.timeout',),
        modules={'platform': True},
        enabled_modules=('platform',),
        compiled_checksum='compiled-sha',
        release_plan_checksum='release-plan-sha',
    )


def _bundle_plan() -> ManagedDataPlan:
    return ManagedDataPlan(
        operations=(
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_menu',
                object_key='sys_menu:1',
                match_fields={'menu_id': 1},
                values=_menu_target(1, '系统管理', menu_type='M'),
            ),
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_menu',
                object_key='sys_menu:100',
                match_fields={'menu_id': 100},
                values=_menu_target(100, '参数配置', parent_id=1),
            ),
            ManagedDataOperation(
                op_type='ensure-link',
                entity_type='sys_role_menu',
                object_key='sys_role_menu:2:100',
                match_fields={'role_id': 2, 'menu_id': 100},
                values={'role_id': 2, 'menu_id': 100},
            ),
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_dict_type',
                object_key='sys_dict_type:1',
                match_fields={'dict_id': 1},
                values=_target_state().dict_types['sys_device_status'],
            ),
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_dict_data',
                object_key='sys_dict_data:1',
                match_fields={'dict_code': 1},
                values=_target_state().dict_data[('sys_device_status', 'enabled')],
            ),
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_config',
                object_key='sys_config:1',
                match_fields={'config_id': 1},
                values=_target_state().configs['device.default.timeout'],
            ),
        )
    )


def _compiled_state(tmp_path: Path) -> CompiledCapabilityState:
    resources = CapabilityResourceState(
        menus=_target_state().menus,
        role_grants=_target_state().role_grants,
        dict_types=_target_state().dict_types,
        dict_data=_target_state().dict_data,
        configs=_target_state().configs,
    )
    declaration = ModuleCapabilityDeclaration(
        module_key='platform',
        source_path=tmp_path / 'capabilities' / 'modules' / 'platform.module.yaml',
        resources=resources,
    )
    return CompiledCapabilityState(
        modules={'platform': declaration},
        resources=resources,
        runtime_gates={},
        checksums=CapabilityCompilationChecksums(
            source_checksum='source-sha',
            compiled_checksum='compiled-sha',
        ),
    )


async def _create_session_factory():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(bind=engine, expire_on_commit=False), engine


async def _seed_roles(session_factory) -> None:
    async with session_factory() as session:
        session.add(
            RoleDO(
                role_id=2,
                role_name='普通角色',
                role_key='common',
                role_sort=2,
                status='0',
                del_flag='0',
            )
        )
        await session.commit()


def _write_bundle(output_root: Path, *, invalid_manifest: bool = False) -> None:
    target_state = _target_state()
    release_selection = _release_selection()
    compiled_state = _compiled_state(output_root.parent)
    manifest_target_state = (
        ManagedDataTargetState(
            menus={999: _menu_target(999, '损坏菜单', parent_id=1)},
            role_grants={'common': (999,)},
            dict_types=target_state.dict_types,
            dict_data=target_state.dict_data,
            configs=target_state.configs,
        )
        if invalid_manifest
        else target_state
    )
    ReleaseBundleService(output_root=output_root).write_bundle(
        bundle_id='20260402_001_device-release',
        bundle_kind='release',
        schema_revision='20260402_head',
        release_key=release_selection.release_key,
        managed_data_payload=build_managed_data_payload(
            '20260402_001_device-release',
            _bundle_plan(),
            target_state=target_state,
            release_selection=release_selection,
            managed_objects=build_managed_object_snapshot(
                compiled_state=compiled_state,
                enabled_modules=release_selection.enabled_modules,
            ),
        ),
        release_manifest_payload=build_release_manifest_payload(
            '20260402_001_device-release',
            target_state=manifest_target_state,
            release_selection=release_selection,
            selection_mode='release-plan',
        ),
        message='device release',
    )


def _write_bootstrap_roles(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                'roles': [
                    {
                        'role_id': 2,
                        'role_name': '普通角色',
                        'role_key': 'common',
                        'role_sort': 2,
                        'status': '0',
                        'del_flag': '0',
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding='utf-8',
    )


async def test_execute_release_deploy_applies_bundles_and_records_history(tmp_path: Path) -> None:
    output_root = tmp_path / 'releases'
    _write_bundle(output_root)
    session_factory, engine = await _create_session_factory()
    try:
        await _seed_roles(session_factory)

        first = await _execute_release_deploy_async(
            output_root=output_root,
            session_factory=session_factory,
            actor='db_workflow',
        )
        assert first.deploy_result == 'success'
        assert first.compiled_checksums == ('compiled-sha',)
        assert first.release_plan_checksums == ('release-plan-sha',)
        assert first.managed_data.result == 'applied'
        assert first.release_manifest.result == 'applied'
        assert first.postcondition_verify.result == 'clean'
        assert first.applied_bundle_ids == ('20260402_001_device-release',)

        async with session_factory() as session:
            menu_ids = (await session.execute(select(MenuDO.menu_id))).scalars().all()
            role_menu_pairs = (await session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
            dict_types = (await session.execute(select(DictTypeDO.dict_type))).scalars().all()
            dict_values = (await session.execute(select(DictDataDO.dict_value))).scalars().all()
            config_keys = (await session.execute(select(ConfigDO.config_key))).scalars().all()
            artifacts = (await session.execute(select(DbWorkflowArtifactDO))).scalars().all()
            workflow_objects = (await session.execute(select(DbWorkflowObjectDO))).scalars().all()

            assert menu_ids == [1, 100]
            assert role_menu_pairs == [(2, 100)]
            assert dict_types == ['sys_device_status']
            assert dict_values == ['enabled']
            assert config_keys == ['device.default.timeout']
            assert {(row.bundle_id, row.artifact_type, row.apply_status) for row in artifacts} == {
                ('20260402_001_device-release', 'managed-data', 'success'),
                ('20260402_001_device-release', 'release-manifest', 'success'),
            }
            assert {
                (row.object_type, row.object_key, row.active_flag, row.module_key, row.object_domain)
                for row in workflow_objects
            } == {
                ('sys_menu', '1', 'Y', 'platform', 'menus'),
                ('sys_menu', '100', 'Y', 'platform', 'menus'),
                ('sys_role_menu', 'common:100', 'Y', 'platform', 'role_grants'),
                ('sys_dict_type', 'sys_device_status', 'Y', 'platform', 'dict_types'),
                ('sys_dict_data', 'sys_device_status:enabled', 'Y', 'platform', 'dict_data'),
                ('sys_config', 'device.default.timeout', 'Y', 'platform', 'configs'),
            }
            assert all(row.source_checksum for row in workflow_objects)

        second = await _execute_release_deploy_async(
            output_root=output_root,
            session_factory=session_factory,
            actor='db_workflow',
        )
        assert second.deploy_result == 'success'
        assert second.managed_data.result == 'no-op'
        assert second.release_manifest.result == 'no-op'
        assert second.postcondition_verify.result == 'clean'
        assert second.skipped_bundle_ids == ('20260402_001_device-release',)
    finally:
        await engine.dispose()


async def test_execute_release_deploy_uses_bootstrap_roles_when_database_roles_are_missing(tmp_path: Path) -> None:
    output_root = tmp_path / 'releases'
    bootstrap_roles = tmp_path / 'seed_data' / 'base' / 'roles.yaml'
    _write_bundle(output_root)
    _write_bootstrap_roles(bootstrap_roles)

    session_factory, engine = await _create_session_factory()
    try:
        report = await _execute_release_deploy_async(
            output_root=output_root,
            session_factory=session_factory,
            actor='db_workflow',
            bootstrap_roles_path=bootstrap_roles,
        )
        assert report.deploy_result == 'success'
        assert report.managed_data.result == 'applied'
        assert report.release_manifest.result == 'applied'
        assert report.postcondition_verify.result == 'clean'

        async with session_factory() as session:
            role_ids = (await session.execute(select(RoleDO.role_id))).scalars().all()
            role_menu_pairs = (await session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()

            assert role_ids == []
            assert role_menu_pairs == [(2, 100)]
    finally:
        await engine.dispose()


async def test_execute_release_deploy_returns_noop_when_no_bundle_exists(tmp_path: Path) -> None:
    output_root = tmp_path / 'releases'
    session_factory, engine = await _create_session_factory()
    try:
        report = await _execute_release_deploy_async(
            output_root=output_root,
            session_factory=session_factory,
            actor='db_workflow',
        )
    finally:
        await engine.dispose()

    assert report.deploy_result == 'success'
    assert report.managed_data.result == 'no-op'
    assert report.release_manifest.result == 'no-op'
    assert report.postcondition_verify.result == 'no-op'
    assert report.applied_bundle_ids == ()
    assert report.skipped_bundle_ids == ()


async def test_execute_release_deploy_stops_when_release_manifest_is_invalid(tmp_path: Path) -> None:
    output_root = tmp_path / 'releases'
    _write_bundle(output_root, invalid_manifest=True)
    session_factory, engine = await _create_session_factory()
    try:
        await _seed_roles(session_factory)

        report = await _execute_release_deploy_async(
            output_root=output_root,
            session_factory=session_factory,
            actor='db_workflow',
        )
        assert report.deploy_result == 'failed'
        assert report.failed_step == 'release-manifest'
        assert report.managed_data.result == 'applied'
        assert report.release_manifest.result == 'failed'
        assert report.postcondition_verify.result == 'skipped'
        assert 'missing menu_ids' in (report.release_manifest.error or '')

        async with session_factory() as session:
            artifacts = (
                await session.execute(select(DbWorkflowArtifactDO.bundle_id, DbWorkflowArtifactDO.artifact_type))
            ).all()
            assert artifacts == [('20260402_001_device-release', 'managed-data')]
    finally:
        await engine.dispose()
