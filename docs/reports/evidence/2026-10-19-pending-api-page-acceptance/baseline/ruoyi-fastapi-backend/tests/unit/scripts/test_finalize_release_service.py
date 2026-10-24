from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import yaml
from sqlalchemy.ext.asyncio import create_async_engine

from config.database import Base
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleMenuDO
from scripts.internal.db_workflow.finalize_release_service import finalize_release_artifacts
from scripts.internal.db_workflow.release_bundle_service import BUNDLE_ID_PATTERN

if TYPE_CHECKING:
    from pathlib import Path

_REGISTERED_MODELS = (ConfigDO, DictDataDO, DictTypeDO, MenuDO, RoleMenuDO)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _write_seed_data_tree(seed_data_dir: Path) -> None:
    modules_root = seed_data_dir.parents[1] / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [
                {
                    'menu_id': 1,
                    'menu_key': 'system.root',
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
                    'menu_key': 'system.config',
                    'menu_name': '参数配置',
                    'parent_id': 1,
                    'parent_menu_key': 'system.root',
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
            'role_grants': [{'role_key': 'common', 'menu_keys': ['system.config']}],
            'dict_types': [
                {
                    'dict_id': 1,
                    'dict_name': '设备状态',
                    'dict_type': 'sys_device_status',
                    'status': '0',
                    'remark': '',
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
                    'remark': '',
                }
            ],
            'configs': [
                {
                    'config_id': 1,
                    'config_name': '设备默认超时',
                    'config_key': 'device.default.timeout',
                    'config_value': '30',
                    'config_type': 'Y',
                    'remark': '',
                }
            ],
        },
    )
    _write_yaml(
        modules_root / 'hidden.module.yaml',
        {
            'version': '1',
            'module_key': 'hidden',
            'dependencies': ['system'],
            'menus': [
                {
                    'menu_id': 110,
                    'menu_key': 'hidden.menu',
                    'menu_name': '隐藏菜单',
                    'parent_id': 1,
                    'parent_menu_key': 'system.root',
                    'order_num': 2,
                    'path': 'hidden',
                    'component': 'system/hidden/index',
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'C',
                    'visible': '0',
                    'status': '0',
                    'perms': 'system:hidden:list',
                    'icon': 'eye-close',
                    'remark': '',
                }
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['hidden.menu']}],
            'dict_types': [
                {
                    'dict_id': 2,
                    'dict_name': '隐藏状态',
                    'dict_type': 'sys_hidden_status',
                    'status': '0',
                    'remark': '',
                }
            ],
            'dict_data': [
                {
                    'dict_code': 2,
                    'dict_sort': 1,
                    'dict_label': '隐藏',
                    'dict_value': 'hidden',
                    'dict_type': 'sys_hidden_status',
                    'css_class': '',
                    'list_class': 'warning',
                    'is_default': 'N',
                    'status': '0',
                    'remark': '',
                }
            ],
            'configs': [
                {
                    'config_id': 2,
                    'config_name': '隐藏开关',
                    'config_key': 'device.hidden.flag',
                    'config_value': 'false',
                    'config_type': 'Y',
                    'remark': '',
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
            'modules': {'system': True, 'hidden': False},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')


async def _create_schema(database_url: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


def test_finalize_release_artifacts_writes_release_scoped_bundle_and_then_noops(tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    _write_seed_data_tree(seed_data_dir)

    database_path = tmp_path / 'finalize.sqlite3'
    asyncio.run(_create_schema(f'sqlite+aiosqlite:///{database_path}'))

    first = finalize_release_artifacts(
        project_root=project_root,
        finalize_database_url=f'sqlite:///{database_path}',
        schema_revision='20260402_head',
        message='Device config release',
    )

    assert first.bundle_id is not None
    assert BUNDLE_ID_PATTERN.match(first.bundle_id)
    assert first.data_finalize == 'generated'
    assert first.visibility_finalize == 'generated'
    assert first.managed_data_operation_count == 6
    assert first.bundle_file is not None and first.bundle_file.exists()
    assert first.managed_data_file is not None and first.managed_data_file.exists()
    assert first.release_manifest_file is not None and first.release_manifest_file.exists()

    managed_data_payload = yaml.safe_load(first.managed_data_file.read_text(encoding='utf-8'))
    manifest_payload = yaml.safe_load(first.release_manifest_file.read_text(encoding='utf-8'))

    operation_keys = {operation['object_key'] for operation in managed_data_payload['operations']}
    assert operation_keys == {
        'sys_menu:1',
        'sys_menu:100',
        'sys_role_menu:2:100',
        'sys_dict_type:1',
        'sys_dict_data:1',
        'sys_config:1',
    }
    assert managed_data_payload['capability']['compiled_checksum']
    assert managed_data_payload['capability']['release_plan_checksum']
    assert managed_data_payload['capability']['enabled_modules'] == ['system']
    assert managed_data_payload['target_state']['menus']['1']['menu_name'] == '系统管理'
    assert {row['object_key'] for row in managed_data_payload['managed_objects']} == {
        '1',
        '100',
        'common:100',
        'sys_device_status',
        'sys_device_status:enabled',
        'device.default.timeout',
    }
    assert manifest_payload['selection_mode'] == 'release-plan'
    assert manifest_payload['capability']['enabled_modules'] == ['system']
    assert manifest_payload['include']['menu_ids'] == [1, 100]
    assert manifest_payload['include']['role_grants'] == [{'role_key': 'common', 'menu_ids': [100]}]
    assert manifest_payload['include']['dict_types'] == ['sys_device_status']
    assert manifest_payload['include']['config_keys'] == ['device.default.timeout']

    second = finalize_release_artifacts(
        project_root=project_root,
        finalize_database_url=f'sqlite:///{database_path}',
        schema_revision='20260402_head',
        message='Device config release',
    )

    assert second.bundle_id is None
    assert second.data_finalize == 'no-op'
    assert second.visibility_finalize == 'no-op'
    assert second.managed_data_operation_count == 0
    release_dirs = sorted(path.name for path in (project_root / 'db_artifacts' / 'releases').iterdir() if path.is_dir())
    assert len(release_dirs) == 1
