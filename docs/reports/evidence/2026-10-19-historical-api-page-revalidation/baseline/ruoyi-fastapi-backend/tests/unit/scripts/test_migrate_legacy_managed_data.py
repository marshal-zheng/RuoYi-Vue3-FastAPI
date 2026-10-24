from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from scripts.internal.menu_registry import migrate_legacy_declarations

if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def _write_roles(path: Path) -> None:
    _write_yaml(
        path,
        {
            'roles': [
                {'role_id': 1, 'role_key': 'admin'},
                {'role_id': 2, 'role_key': 'common'},
            ]
        },
    )


def _legacy_menu(
    *,
    menu_id: int,
    menu_name: str,
    path: str,
    menu_type: str = 'C',
    parent_id: int = 0,
    component: str | None = None,
) -> dict[str, object]:
    return {
        'menu_id': menu_id,
        'menu_name': menu_name,
        'parent_id': parent_id,
        'order_num': menu_id,
        'path': path,
        'component': component if menu_type == 'C' else None,
        'query': None,
        'route_name': '',
        'is_frame': 1,
        'is_cache': 0,
        'menu_type': menu_type,
        'visible': '0',
        'status': '0',
        'perms': '' if menu_type == 'M' else f'{path}:list',
        'icon': 'menu',
        'remark': '',
        'managed_by_seed': True,
    }


def test_migrate_legacy_declarations_exports_managed_data(tmp_path: Path) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    menu_registry = backend_root / 'scripts' / 'seed_data' / 'menus.registry.yaml'
    dict_types = backend_root / 'scripts' / 'seed_data' / 'base' / 'dict_types.yaml'
    dict_data = backend_root / 'scripts' / 'seed_data' / 'base' / 'dict_data.yaml'
    configs = backend_root / 'scripts' / 'seed_data' / 'base' / 'configs.yaml'
    _write_roles(roles_file)
    _write_yaml(
        menu_registry,
        {
            'version': '1',
            'menus': [
                _legacy_menu(menu_id=1, menu_name='平台', path='platform', menu_type='M'),
                _legacy_menu(menu_id=2, menu_name='用户管理', path='user', parent_id=1, component='system/user/index'),
            ],
            'role_grants': [{'role_key': 'common', 'menu_ids': [1, 2]}],
        },
    )
    _write_yaml(
        dict_types,
        {
            'dict_types': [
                {
                    'dict_id': 1,
                    'dict_name': '平台状态',
                    'dict_type': 'platform_status',
                    'status': '0',
                    'remark': '',
                }
            ]
        },
    )
    _write_yaml(
        dict_data,
        {
            'dict_data': [
                {
                    'dict_code': 1,
                    'dict_sort': 1,
                    'dict_label': '启用',
                    'dict_value': 'enabled',
                    'dict_type': 'platform_status',
                    'css_class': '',
                    'list_class': 'success',
                    'is_default': 'Y',
                    'status': '0',
                    'remark': '',
                }
            ]
        },
    )
    _write_yaml(
        configs,
        {
            'configs': [
                {
                    'config_id': 1,
                    'config_name': '平台能力开关',
                    'config_key': 'capability.platform.enabled',
                    'config_value': 'true',
                    'config_type': 'Y',
                    'remark': '',
                }
            ]
        },
    )

    summary = migrate_legacy_declarations(
        module_key='platform',
        modules_root=modules_root,
        roles_file=roles_file,
        menu_registry=menu_registry,
        dict_types=dict_types,
        dict_data=dict_data,
        configs=configs,
        gate_config_key='capability.platform.enabled',
        gate_default_enabled=True,
    )

    manifest_payload = _load_yaml(modules_root / 'platform.module.yaml')

    assert summary['menuCount'] == 2
    assert manifest_payload['menus'][0]['menu_key'] == 'platform.menu.1'
    assert manifest_payload['menus'][1]['menu_key'] == 'platform.menu.2'
    assert manifest_payload['menus'][1]['parent_menu_key'] == 'platform.menu.1'
    assert manifest_payload['role_grants'] == [{'role_key': 'common', 'menu_keys': ['platform.menu.1', 'platform.menu.2']}]
    assert manifest_payload['runtime_gate'] == {
        'config_key': 'capability.platform.enabled',
        'default_enabled': True,
    }


def test_migrate_legacy_declarations_fails_on_double_write(tmp_path: Path) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    menu_registry = backend_root / 'scripts' / 'seed_data' / 'menus.registry.yaml'
    _write_roles(roles_file)
    _write_yaml(
        modules_root / 'platform.module.yaml',
        {
            'version': '1',
            'module_key': 'platform',
            'menus': [],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )
    _write_yaml(
        menu_registry,
        {
            'version': '1',
            'menus': [_legacy_menu(menu_id=1, menu_name='平台', path='platform', menu_type='M')],
            'role_grants': [],
        },
    )

    with pytest.raises(ValueError, match='module manifest already exists: platform'):
        migrate_legacy_declarations(
            module_key='platform',
            modules_root=modules_root,
            roles_file=roles_file,
            menu_registry=menu_registry,
        )


def test_migrate_legacy_declarations_fails_on_existing_module_conflict(tmp_path: Path) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    menu_registry = backend_root / 'scripts' / 'seed_data' / 'menus.registry.yaml'
    _write_roles(roles_file)
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [
                {
                    'config_id': 1,
                    'config_name': '冲突配置',
                    'config_key': 'capability.platform.enabled',
                    'config_value': 'true',
                    'config_type': 'Y',
                    'remark': '',
                }
            ],
        },
    )
    _write_yaml(
        menu_registry,
        {
            'version': '1',
            'menus': [_legacy_menu(menu_id=1, menu_name='平台', path='platform', menu_type='M')],
            'role_grants': [],
        },
    )
    _write_yaml(
        backend_root / 'scripts' / 'seed_data' / 'base' / 'configs.yaml',
        {
            'configs': [
                {
                    'config_id': 2,
                    'config_name': '平台能力开关',
                    'config_key': 'capability.platform.enabled',
                    'config_value': 'true',
                    'config_type': 'Y',
                    'remark': '',
                }
            ]
        },
    )

    with pytest.raises(ValueError, match='config_key already owned by module platform'):
        migrate_legacy_declarations(
            module_key='platform',
            modules_root=modules_root,
            roles_file=roles_file,
            menu_registry=menu_registry,
            configs=backend_root / 'scripts' / 'seed_data' / 'base' / 'configs.yaml',
            gate_config_key='capability.platform.enabled',
        )
