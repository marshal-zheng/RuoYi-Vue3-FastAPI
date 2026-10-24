from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml
from sqlalchemy import create_engine, inspect

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.db_workflow_do import DbWorkflowArtifactDO, DbWorkflowObjectDO
from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataTargetState, ReleasePlanSelection
from scripts.internal.db_workflow.managed_data_planner import ManagedDataOperation, ManagedDataPlan
from scripts.internal.db_workflow.release_bundle_service import (
    ReleaseBundleService,
    build_managed_data_payload,
    build_release_manifest_payload,
)
from scripts.manual.generate_baseline_bundle import generate_baseline_bundle

if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _write_seed_data_tree(seed_data_dir: Path) -> None:
    modules_root = seed_data_dir.parent / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'platform.module.yaml',
        {
            'version': '1',
            'module_key': 'platform',
            'menus': [
                {
                    'menu_id': 1,
                    'menu_key': 'platform.system',
                    'menu_name': '系统管理',
                    'parent_id': 0,
                    'order_num': 1,
                    'path': 'system',
                    'component': None,
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'M',
                    'visible': '0',
                    'status': '0',
                    'perms': '',
                    'icon': 'system',
                    'remark': '',
                },
                {
                    'menu_id': 100,
                    'menu_key': 'platform.system.config',
                    'menu_name': '参数配置',
                    'parent_id': 1,
                    'parent_menu_key': 'platform.system',
                    'order_num': 1,
                    'path': 'config',
                    'component': 'system/config/index',
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'C',
                    'visible': '0',
                    'status': '0',
                    'perms': 'system:config:list',
                    'icon': 'setting',
                    'remark': '',
                },
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['platform.system.config']}],
            'dict_types': [
                {
                    'dict_id': 1,
                    'dict_name': '设备状态',
                    'dict_type': 'sys_device_status',
                    'status': '0',
                    'remark': '设备状态列表',
                }
            ],
            'dict_data': [
                {
                    'dict_code': 1,
                    'dict_sort': 1,
                    'dict_label': '启用',
                    'dict_value': 'enabled',
                    'dict_type': 'sys_device_status',
                    'css_class': '',
                    'list_class': 'success',
                    'is_default': 'Y',
                    'status': '0',
                    'remark': '启用状态',
                }
            ],
            'configs': [
                {
                    'config_id': 1,
                    'config_name': '设备默认超时',
                    'config_key': 'device.default.timeout',
                    'config_value': '30',
                    'config_type': 'Y',
                    'remark': '秒',
                }
            ],
        },
    )
    _write_yaml(
        seed_data_dir / 'base' / 'roles.yaml',
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
    )
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': '2026-04-device-config',
            'modules': {'platform': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')


def _target_state() -> ManagedDataTargetState:
    return ManagedDataTargetState(
        menus={
            100: {
                'menu_id': 100,
                'menu_name': '参数配置',
                'parent_id': 1,
                'order_num': 1,
                'path': 'config',
                'component': 'system/config/index',
                'query': None,
                'route_name': '',
                'is_frame': 1,
                'is_cache': 0,
                'menu_type': 'C',
                'visible': '0',
                'status': '0',
                'perms': 'system:config:list',
                'icon': 'setting',
                'remark': '',
            }
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


def test_release_bundle_service_writes_files_and_enforces_idempotency(tmp_path: Path) -> None:
    plan = ManagedDataPlan(
        operations=(
            ManagedDataOperation(
                op_type='upsert-row',
                entity_type='sys_menu',
                object_key='sys_menu:100',
                match_fields={'menu_id': 100},
                values={'menu_id': 100, 'menu_name': '参数配置'},
            ),
            ManagedDataOperation(
                op_type='ensure-link',
                entity_type='sys_role_menu',
                object_key='sys_role_menu:2:100',
                match_fields={'role_id': 2, 'menu_id': 100},
                values={'role_id': 2, 'menu_id': 100},
            ),
        )
    )
    service = ReleaseBundleService(output_root=tmp_path)

    bundle = service.write_bundle(
        bundle_id='20260402_001_device-baseline',
        bundle_kind='baseline',
        schema_revision='20260402_workflow_metadata',
        release_key='2026-04-device-config',
        managed_data_payload=build_managed_data_payload('20260402_001_device-baseline', plan),
        release_manifest_payload=build_release_manifest_payload(
            '20260402_001_device-baseline',
            target_state=_target_state(),
            release_selection=_release_selection(),
        ),
        message='baseline scaffold',
    )

    assert (bundle.bundle_dir / 'bundle.yaml').exists()
    assert (bundle.bundle_dir / 'managed-data.yaml').exists()
    assert (bundle.bundle_dir / 'release.manifest.yaml').exists()

    bundle_yaml = yaml.safe_load((bundle.bundle_dir / 'bundle.yaml').read_text(encoding='utf-8'))
    manifest_yaml = yaml.safe_load((bundle.bundle_dir / 'release.manifest.yaml').read_text(encoding='utf-8'))
    assert bundle_yaml['schema_revision'] == '20260402_workflow_metadata'
    assert bundle_yaml['idempotency_key'] == bundle.idempotency_key
    assert [artifact['artifact_type'] for artifact in bundle_yaml['artifacts']] == ['managed-data', 'release-manifest']
    assert manifest_yaml['capability']['compiled_checksum'] == 'compiled-sha'
    assert manifest_yaml['capability']['release_plan_checksum'] == 'release-plan-sha'

    replay = service.write_bundle(
        bundle_id='20260402_001_device-baseline',
        bundle_kind='baseline',
        schema_revision='20260402_workflow_metadata',
        release_key='2026-04-device-config',
        managed_data_payload=build_managed_data_payload('20260402_001_device-baseline', plan),
        release_manifest_payload=build_release_manifest_payload(
            '20260402_001_device-baseline',
            target_state=_target_state(),
            release_selection=_release_selection(),
        ),
        message='baseline scaffold',
    )

    assert replay.file_by_type('bundle').checksum == bundle.file_by_type('bundle').checksum

    with pytest.raises(ValueError, match='bundle file already exists with different content'):
        service.write_bundle(
            bundle_id='20260402_001_device-baseline',
            bundle_kind='baseline',
            schema_revision='20260402_workflow_metadata_v2',
            release_key='2026-04-device-config',
            managed_data_payload=build_managed_data_payload('20260402_001_device-baseline', plan),
            release_manifest_payload=build_release_manifest_payload(
                '20260402_001_device-baseline',
                target_state=_target_state(),
                release_selection=_release_selection(),
            ),
        )


def test_generate_baseline_bundle_scaffolds_full_declaration_bundle(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'seed_data'
    output_root = tmp_path / 'releases'
    _write_seed_data_tree(seed_data_dir)

    bundle = generate_baseline_bundle(
        bundle_id='20260402_001_device-baseline',
        schema_revision='20260402_workflow_metadata',
        seed_data_dir=seed_data_dir,
        output_root=output_root,
    )

    managed_payload = yaml.safe_load((bundle.bundle_dir / 'managed-data.yaml').read_text(encoding='utf-8'))
    manifest_payload = yaml.safe_load((bundle.bundle_dir / 'release.manifest.yaml').read_text(encoding='utf-8'))

    assert managed_payload['operation_count'] == 6
    assert managed_payload['capability']['enabled_modules'] == ['platform']
    assert managed_payload['target_state']['configs']['device.default.timeout']['config_value'] == '30'
    assert len(managed_payload['managed_objects']) == 6
    assert managed_payload['summary']['by_operation'] == {'upsert-row': 5, 'ensure-link': 1}
    assert {operation['entity_type'] for operation in managed_payload['operations']} == {
        'sys_menu',
        'sys_role_menu',
        'sys_dict_type',
        'sys_dict_data',
        'sys_config',
    }
    assert manifest_payload['selection_mode'] == 'full-declarations'
    assert manifest_payload['include']['menu_ids'] == [1, 100]
    assert manifest_payload['include']['dict_types'] == ['sys_device_status']
    assert manifest_payload['include']['config_keys'] == ['device.default.timeout']


def test_workflow_metadata_models_expose_unique_constraints() -> None:
    engine = create_engine('sqlite:///:memory:')
    try:
        LegacyBaseModel.metadata.create_all(bind=engine)

        inspector = inspect(engine)

        assert 'sys_db_workflow_artifact' in inspector.get_table_names()
        assert 'sys_db_workflow_object' in inspector.get_table_names()
        assert {constraint['name'] for constraint in inspector.get_unique_constraints('sys_db_workflow_artifact')} == {
            'uq_sys_db_workflow_artifact_bundle_type'
        }
        assert {constraint['name'] for constraint in inspector.get_unique_constraints('sys_db_workflow_object')} == {
            'uq_sys_db_workflow_object_type_key'
        }
        workflow_columns = {column['name'] for column in inspector.get_columns('sys_db_workflow_object')}
        assert {'module_key', 'object_domain', 'source_checksum'} <= workflow_columns

        assert DbWorkflowArtifactDO.__tablename__ == 'sys_db_workflow_artifact'
        assert DbWorkflowObjectDO.__tablename__ == 'sys_db_workflow_object'
    finally:
        engine.dispose()
