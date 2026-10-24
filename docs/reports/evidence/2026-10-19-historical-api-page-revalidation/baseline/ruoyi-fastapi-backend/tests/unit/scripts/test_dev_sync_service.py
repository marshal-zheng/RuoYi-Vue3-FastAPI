from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.database import Base
from config.env import DataBaseWorkflowStatus
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.db_workflow_do import DbWorkflowObjectDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from scripts.internal.db_workflow import dev_sync_service
from scripts.internal.db_workflow.capability_models import (
    CapabilityCompilationChecksums,
    CapabilityResourceState,
    CompiledCapabilityState,
    ModuleCapabilityDeclaration,
)
from scripts.internal.db_workflow.managed_data_declaration_loader import (
    ManagedDataDeclarationBundle,
    ManagedDataDeclarationPaths,
    ManagedDataTargetState,
    ReleasePlanSelection,
)

if TYPE_CHECKING:
    from pathlib import Path


def _status() -> DataBaseWorkflowStatus:
    return DataBaseWorkflowStatus(
        workflow_mode='development',
        db_dev_sync_engine='atlas',
        db_target='sqlite:///:memory:',
        startup_action='dev-sync',
        deploy_path='python scripts/db.py deploy --revision head',
    )


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


def _bundle(tmp_path: Path, *, include_config: bool = True) -> ManagedDataDeclarationBundle:
    target_state = ManagedDataTargetState(
        menus={
            10: _menu_target(10, '系统管理', menu_type='M'),
            20: _menu_target(20, '参数配置', parent_id=10),
        },
        role_grants={'common': (20,)},
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
        }
        if include_config
        else {},
    )
    compiled_state = _compiled_capability_state(tmp_path, target_state, include_config=include_config)
    release_selection = ReleasePlanSelection(
        version='2',
        release_key='dev-sync-test',
        menu_ids=(10, 20),
        role_grants={'common': (20,)},
        dict_types=('sys_device_status',),
        config_keys=('device.default.timeout',) if include_config else (),
        modules={'platform': True},
        enabled_modules=('platform',),
        compiled_checksum=compiled_state.checksums.compiled_checksum,
        release_plan_checksum=f'release-plan-{int(include_config)}',
    )
    seed_root = tmp_path / 'seed_data'
    return ManagedDataDeclarationBundle(
        paths=ManagedDataDeclarationPaths(
            menu_registry=seed_root / 'menus.registry.yaml',
            dict_types=seed_root / 'base' / 'dict_types.yaml',
            dict_data=seed_root / 'base' / 'dict_data.yaml',
            configs=seed_root / 'base' / 'configs.yaml',
            release_plan=seed_root / 'release-plan.yaml',
            bootstrap_roles=seed_root / 'base' / 'roles.yaml',
            module_manifest_root=tmp_path / 'capabilities' / 'modules',
        ),
        managed_scopes=('menus', 'role_menus', 'dict_types', 'dict_data', 'configs', 'release_visibility'),
        bootstrap_scopes=('roles', 'users', 'depts', 'posts', 'user_roles', 'user_posts', 'role_depts'),
        bootstrap_role_keys=('common',),
        menu_registry=SimpleNamespace(),
        dev_target_state=target_state,
        formal_candidate_state=target_state,
        release_selection=release_selection,
        compiled_capability_state=compiled_state,
    )


def _compiled_capability_state(
    tmp_path: Path,
    target_state: ManagedDataTargetState,
    *,
    include_config: bool,
) -> CompiledCapabilityState:
    resources = CapabilityResourceState(
        menus=target_state.menus,
        role_grants=target_state.role_grants,
        dict_types=target_state.dict_types,
        dict_data=target_state.dict_data,
        configs=target_state.configs,
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
            source_checksum=f'source-sha-{int(include_config)}',
            compiled_checksum=f'compiled-sha-{int(include_config)}',
        ),
    )


def _build_session_factory():
    async def _factory():
        engine = create_async_engine(
            'sqlite+aiosqlite:///:memory:',
            echo=False,
            poolclass=StaticPool,
            connect_args={'check_same_thread': False},
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return engine, async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)

    return asyncio.run(_factory())


def _seed_roles(session_factory) -> None:
    async def _seed() -> None:
        async with session_factory() as session, session.begin():
            session.add(
                RoleDO(
                    role_id=2,
                    role_name='common',
                    role_key='common',
                    role_sort=2,
                    status='0',
                    del_flag='0',
                )
            )

    asyncio.run(_seed())


