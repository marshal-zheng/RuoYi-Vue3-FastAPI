"""Menu service unit tests for the repository-based architecture."""

from types import SimpleNamespace

from modules.system.application.services.menu_service import MenuService


def test_list_to_tree_builds_parent_child_relationship():
    items = [
        SimpleNamespace(menu_id=1, menu_name="Root", parent_id=0),
        SimpleNamespace(menu_id=2, menu_name="Child", parent_id=1),
    ]

    tree = MenuService.list_to_tree(items)

    assert len(tree) == 1
    assert tree[0]["id"] == 1
    assert tree[0]["children"][0]["id"] == 2


def test_list_to_tree_treats_orphan_as_root_node():
    items = [SimpleNamespace(menu_id=99, menu_name="Orphan", parent_id=1000)]

    tree = MenuService.list_to_tree(items)

    assert len(tree) == 1
    assert tree[0]["id"] == 99


def test_menu_service_contract_methods_exist():
    assert callable(MenuService.get_menu_tree_services)
    assert callable(MenuService.add_menu_services)
    assert callable(MenuService.edit_menu_services)
    assert callable(MenuService.delete_menu_services)
