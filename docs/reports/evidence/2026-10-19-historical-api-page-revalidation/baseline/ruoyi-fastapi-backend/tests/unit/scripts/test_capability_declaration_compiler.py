from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from scripts.internal.db_workflow.capability_declaration_compiler import CapabilityDeclarationCompiler

if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _menu_row(
    *,
    menu_id: int,
    menu_name: str,
    menu_key: str,
    parent_id: int = 0,
    path: str | None = None,
    component: str | None = None,
    menu_type: str = 'C',
    parent_menu_key: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        'menu_id': menu_id,
        'menu_key': menu_key,
        'menu_name': menu_name,
        'parent_id': parent_id,
        'order_num': menu_id,
        'path': path or f'menu-{menu_id}',
        'component': component if menu_type == 'C' else None,
        'query': None,
        'route_name': '',
        'is_frame': 1,
        'is_cache': 0,
        'menu_type': menu_type,
        'visible': '0',
        'status': '0',
        'perms': '' if menu_type == 'M' else f'test:menu:{menu_id}',
        'icon': 'menu',
        'remark': '',
    }
    if parent_menu_key is not None:
        row['parent_menu_key'] = parent_menu_key
    return row


def test_compiler_compiles_module_manifests_and_emits_checksums(tmp_path: Path) -> None:
    modules_root = tmp_path / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [
                _menu_row(
                    menu_id=2,
                    menu_name='系统监控',
                    menu_key='system.monitor',
                    menu_type='M',
                    path='monitor',
                )
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['system.monitor']}],
            'dict_types': [
                {
                    'dict_id': 1,
                    'dict_name': '系统状态',
                    'dict_type': 'system_status',
                    'status': '0',
                    'remark': '',
                }
            ],
            'dict_data': [
                {
                    'dict_code': 1,
                    'dict_sort': 1,
                    'dict_label': '正常',
                    'dict_value': 'ok',
                    'dict_type': 'system_status',
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
                    'config_name': '系统开关',
                    'config_key': 'capability.system.enabled',
                    'config_value': 'true',
                    'config_type': 'Y',
                    'remark': '',
                }
            ],
            'runtime_gate': {'config_key': 'capability.system.enabled', 'default_enabled': True},
        },
    )
    _write_yaml(
        modules_root / 'monitor.module.yaml',
        {
            'version': '1',
            'module_key': 'monitor',
            'dependencies': ['system'],
            'menus': [
                _menu_row(
                    menu_id=200,
                    menu_name='监控看板',
                    menu_key='monitor.dashboard',
                    parent_id=2,
                    parent_menu_key='system.monitor',
                    path='dashboard',
                    component='monitor/dashboard/index',
                )
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['monitor.dashboard']}],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )

    compiled_state = CapabilityDeclarationCompiler(
        modules_root=modules_root,
        known_role_keys=frozenset({'common'}),
    ).compile()

    assert set(compiled_state.modules) == {'monitor', 'system'}
    assert compiled_state.modules['monitor'].dependencies == ('system',)
    assert compiled_state.resources.menus[200]['parent_id'] == 2
    assert compiled_state.resources.role_grants['common'] == (2, 200)
    assert compiled_state.runtime_gates['system'].config_key == 'capability.system.enabled'
    assert compiled_state.checksums is not None
    assert compiled_state.checksums.source_checksum
    assert compiled_state.checksums.compiled_checksum


def test_compiler_materializes_runtime_gate_config_when_not_declared(tmp_path: Path) -> None:
    modules_root = tmp_path / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
            'runtime_gate': {'config_key': 'capability.system.enabled', 'default_enabled': True},
        },
    )

    compiled_state = CapabilityDeclarationCompiler(modules_root=modules_root).compile()

    gate_config = compiled_state.resources.configs['capability.system.enabled']
    assert gate_config['config_name'] == 'Capability Gate: system'
    assert gate_config['config_key'] == 'capability.system.enabled'
    assert gate_config['config_value'] == 'true'
    assert gate_config['config_type'] == 'Y'
    assert int(gate_config['config_id']) < 0
    assert compiled_state.modules['system'].resources.configs['capability.system.enabled'] == gate_config


def test_compiler_rejects_duplicate_menu_ownership_across_manifests(tmp_path: Path) -> None:
    modules_root = tmp_path / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [_menu_row(menu_id=2, menu_name='系统监控', menu_key='system.monitor', menu_type='M', path='monitor')],
            'role_grants': [],
        },
    )
    _write_yaml(
        modules_root / 'monitor.module.yaml',
        {
            'version': '1',
            'module_key': 'monitor',
            'menus': [_menu_row(menu_id=2, menu_name='冲突菜单', menu_key='system.monitor', path='conflict', component='monitor/conflict/index')],
            'role_grants': [],
        },
    )

    issues = CapabilityDeclarationCompiler(modules_root=modules_root).validate()

    assert any('menu_key already owned by module ' in issue.message for issue in issues)
    assert any('menu_id already owned by module ' in issue.message for issue in issues)


def test_compiler_requires_declared_dependency_for_cross_module_parent(tmp_path: Path) -> None:
    modules_root = tmp_path / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'system.module.yaml',
        {
            'version': '1',
            'module_key': 'system',
            'menus': [_menu_row(menu_id=1, menu_name='系统管理', menu_key='system.root', menu_type='M', path='system')],
            'role_grants': [],
        },
    )
    _write_yaml(
        modules_root / 'monitor.module.yaml',
        {
            'version': '1',
            'module_key': 'monitor',
            'menus': [
                _menu_row(
                    menu_id=200,
                    menu_name='监控看板',
                    menu_key='monitor.dashboard',
                    parent_id=1,
                    parent_menu_key='system.root',
                    path='dashboard',
                    component='monitor/dashboard/index',
                )
            ],
            'role_grants': [],
        },
    )

    issues = CapabilityDeclarationCompiler(modules_root=modules_root).validate()

    assert any('module dependency missing for parent menu owner: system' in issue.message for issue in issues)


def test_compiler_requires_module_manifests(tmp_path: Path) -> None:
    issues = CapabilityDeclarationCompiler(modules_root=tmp_path / 'capabilities' / 'modules').validate()

    assert any(issue.domain == 'modules' and issue.message == 'no module manifests found' for issue in issues)