def _snapshot(session_factory) -> dict[str, object]:
    async def _collect() -> dict[str, object]:
        async with session_factory() as session:
            menus = {
                row.menu_id: row.menu_name
                for row in (await session.execute(select(MenuDO.menu_id, MenuDO.menu_name))).all()
            }
            role_menus = {
                (row.role_id, row.menu_id)
                for row in (await session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
            }
            dict_types = {
                row.dict_id: row.dict_type for row in (await session.execute(select(DictTypeDO))).scalars().all()
            }
            dict_data = {
                row.dict_code: (row.dict_type, row.dict_value)
                for row in (await session.execute(select(DictDataDO))).scalars().all()
            }
            configs = {
                row.config_id: row.config_key for row in (await session.execute(select(ConfigDO))).scalars().all()
            }
            workflow_objects = {
                (row.object_type, row.object_key): {
                    'active_flag': row.active_flag,
                    'module_key': row.module_key,
                    'object_domain': row.object_domain,
                    'source_checksum': row.source_checksum,
                }
                for row in (await session.execute(select(DbWorkflowObjectDO))).scalars().all()
            }
            return {
                'menus': menus,
                'role_menus': role_menus,
                'dict_types': dict_types,
                'dict_data': dict_data,
                'configs': configs,
                'workflow_objects': workflow_objects,
            }

    return asyncio.run(_collect())


def test_execute_dev_sync_applies_managed_data_and_tracks_metadata(monkeypatch, tmp_path: Path) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)

    runner_calls: dict[str, object] = {}

    def fake_runner(**kwargs) -> str:
        runner_calls.update(kwargs)
        return 'atlas_apply_success:atlas'

    bundles = [_bundle(tmp_path, include_config=True), _bundle(tmp_path, include_config=False)]
    monkeypatch.setattr(dev_sync_service, '_load_declaration_bundle', lambda: bundles.pop(0))

    try:
        first_report = dev_sync_service.execute_dev_sync(
            project_root=tmp_path,
            workflow_status=_status(),
            invoked_by_startup=False,
            schema_apply_runner_loader=lambda _engine_name: fake_runner,
            session_factory=session_factory,
        )
        second_report = dev_sync_service.execute_dev_sync(
            project_root=tmp_path,
            workflow_status=_status(),
            invoked_by_startup=False,
            schema_apply_runner_loader=lambda _engine_name: fake_runner,
            session_factory=session_factory,
        )
        current = _snapshot(session_factory)
    finally:
        asyncio.run(engine.dispose())

    assert runner_calls['invoked_by_startup'] is False
    assert first_report.dev_sync_result == 'success'
    assert first_report.compiled_checksum == 'compiled-sha-1'
    assert first_report.schema_sync.result == 'atlas_apply_success:atlas'
    assert first_report.managed_data.status == 'success'
    assert first_report.postcondition_verify.status == 'success'
    assert first_report.postcondition_verify.result == 'clean'
    assert first_report.residual_objects == ()
    assert first_report.managed_data_applied_operations == 6
    assert first_report.metadata_updated_objects == 6

    assert second_report.dev_sync_result == 'success'
    assert second_report.compiled_checksum == 'compiled-sha-0'
    assert second_report.postcondition_verify.status == 'success'
    assert second_report.managed_data_applied_operations == 1
    assert second_report.metadata_deactivated_objects == 1

    assert current['menus'] == {10: '系统管理', 20: '参数配置'}
    assert current['role_menus'] == {(2, 20)}
    assert current['dict_types'] == {1: 'sys_device_status'}
    assert current['dict_data'] == {1: ('sys_device_status', 'enabled')}
    assert current['configs'] == {}
    assert current['workflow_objects'][('sys_config', 'device.default.timeout')]['active_flag'] == 'N'
    assert current['workflow_objects'][('sys_config', 'device.default.timeout')]['module_key'] == 'platform'
    assert current['workflow_objects'][('sys_config', 'device.default.timeout')]['object_domain'] == 'configs'
    assert current['workflow_objects'][('sys_config', 'device.default.timeout')]['source_checksum']
    assert current['workflow_objects'][('sys_menu', '10')]['active_flag'] == 'Y'


