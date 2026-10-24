from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataDeclarationLoader

if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _write_module_tree(seed_data_dir: Path) -> None:
    modules_root = seed_data_dir.parents[1] / 'capabilities' / 'modules'
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
            'release_key': '2026-04-platform',
            'modules': {'platform': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')


def test_loader_builds_bundle_from_module_manifests(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)

    loader = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir)
    bundle = loader.load()

    assert bundle.bootstrap_role_keys == ('common',)
    assert bundle.dev_target_state.menus[100]['component'] == 'system/config/index'
    assert bundle.dev_target_state.role_grants == {'common': (100,)}
    assert bundle.dev_target_state.dict_types['sys_device_status']['dict_id'] == 1
    assert bundle.dev_target_state.dict_data[('sys_device_status', 'enabled')]['dict_code'] == 1
    assert bundle.dev_target_state.configs['device.default.timeout']['config_id'] == 1
    assert bundle.formal_candidate_state == bundle.dev_target_state
    assert bundle.release_selection.release_key == '2026-04-platform'
    assert bundle.release_selection.modules == {'platform': True}
    assert bundle.release_selection.enabled_modules == ('platform',)
    assert bundle.release_selection.menu_ids == (1, 100)
    assert bundle.release_selection.role_grants == {'common': (100,)}
    assert bundle.release_selection.dict_types == ('sys_device_status',)
    assert bundle.release_selection.config_keys == ('device.default.timeout',)
    assert bundle.compiled_capability_state is not None
    assert bundle.compiled_capability_state.resources.menus == bundle.dev_target_state.menus
    assert bundle.compiled_capability_state.checksums is not None
    assert bundle.compiled_capability_state.checksums.source_checksum
    assert bundle.compiled_capability_state.checksums.compiled_checksum


def test_loader_rejects_legacy_seed_content(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)
    _write_yaml(
        seed_data_dir / 'menus.registry.yaml',
        {
            'version': '1',
            'menus': [
                {
                    'menu_id': 999,
                    'menu_name': '旧菜单',
                    'parent_id': 0,
                    'order_num': 1,
                    'path': 'legacy',
                    'component': None,
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'M',
                    'visible': '0',
                    'status': '0',
                    'perms': '',
                    'icon': 'legacy',
                    'remark': '',
                }
            ],
            'role_grants': [],
        },
    )

    issues = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).validate()

    assert any(
        issue.domain == 'menus'
        and 'legacy declaration file is no longer supported' in issue.message
        for issue in issues
    )


def test_loader_rejects_object_level_release_plan(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '1',
            'release_key': 'broken',
            'include': {'menu_ids': [100]},
        },
    )

    issues = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).validate()

    messages = {(issue.domain, issue.location, issue.message) for issue in issues}
    assert ('release_visibility', 'version', 'version must be "2"') in messages
    assert (
        'release_visibility',
        'include',
        'object-level include selectors are no longer supported; use modules: {<module>: true|false}',
    ) in messages
    assert ('release_visibility', 'modules', 'modules must be a mapping') in messages


def test_loader_rejects_top_level_object_selectors_and_unknown_keys(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': 'broken',
            'modules': {'platform': True},
            'menu_ids': [100],
            'dict_types': ['sys_device_status'],
            'profile': 'legacy-standard',
        },
    )

    issues = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).validate()

    messages = {(issue.location, issue.message) for issue in issues}
    assert (
        'menu_ids',
        'object-level selector "menu_ids" is no longer supported; use modules: {<module>: true|false}',
    ) in messages
    assert (
        'dict_types',
        'object-level selector "dict_types" is no longer supported; use modules: {<module>: true|false}',
    ) in messages
    assert (
        'profile',
        'unsupported release-plan key: profile; only version, release_key, modules, metadata are allowed',
    ) in messages


def test_loader_accepts_metadata_for_template_prefill_but_keeps_modules_as_only_control_plane(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': '2026-04-platform',
            'metadata': {
                'template_source': {
                    'type': 'profile',
                    'name': 'standard',
                }
            },
            'modules': {'platform': True},
        },
    )

    bundle = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).load()

    assert bundle.release_selection.modules == {'platform': True}
    assert bundle.release_selection.enabled_modules == ('platform',)


def test_loader_rejects_unknown_module_and_illegal_module_value(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    _write_module_tree(seed_data_dir)
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': 'broken',
            'modules': {
                'platform': 'yes',
                'unknown': True,
            },
        },
    )

    issues = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).validate()

    messages = {(issue.location, issue.message) for issue in issues}
    assert ('modules.platform', 'module value must be true or false') in messages
    assert ('modules.unknown', 'unknown module: unknown') in messages


def test_loader_rejects_explicitly_disabled_module_dependency(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    modules_root = seed_data_dir.parents[1] / 'capabilities' / 'modules'
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
        },
    )
    _write_yaml(
        modules_root / 'monitor.module.yaml',
        {
            'version': '1',
            'module_key': 'monitor',
            'dependencies': ['system'],
            'menus': [],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
        },
    )
    _write_yaml(seed_data_dir / 'base' / 'roles.yaml', {'roles': []})
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': 'broken',
            'modules': {'monitor': True, 'system': False},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')

    issues = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).validate()

    assert any(
        issue.location == 'modules.monitor' and issue.message == 'module dependency is explicitly disabled: system'
        for issue in issues
    )


def test_loader_expands_module_dependencies(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
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
                }
            ],
            'role_grants': [],
        },
    )
    _write_yaml(
        modules_root / 'monitor.module.yaml',
        {
            'version': '1',
            'module_key': 'monitor',
            'dependencies': ['system'],
            'menus': [
                {
                    'menu_id': 200,
                    'menu_key': 'monitor.dashboard',
                    'menu_name': '监控看板',
                    'parent_id': 1,
                    'parent_menu_key': 'system.root',
                    'order_num': 1,
                    'path': 'dashboard',
                    'component': 'monitor/dashboard/index',
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'C',
                    'visible': '0',
                    'status': '0',
                    'perms': 'monitor:dashboard:list',
                    'icon': 'monitor',
                    'remark': '',
                }
            ],
            'role_grants': [],
        },
    )
    _write_yaml(
        seed_data_dir / 'base' / 'roles.yaml',
        {'roles': []},
    )
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': 'monitor-only',
            'modules': {'monitor': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')

    bundle = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).load()

    assert bundle.release_selection.modules == {'monitor': True, 'system': False}
    assert bundle.release_selection.enabled_modules == ('monitor', 'system')
    assert bundle.formal_candidate_state.menus.keys() == {1, 200}


def test_loader_materializes_runtime_gate_config_into_release_target_state(tmp_path: Path) -> None:
    seed_data_dir = tmp_path / 'scripts' / 'seed_data'
    modules_root = seed_data_dir.parents[1] / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'demo.module.yaml',
        {
            'version': '1',
            'module_key': 'demo',
            'menus': [],
            'role_grants': [],
            'dict_types': [],
            'dict_data': [],
            'configs': [],
            'runtime_gate': {'config_key': 'capability.demo.enabled', 'default_enabled': True},
        },
    )
    _write_yaml(seed_data_dir / 'base' / 'roles.yaml', {'roles': []})
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': 'demo',
            'modules': {'demo': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')

    bundle = ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir).load()

    assert bundle.release_selection.config_keys == ('capability.demo.enabled',)
    assert bundle.release_selection.runtime_gates['demo'].config_key == 'capability.demo.enabled'
    gate_config = bundle.formal_candidate_state.configs['capability.demo.enabled']
    assert gate_config['config_value'] == 'true'
    assert int(gate_config['config_id']) < 0
