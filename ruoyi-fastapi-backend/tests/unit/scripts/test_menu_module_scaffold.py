from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml

from scripts import menu as menu_cli

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


def _menu_row(
    *,
    menu_id: int,
    menu_key: str,
    menu_name: str,
    path: str,
    menu_type: str = 'C',
    parent_id: int = 0,
    parent_menu_key: str | None = None,
    component: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        'menu_id': menu_id,
        'menu_key': menu_key,
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
        'perms': '' if menu_type == 'M' else f'{menu_key}:list',
        'icon': 'menu',
        'remark': '',
    }
    if parent_menu_key is not None:
        row['parent_menu_key'] = parent_menu_key
    return row


def test_menu_add_creates_module_manifest_and_assigns_ids(tmp_path: Path, capsys) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    _write_roles(roles_file)

    exit_code = menu_cli.main(
        [
            '--modules-root',
            str(modules_root),
            '--roles-file',
            str(roles_file),
            'add',
            '--module',
            'reports',
            '--menu-name',
            '报表中心',
            '--path',
            'reports',
            '--component',
            'reports/index',
            '--grant-role',
            'common',
        ]
    )

    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    manifest_payload = _load_yaml(modules_root / 'reports.module.yaml')

    assert exit_code == 0
    assert summary['moduleKey'] == 'reports'
    assert summary['menuId'] == 1
    assert summary['menuKey'] == 'reports.reports'
    assert manifest_payload['menus'][0]['menu_id'] == 1
    assert manifest_payload['menus'][0]['menu_key'] == 'reports.reports'
    assert manifest_payload['role_grants'] == [{'role_key': 'common', 'menu_keys': ['reports.reports']}]


def test_menu_add_cross_module_parent_auto_adds_dependency(tmp_path: Path) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    _write_roles(roles_file)
    _write_yaml(
        modules_root / 'platform.module.yaml',
        {
            'version': '1',
            'module_key': 'platform',
            'menus': [_menu_row(menu_id=1, menu_key='platform.root', menu_name='平台', path='platform', menu_type='M')],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )

    exit_code = menu_cli.main(
        [
            '--modules-root',
            str(modules_root),
            '--roles-file',
            str(roles_file),
            'add',
            '--module',
            'reports',
            '--parent-key',
            'platform.root',
            '--menu-name',
            '运营看板',
            '--path',
            'dashboard',
            '--component',
            'reports/dashboard/index',
        ]
    )

    manifest_payload = _load_yaml(modules_root / 'reports.module.yaml')

    assert exit_code == 0
    assert manifest_payload['dependencies'] == ['platform']
    assert manifest_payload['menus'][0]['parent_id'] == 1
    assert manifest_payload['menus'][0]['parent_menu_key'] == 'platform.root'


def test_menu_remove_cascade_prunes_role_grants(tmp_path: Path) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    _write_roles(roles_file)
    _write_yaml(
        modules_root / 'reports.module.yaml',
        {
            'version': '1',
            'module_key': 'reports',
            'menus': [
                _menu_row(menu_id=1, menu_key='reports.root', menu_name='报表', path='reports', menu_type='M'),
                _menu_row(
                    menu_id=2,
                    menu_key='reports.child',
                    menu_name='明细报表',
                    path='detail',
                    parent_id=1,
                    parent_menu_key='reports.root',
                    component='reports/detail/index',
                ),
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['reports.root', 'reports.child']}],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )

    exit_code = menu_cli.main(
        [
            '--modules-root',
            str(modules_root),
            '--roles-file',
            str(roles_file),
            'remove',
            '--module',
            'reports',
            '--menu-key',
            'reports.root',
            '--cascade',
        ]
    )

    manifest_payload = _load_yaml(modules_root / 'reports.module.yaml')

    assert exit_code == 0
    assert manifest_payload['menus'] == []
    assert manifest_payload['role_grants'] == []


def test_menu_check_blocks_non_empty_legacy_sources(tmp_path: Path, capsys) -> None:
    backend_root = tmp_path
    modules_root = backend_root / 'capabilities' / 'modules'
    roles_file = backend_root / 'scripts' / 'seed_data' / 'base' / 'roles.yaml'
    legacy_menu_registry = backend_root / 'scripts' / 'seed_data' / 'menus.registry.yaml'
    _write_roles(roles_file)
    _write_yaml(
        modules_root / 'reports.module.yaml',
        {
            'version': '1',
            'module_key': 'reports',
            'menus': [_menu_row(menu_id=1, menu_key='reports.root', menu_name='报表', path='reports', menu_type='M')],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )
    _write_yaml(
        legacy_menu_registry,
        {
            'version': '1',
            'menus': [_menu_row(menu_id=99, menu_key='legacy.root', menu_name='旧菜单', path='legacy', menu_type='M')],
            'role_grants': [],
        },
    )

    exit_code = menu_cli.main(
        [
            '--modules-root',
            str(modules_root),
            '--roles-file',
            str(roles_file),
            'check',
            '--legacy-menu-registry',
            str(legacy_menu_registry),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert 'legacy declaration file is no longer supported' in captured.out