def test_execute_dev_sync_noop_path_stays_clean_and_fast(monkeypatch, tmp_path: Path) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)

    same_bundle = _bundle(tmp_path, include_config=True)
    monkeypatch.setattr(dev_sync_service, '_load_declaration_bundle', lambda: same_bundle)

    try:
        first_report = dev_sync_service.execute_dev_sync(
            project_root=tmp_path,
            workflow_status=_status(),
            invoked_by_startup=False,
            schema_apply_runner_loader=lambda _engine_name: (lambda **_kwargs: 'atlas_apply_success:atlas'),
            session_factory=session_factory,
        )
        second_report = dev_sync_service.execute_dev_sync(
            project_root=tmp_path,
            workflow_status=_status(),
            invoked_by_startup=False,
            schema_apply_runner_loader=lambda _engine_name: (lambda **_kwargs: 'atlas_apply_success:atlas'),
            session_factory=session_factory,
        )
    finally:
        asyncio.run(engine.dispose())

    assert first_report.managed_data_applied_operations == 6
    assert second_report.dev_sync_result == 'success'
    assert second_report.managed_data_applied_operations == 0
    assert second_report.metadata_updated_objects == 0
    assert second_report.metadata_deactivated_objects == 0
    assert second_report.affected_objects == ()
    assert second_report.residual_objects == ()
    assert second_report.postcondition_verify.result == 'clean'
    assert second_report.duration_ms <= first_report.duration_ms + 100


def test_execute_dev_sync_returns_failed_report_when_declaration_is_invalid(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        dev_sync_service,
        '_load_declaration_bundle',
        lambda: (_ for _ in ()).throw(ValueError('invalid declaration bundle')),
    )

    report = dev_sync_service.execute_dev_sync(
        project_root=tmp_path,
        workflow_status=_status(),
        invoked_by_startup=False,
        schema_apply_runner_loader=lambda _engine_name: (_ for _ in ()).throw(AssertionError('should not be called')),
        session_factory=None,
    )

    assert report.dev_sync_result == 'failed'
    assert report.failed_step == 'declaration-validation'
    assert report.declaration_validation.status == 'failed'
    assert report.declaration_validation.error == 'invalid declaration bundle'


def test_execute_dev_sync_fails_when_postcondition_verify_detects_residual_objects(
    monkeypatch,
    tmp_path: Path,
) -> None:
    engine, session_factory = _build_session_factory()
    _seed_roles(session_factory)

    async def fake_verify(self, *, declaration_bundle, role_key_to_id):
        return dev_sync_service.PostconditionVerificationResult(
            duration_ms=1,
            pending_operation_objects=('sys_config:device.default.timeout',),
            metadata_drift_objects=('sys_config:device.default.timeout',),
            residual_objects=('sys_config:device.default.timeout',),
        )

    monkeypatch.setattr(dev_sync_service, '_load_declaration_bundle', lambda: _bundle(tmp_path, include_config=True))
    monkeypatch.setattr(dev_sync_service.PostconditionVerifier, 'verify', fake_verify)

    try:
        report = dev_sync_service.execute_dev_sync(
            project_root=tmp_path,
            workflow_status=_status(),
            invoked_by_startup=False,
            schema_apply_runner_loader=lambda _engine_name: (lambda **_kwargs: 'atlas_apply_success:atlas'),
            session_factory=session_factory,
        )
        current = _snapshot(session_factory)
    finally:
        asyncio.run(engine.dispose())

    assert report.dev_sync_result == 'failed'
    assert report.failed_step == 'postcondition-verify'
    assert report.managed_data.status == 'success'
    assert report.postcondition_verify.status == 'failed'
    assert report.postcondition_verify.result == 'drift-detected'
    assert report.residual_objects == ('sys_config:device.default.timeout',)
    assert current['menus'] == {}
    assert current['role_menus'] == set()
    assert current['dict_types'] == {}
    assert current['dict_data'] == {}
    assert current['configs'] == {}
    assert current['workflow_objects'] == {}
    assert report.schema_sync.status == 'success'


def test_execute_dev_sync_returns_failed_report_when_schema_sync_fails(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dev_sync_service, '_load_declaration_bundle', lambda: _bundle(tmp_path))

    def failing_runner(**kwargs) -> str:
        raise RuntimeError('atlas failed')

    report = dev_sync_service.execute_dev_sync(
        project_root=tmp_path,
        workflow_status=_status(),
        invoked_by_startup=True,
        schema_apply_runner_loader=lambda _engine_name: failing_runner,
        session_factory=None,
    )

    assert report.dev_sync_result == 'failed'
    assert report.trigger == 'startup'
    assert report.failed_step == 'schema-sync'
    assert report.schema_sync.status == 'failed'
    assert report.schema_sync.error == 'atlas failed'
    assert report.managed_data.status == 'skipped'
