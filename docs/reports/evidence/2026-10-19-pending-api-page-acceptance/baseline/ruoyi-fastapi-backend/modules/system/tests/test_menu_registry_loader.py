from __future__ import annotations

from pathlib import Path
import yaml

from modules.system.runtime.menu_registry_loader import MenuRegistryLoader


def _write_registry(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _menu(menu_id: int, parent_id: int = 0, component: str | None = None) -> dict:
    return {
        'menu_id': menu_id,
        'menu_name': f'Menu-{menu_id}',
        'parent_id': parent_id,
        'order_num': menu_id,
        'path': f'menu-{menu_id}',
        'component': component or f'system/menu/{menu_id}',
        'query': None,
        'route_name': '',
        'is_frame': 1,
        'is_cache': 0,
        'menu_type': 'C',
        'visible': '0',
        'status': '0',
        'perms': '',
        'icon': 'menu',
        'remark': '',
        'managed_by_seed': True,
    }


def test_loader_build_target_state_success(tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu(1), _menu(2, parent_id=1)],
            'role_grants': [{'role_key': 'common', 'menu_ids': [1, 2]}],
        },
    )

    loader = MenuRegistryLoader(registry_file)
    payload = loader.load_registry()
    target_state = loader.build_target_state(payload, {'common': 2})

    assert set(target_state.target_menus.keys()) == {1, 2}
    assert target_state.target_role_menu_pairs == {(2, 1), (2, 2)}


def test_loader_reports_duplicate_menu_id(tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu(1), _menu(1)],
            'role_grants': [],
        },
    )

    loader = MenuRegistryLoader(registry_file)
    payload = loader.load_registry()
    issues = loader.validate_registry(payload)

    assert any('duplicate menu_id' in issue.message for issue in issues)


def test_loader_reports_parent_cycle(tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu(1, parent_id=2), _menu(2, parent_id=1)],
            'role_grants': [],
        },
    )

    loader = MenuRegistryLoader(registry_file)
    payload = loader.load_registry()
    issues = loader.validate_registry(payload)

    assert any('parent cycle detected' in issue.message for issue in issues)


def test_loader_reports_invalid_component_path(tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    menu = _menu(1)
    menu['component'] = 'system/menu/index.vue'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [menu],
            'role_grants': [],
        },
    )

    loader = MenuRegistryLoader(registry_file)
    payload = loader.load_registry()
    issues = loader.validate_registry(payload)

    assert any('invalid characters' in issue.message for issue in issues)


def test_loader_reports_missing_role_key_mapping(tmp_path: Path) -> None:
    registry_file = tmp_path / 'menus.registry.yaml'
    _write_registry(
        registry_file,
        {
            'version': '1',
            'menus': [_menu(1)],
            'role_grants': [{'role_key': 'missing', 'menu_ids': [1]}],
        },
    )

    loader = MenuRegistryLoader(registry_file)
    payload = loader.load_registry()
    issues = loader.validate_role_keys(payload, {'common'})

    assert len(issues) == 1
    assert 'missing' in issues[0].message
